"""Offline structural coverage. Quality warnings do not manufacture execution."""
import hashlib
import itertools
import json
from pathlib import Path
from settings import SYSTEMS

def load(p):
    return json.loads(Path(p).read_text(encoding='utf-8'))

def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def unique(rows, key, expected):
    ids = [r.get(key) for r in rows]
    if len(ids) != len(set(ids)) or set(ids) != set(expected):
        raise ValueError('Exact coverage mismatch: '+key)
    return dict(zip(ids, rows))

def report_set(reports):
    rows = unique(reports, 'report_id', SYSTEMS)
    if any(r['system'] != SYSTEMS[i] for i, r in rows.items()):
        raise ValueError('System/report ID mapping changed')

def judgments(value, guides, rids):
    rows = unique(value['judgments'], 'guide_id', guides)
    for row in rows.values():
        w, n = row.get('preferred_report_id'), row.get('strength')
        if w not in list(rids)+['tie'] or type(n) is not int or n not in ([0] if w=='tie' else [1,2]):
            raise ValueError('Missing or invalid actual winner/strength')
        if not isinstance(row.get('reason'), str) or not row['reason'].strip():
            raise ValueError('Missing actual judgment reason')
    return rows

def valid_pair(pair, guides, rids):
    if pair.get('report_ids') != list(rids) or pair.get('pair') != '_'.join(rids):
        raise ValueError('Pair identity mismatch')
    for order in ('AB','BA'): judgments(pair[order], guides, rids)

def graph_ok(graph, units):
    cs = graph.get('claims', [])
    if not cs: raise ValueError('Empty graph')
    ids = [c.get('id') for c in cs]
    if len(ids)!=len(set(ids)) or not all(isinstance(i,str) and i for i in ids):
        raise ValueError('Invalid Claim IDs')
    for c in cs:
        if not c.get('statement') or not c.get('block_ids') or not set(c['block_ids']+c.get('condition_block_ids',[]))<=set(units):
            raise ValueError('Claim has no valid original anchor')
    for e in graph.get('relations', []):
        if e.get('conclusion') not in ids or not e.get('premises') or not set(e['premises'])<=set(ids) or e['conclusion'] in e['premises']:
            raise ValueError('Dangling or self relation')

def point_rows(point, ids):
    rows = point['final']
    if set(rows)!=set(ids): raise ValueError('Pointwise coverage mismatch')
    for r in rows.values():
        if r.get('state')!='scored' or type(r.get('score')) is not int or not 1<=r['score']<=5 or not r.get('reason'):
            raise ValueError('No actual valid pointwise score')
    return rows

def stage_proof(root, name):
    state=load(root/'stage_status'/f'{name}.json')
    if state.get('state')!='complete': raise ValueError('Stage not complete: '+name)
    entry=load(root/'stage_inputs'/f'{name}.json')
    if entry['call_key']!=state['call_key']: raise ValueError('Stale stage identity: '+name)
    folder=root/'calls'/state['call_key']; success=load(folder/'success.json')
    source=success.get('source','')
    if not source.startswith('response_') or Path(source).name!=source:
        raise ValueError('No actual response provenance: '+name)
    raw=load(folder/source)['raw']
    if raw['choices'][0].get('finish_reason')=='length':raise ValueError('Truncated source: '+name)
    return success

def inspect_task(manifest, root, require_trace=True):
    root=Path(root); suite=load(manifest['rubrics']); report_set(manifest['reports'])
    pids=[r['id'] for r in suite['pointwise']]; gids=[g['id'] for g in suite['pairwise']]
    unique(suite['pointwise'],'id',pids); unique(suite['pairwise'],'id',gids)
    content=[g['id'] for g in suite['pairwise'] if g['dimension'] not in ('D5','D6')]
    direct=[g['id'] for g in suite['pairwise'] if g['dimension'] in ('D5','D6')]
    stats={'graphs':0,'pt':0,'pw':0,'pairs':0,'pt_reviews_complete':0}
    errors=[]; points={}; pairs=[]; required=[]
    def problem(kind, identity, ex): errors.append({'stage':kind,'object':identity,'error':str(ex)})
    for r in manifest['reports']:
        rid=r['report_id']; required+=['graph_'+rid,'pt_'+rid+'_initial']
        try:
            units=load(root/'reports'/rid/'units.json'); g=load(root/'reports'/rid/'graph.json')
            graph_ok(g,{u['id'] for u in units})
            if g.get('report_id')!=rid:raise ValueError('Graph/report identity mismatch')
            stats['graphs']+=1
        except (OSError,ValueError,KeyError,TypeError) as ex:problem('graph',rid,ex)
        try:
            point=load(root/'pointwise'/rid/'result.json'); rows=point_rows(point,pids)
            points[rid]=point;stats['pt']+=len(rows)
            if any(v.get('review_complete') is False or v.get('stage')=='initial_retained_after_review_failure' for v in rows.values()):
                raise ValueError('Actual initial scores retained, but review incomplete')
            stats['pt_reviews_complete']+=len(rows)
            if require_trace:
                first=load(root/'pointwise'/rid/'initial.json')
                required += ['pt_'+rid+'_'+v['rubric_id'] for v in first['scores'] if v.get('verification_request')]
        except (OSError,ValueError,KeyError,TypeError) as ex:problem('pointwise',rid,ex)
    for a,b in itertools.combinations(SYSTEMS,2):
        key=a+'_'+b; folder=root/'pairs'/key
        if content:
            required+=['plan_'+key]+['judge_'+key+'_'+order for order in ('AB','BA')]
            required += [f'{prefix}_{key}_{n}' for n in range((len(content)+3)//4) for prefix in ('loc','diff')]
        if direct:required+=['readability_raw_'+key+'_'+order for order in ('AB','BA')]
        try:
            pair=load(folder/'result.json'); valid_pair(pair,gids,[a,b]);pairs.append(pair);stats['pairs']+=1
        except (OSError,ValueError,KeyError,TypeError) as ex:problem('pairwise',key,ex)
        # Count real valid direction items even when the merged pair is incomplete.
        for mode,gs in [('content',content),('readability',direct)]:
            file=folder/(mode+'_result.json')
            try: result=load(file)
            except (OSError,ValueError):result={}
            for order in ('AB','BA'):
                try:stats['pw']+=len(judgments(result[order],gs,[a,b]))
                except (KeyError,ValueError,TypeError):pass
    if require_trace:
        for name in required:
            try:stage_proof(root,name)
            except (OSError,ValueError,KeyError,TypeError) as ex:problem('provenance',name,ex)
    cards=[]
    for file in sorted((root/'check_results').glob('*.json')):
        try:
            card=load(file);cards.append(card)
            if card.get('execution') not in ('completed','no_material'):raise ValueError('Technical verification failure')
        except (OSError,ValueError,KeyError,TypeError) as ex:problem('verification',file.stem,ex)
    n=len(SYSTEMS)
    expected={'graphs':n,'pt':n*len(pids),'pw':n*(n-1)*len(gids),'pairs':n*(n-1)//2}
    scoring_complete=stats['pt']==expected['pt'] and stats['pairs']==expected['pairs']
    return {'task':manifest['task_key'],'counts':stats,'expected':expected,
            'scoring_complete':scoring_complete,'framework_complete':not errors and all(stats[k]==v for k,v in expected.items()),
            'errors':errors,'points':points,'pairs_data':pairs,'cards':cards,'suite':suite}

def compact(audit):
    return {k:v for k,v in audit.items() if k not in ('points','pairs_data','cards','suite')}
