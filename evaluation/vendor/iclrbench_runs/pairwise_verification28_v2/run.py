"""Minimal fixes. Frozen prior inputs, two grouped checks, one AB/BA acceptance."""
import importlib.util,copy,json,time,sys,concurrent.futures as cf
from pathlib import Path
ROOT=Path(__file__).resolve().parent;OLD=ROOT.parent/'pairwise_verification28_v1'
s=importlib.util.spec_from_file_location('previous_pw',OLD/'run.py');p=importlib.util.module_from_spec(s);s.loader.exec_module(p)
T=p.T;T.BASE=ROOT;p.v.ROOT=ROOT;p.v.old.retrieval.BASE=ROOT/'acquisition'
normalize=p.fix.normalize_explanations
original_validator=p.v.old.validate_card
def normalized_validator(out,data):return original_validator(normalize(out),data)
p.v.old.validate_card=normalized_validator

def group_checks(checks,report_hashes):
 """Same report version, exact span/assertion AND citation set. Preserve ALL questions."""
 groups={}
 for c in checks:
  key=T.digest({'report_sha':report_hashes[c['report_id']],'report_id':c['report_id'],'original_id':c['original_id'],'quote':c['quote'],'citations':sorted(x['url'] for x in c['citations'])})
  g=groups.setdefault(key,{'group_id':'G'+key[:20],'members':[],'questions':[]})
  g['members'].append(c)
  if c['question'] not in g['questions']:g['questions'].append(c['question'])
 return list(groups.values())

def packed(data):
 """Lossless source/card pools. Evidence IDs are namespaced by full content hash."""
 out=copy.deepcopy(data);ep={};cp={}
 for gp in out['guide_packets']:
  ids=[]
  for card in gp.pop('verification_cards'):
   c=copy.deepcopy(card);mapping={}
   for e in c.pop('evidence'):
    eid='E'+T.digest(e);ep[eid]=e;mapping[e['id']]=eid
   for branch in ('fact','citation'):
    if c.get('result') and branch in c['result']:
     c['result'][branch]['evidence_ids']=[mapping[i] for i in c['result'][branch]['evidence_ids']]
   c['evidence_refs']=list(mapping.values());cid=c['check_id']
   p.need(cid not in cp or cp[cid]==c,'conflicting check ID');cp[cid]=c;ids.append(cid)
  gp['verification_card_ids']=ids
 out['verification_card_pool']=list(cp.values());out['evidence_pool']=[{'evidence_ref':k,'source':v} for k,v in ep.items()]
 return out

def unpacked(data):
 out=copy.deepcopy(data);cp={c['check_id']:c for c in out.pop('verification_card_pool')};ep={e['evidence_ref']:e['source'] for e in out.pop('evidence_pool')}
 for gp in out['guide_packets']:
  cards=[]
  for cid in gp.pop('verification_card_ids'):
   c=copy.deepcopy(cp[cid]);refs=c.pop('evidence_refs');c['evidence']=[ep[i] for i in refs]
   for branch in ('fact','citation'):
    if c.get('result') and branch in c['result']:c['result'][branch]['evidence_ids']=[ep[i]['id'] for i in c['result'][branch]['evidence_ids']]
   cards.append(c)
  gp['verification_cards']=cards
 return out

JUDGE=p.JUDGE+'''\nSerialization only: each guide's verification_card_ids selects its allowed cards from verification_card_pool. Each card references evidence_pool via evidence_refs and its verdict evidence_ids; resolve those refs to the complete source passages. Pool membership is storage, NOT permission to borrow other guides' cards or another report's verdict. Scores, anchors and uncertainty policy are unchanged.'''
def valid_judge(out,data):p.valid_judge(out,unpacked(data))

def grouped_input(g,oldcards):
 """Use acquired bodies, not old verdicts. All requested scopes preserved, no new search."""
 evidences={};acquisition=[]
 for c in g['members']:
  old=oldcards[c['check_id']]
  evidence=old.get('evidence',[])
  if not evidence:
   f=OLD/'checks'/c['check_id']/'citation_input.json'
   if f.exists():evidence=T.load(f)['evidence']
  for e in evidence:
   p.need(e['id'] not in evidences or evidences[e['id']]==e,'conflicting evidence snapshots')
   evidences[e['id']]=e
  acquisition+=old.get('sources',[])
 first=g['members'][0]
 return {'check_id':g['group_id'],'question':'Check the exact quoted assertion within ALL requested scopes below; partial support must not be upgraded.\n'+json.dumps({'assertion':first['quote'],'requested_questions':g['questions']},ensure_ascii=False),'original_units':first['original_units'],'has_citation':bool(first['citations']),'evidence':list(evidences.values()),'acquisition':acquisition}

def main(execute=False):
 start=time.time();inp,suite,rs,diffs=p.setup();old=T.load(OLD/'check_bindings.json');cards=T.load(OLD/'verification_results.json');bindings=copy.deepcopy(old['bindings'])
 groups=group_checks(old['checks'],{r['report_id']:T.digest(r['segments']) for r in rs});multi=[g for g in groups if len(g['members'])>1]
 # Refuse stale upstream inputs instead of silently reusing evaluations.
 for path,sha in T.load(OLD/'protocol.json')['hashes'].items():p.need(T.sha(Path(path))==sha,'upstream changed: '+path)
 T.freeze(ROOT/'protocol.json',{'version':'minimal-scoped-pw-v2','hashes':{str(f):T.sha(f) for f in [Path(__file__),OLD/'run.py',OLD/'protocol.json',OLD/'verification_results.json',OLD/'check_bindings.json']},'scope':'Same DRBII28 R1/R3 and8guides. Reuse frozen plan/differences and prior acquired source bodies; no new search or baseline. One AB/BA acceptance only, no stability claim.','fixes':['normalize explanation string-arrays in original and inherited follow validators','group exact report/version/span/assertion/citations retaining all questions; no cross-report verdict transfer','lossless shared card/source pools'],'model':p.CFG['model'],'reasoning_effort':p.CFG['reasoning_effort'],'maximum_calls':{'grouped_deepseek':len(multi),'gpt_judge':2},'workers':20,'prompts':{'judge':JUDGE,'verify':p.v.VERIFY}})
 T.freeze(ROOT/'groups.json',groups)
 if not execute:return
 alias={};failures=[]
 def verify_group(g):
  d=grouped_input(g,cards);T.freeze(ROOT/'group_inputs'/f'{g["group_id"]}.json',d)
  out=p.v.old.ds_call(ROOT,g['group_id'],p.v.VERIFY,d,normalized_validator,p.CFG);T.freeze(ROOT/'group_outputs'/f'{g["group_id"]}.json',out)
  c=g['members'][0]
  return {'check_id':g['group_id'],'report_id':c['report_id'],'original_id':c['original_id'],'question':d['question'],'execution':'completed','result':out['result'],'evidence':d['evidence'],'sources':d['acquisition'],'member_check_ids':[x['check_id'] for x in g['members']]}
 with cf.ThreadPoolExecutor(max_workers=20) as pool:
  fs={pool.submit(verify_group,g):g for g in multi}
  for f in cf.as_completed(fs):
   g=fs[f]
   try:c=f.result();cards[c['check_id']]=c
   except Exception as e:failures.append({'stage':'group_verify','group':g['group_id'],'error':str(e)});continue
   for member in g['members']:alias[member['check_id']]=g['group_id']
 for b in bindings:b['new_check_ids']=list(dict.fromkeys(alias.get(i,i) for i in b['new_check_ids']))
 T.save(ROOT/'bindings.json',bindings);T.save(ROOT/'cards.json',cards)
 results=[];sizes={}
 def judge(order):
  d=p.packet(inp,suite,rs,diffs,bindings,cards,'verified',order);z=packed(d);p.need(unpacked(z)==d,'lossy serialization')
  T.freeze(ROOT/'judge_inputs'/f'{order}.json',z)
  sizes[order]={'inline_bytes':len(json.dumps(d,ensure_ascii=False).encode()),'pooled_bytes':len(json.dumps(z,ensure_ascii=False).encode())}
  o=T.Client().call('acceptance_'+order,JUDGE,z,valid_judge,'en','pairwise_acceptance');T.save(ROOT/'judgments'/f'{order}.json',o);return {'order':order,**o}
 with cf.ThreadPoolExecutor(max_workers=20) as pool:
  fs={pool.submit(judge,o):o for o in ('AB','BA')}
  for f in cf.as_completed(fs):
   try:results.append(f.result())
   except Exception as e:failures.append({'stage':'judge','order':fs[f],'error':str(e)})
 usage=[]
 for f in list((ROOT/'calls').glob('*/response_*.json'))+list((ROOT/'deepseek_calls').glob('*/response*.json')):
  r=T.load(f);usage.append({'path':str(f),'model':r['raw'].get('model'),'usage':r['raw'].get('usage',{}),'seconds':r.get('seconds')})
 T.save(ROOT/'summary.json',{'seconds':time.time()-start,'results':results,'failures':failures,'sizes':sizes,'usage':usage,'checks_before':len(old['checks']),'unique_objects':len(groups),'grouped_rechecks':len(multi),'new_searches':0,'complete':len(results)==2 and not failures})
 print('FINISHED',len(results),failures,flush=True)
if __name__=='__main__':main('--execute' in sys.argv)
