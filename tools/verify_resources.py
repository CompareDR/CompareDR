"""Verify distributed report identities, label bindings, criteria and documentation."""
import hashlib,json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def read(p):return json.loads((ROOT/p).read_text(encoding='utf-8'))
def need(ok,message):
    if not ok:raise ValueError(message)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def safe(rel):
    p=ROOT/rel
    need(not p.is_symlink() and p.resolve().is_relative_to(ROOT),'Unsafe resource path')
    need(p.is_file(),'Missing resource: '+rel)
    return p
def verify():
    counts={};lookups={};query_text={}
    b=read('reproduction/offline/data/benchmark.json')
    original={(r['query'],r['report_id']):r['sha256'] for r in b['report_manifest']}
    for cohort,n in [('main9',9),('studies7',7)]:
        rows=read(f'data/reports/{cohort}/manifest.json')['items']
        need(len(rows)==40*n,'Incorrect report count')
        lookup={(r['query_id'],r['report_id']):r for r in rows};need(len(lookup)==len(rows),'Duplicate report')
        qs=sorted({r['query_id'] for r in rows});need(len(qs)==40,'Query count')
        ids=['R1','R2','R3','R4','R5','R6','R7']+(['R9','R10'] if n==9 else [])
        for q in qs:
            need([r['report_id'] for r in rows if r['query_id']==q]==ids,'System order drift')
            rp=safe(f'data/evaluation/{cohort}/rubrics/{q}.json');rub=json.loads(rp.read_text())
            route=read(f'data/evaluation/{cohort}/routing/{q}.json')
            need(route['rubrics_sha256']==sha(rp),'Routing hash mismatch')
            for field,key in [('pointwise','items'),('pairwise','pairwise')]:
                need({r['id'] for r in rub[field]}=={r['id'] for r in route[key]},'Routing coverage')
            query_text.setdefault(q,rub['full_query']);need(query_text[q]==rub['full_query'],'Cross-cohort query drift')
        for r in rows:
            p=safe(r['path']);need(sha(p)==r['file_sha256'],'Report hash mismatch: '+r['path'])
            need(bool(p.read_text().strip()),'Empty report')
            if cohort=='main9':need(original[r['query_id'],r['report_id']]==r['evaluation_sha256'],'Evaluated report identity mismatch')
        counts[cohort]=len(rows);lookups[cohort]=lookup
    labels=read('data/annotations/human_preferences.json')['items']
    frozen={r['pair_id']:r for r in read('reproduction/offline/data/human80.json')['rows']}
    need(len(labels)==80 and len({r['pair_id'] for r in labels})==80,'Human pair count')
    used=set()
    for p in labels:
        need(p['cohort']=='studies7' and p['labels']==frozen[p['pair_id']]['human'],'Human labels changed')
        need(p['query_id']==frozen[p['pair_id']]['task'],'Human query changed')
        for side in ('A','B'):
            s=p['sides'][side];r=lookups['studies7'][p['query_id'],s['report_id']]
            need(all(s[k]==r[k] for k in ('path','file_sha256','evaluation_sha256')),'Unbound label side')
            used.add((p['query_id'],s['report_id']))
    need(len(used)==128,'Human report count')
    need(read('data/annotations/controlled_revisions.json')==read('reproduction/offline/data/controlled_selected_packet.json'),'Controlled labels changed')
    seven=read('data/results/studies7_judgments.json')
    need(seven['counts']=={'pt':5432,'graphs':280,'pairs':840,'pw':13566},'Study judgment counts')
    need(sum(map(len,seven['pairwise_by_dimension']))==13566,'Study PW count')
    docs=[ROOT/'README.md',*sorted((ROOT/'docs').glob('*.md')),ROOT/'evaluation/README.md',ROOT/'experiments/README.md']
    links=0
    for p in docs:
        for target in re.findall(r'\]\(([^)]+)\)',p.read_text()):
            if re.match(r'[a-zA-Z]+:',target) or target.startswith('#'):continue
            target=target.split('#',1)[0];need((p.parent/target).exists(),'Broken documentation link: '+target);links+=1
    return {'status':'passed','reports':counts,'queries':len(query_text),'human_pairs':80,'human_reports':128,'controlled_revisions':120,'documentation_links':links}
if __name__=='__main__':print(json.dumps(verify(),indent=2))
