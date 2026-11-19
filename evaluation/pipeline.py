"""Manifest-driven complete single-task pipeline. No hidden sampled reports/checks."""
import argparse,concurrent.futures as cf,copy,json,os,re,threading,time,urllib.request
from pathlib import Path
import common as C
import compat
import readability_raw as RR
import judgment_language as JL
import acquisition_fix as A
import settings
T=C.T;pt=C.pt;pw=C.pw;loc=C.loc;graph=C.graph;need=C.need

class Runner:
 def __init__(self,manifest,out):
  if not getattr(C,'soft_runtime_installed',False):
   import repair_20260919
   repair_20260919.install();C.soft_runtime_installed=True
  self.manifest_path=Path(manifest);self.m=T.load(self.manifest_path);self.out=Path(out);self.out.mkdir(parents=True,exist_ok=True)
  self.suite=T.load(Path(self.m['rubrics']));self.routing=T.load(Path(self.m['routing']));self.query=self.suite['full_query']
  need(T.sha(Path(self.m['rubrics']))==self.m['rubrics_sha256']==self.routing['rubrics_sha256'],'rubrics mismatch')
  need(T.sha(Path(self.m['routing']))==self.m['routing_sha256'],'routing mismatch')
  need({x['id'] for x in self.routing['items']}=={x['id'] for x in self.suite['pointwise']},'PT routing coverage')
  need({x['id'] for x in self.routing['pairwise']}=={x['id'] for x in self.suite['pairwise']},'PW routing coverage')
  need(self.m['budget']['citation_units_per_report'] is None and self.m['budget']['explicit_checks_per_report'] is None,'full run cannot have sampling caps')
  self.cfg=pt.v2.CFG|settings.config()
  prior=self.out/'protocol.json'
  if prior.exists():
   contract=self.out/'readability_contract.json'
   need(contract.exists() and T.load(contract).get('version')==RR.VERSION,'Readability input changed: use a NEW output directory; preserve historical results')
   frozen=T.load(prior)['models'];need(frozen['judge']==self.cfg['model'] and frozen['reasoning']==self.cfg['reasoning_effort'],'Judge changed: use a NEW output directory; do not mix old and new model results')
  self.sem=threading.BoundedSemaphore(self.cfg['workers']);self.lock=threading.Lock();self.check_locks={};self.cards={};self.events=[]
  self.reports=[];self.seed={};T.BASE=self.out;T.config=lambda:self.cfg
  for v in [pt.v2,pw.p.v]:v.ROOT=self.out;v.T.BASE=self.out;v.old.retrieval.BASE=self.out/'acquisition'
  # Single shared source cache and validators, not per-report monkeypatch races.
  pt.v2.old.retrieval.fetch=pw.p.fix.singleflight(pt.v2.old.retrieval.fetch)
  pt.v2.old.retrieval.search=pw.p.fix.singleflight(pt.v2.old.retrieval.search)
  original=pt.v2.old.validate_card;follow=pt.v2.follow_valid
  pt.v2.old.validate_card=lambda o,d:original(C.normalize(o),d)
  pt.v2.follow_valid=lambda o,d:follow(C.normalize(o),d)
  pt.v2.old.ds_call=compat.recover_deepseek(pt.v2.old.ds_call)
  self.verify_rules=pt.v2.old.policy.policy(self.query)
  A.R.BASE=self.out/'acquisition_fetchfix1'
  for root in self.m.get('seed_dirs',[]):
   for f in Path(root).glob('calls/*/identity.json'):
    s=f.parent/'success.json'
    if s.exists():
     identity=T.load(f);self.seed[C.digest({'body':identity['body'],'endpoint':identity['endpoint']})]=(s,identity)

 def event(self,stage,state,**kw):
  with self.lock:
   self.events.append({'time':time.time(),'stage':stage,'state':state,**kw});T.save(self.out/'progress.json',self.events)
  print(stage,state,flush=True)

 def call(self,name,prompt,data,validator,max_tokens=12000,raw=False):
  import soft_contracts as S
  max_tokens=settings.token_budget(name,self.cfg)
  if name.startswith(('graph_','loc_','diff_')):prompt=settings.language(prompt)
  if name.startswith('loc_'):prompt=prompt.replace('Empty selection allowed only with explicit limitation; do not manufacture content.','For each side select a supplied Claim or a relevant supplied section for original-text inspection. If the graph lacks relevant Claims, request a section and explain the limitation; do not manufacture content.')
  if name.startswith('diff_'):prompt=prompt.replace("Different guides may share a passage but cannot borrow each other's selected IDs or Claims.","All supplied same-report IDs in this batch may be referenced; never cross reports or invent IDs.")
  original=validator
  validate=lambda o,d:compat.validate_output(name,o,d,original)
  try:out=S.invoke(self.out,name,prompt,data,validate,self.cfg,T,max_tokens=max_tokens,raw=raw,sem=self.sem,context=getattr(original,'soft_context',None))
  except Exception as ex:
   T.save(self.out/'stage_status'/f'{name}.json',{'state':'failed','error':str(ex)});raise
  T.save(self.out/'stage_status'/f'{name}.json',{'state':'complete','acceptance':out['acceptance'],'call_key':out['call_key'],'returned_model':out.get('returned_model')})
  self.event(name,out['acceptance'])
  return out['result']

 def ds(self,name,prompt,data,validator):
  with self.sem:out=pt.v2.old.ds_call(self.out,name,prompt,data,validator,self.cfg)
  self.event(name,'completed');return out['result']

 def preflight(self):
  import soft_contracts as S
  T.freeze(self.out/'soft_limit_contract.json',{'version':S.VERSION,'module_sha':T.sha(Path(S.__file__)),'gpt_total_attempts':self.cfg['attempts'],'deepseek_total_attempts':self.cfg['ds_attempts'],'on_exhaustion':'Accept usable real output with recorded warnings; no response, empty graph or absent decision remains failed','cache':'Same request and contract; offline revalidate before reuse; no outcome-based retry'})
  for r in self.m['reports']:
   src=Path(r['path']);need(T.sha(src)==r['sha256'],'report changed '+r['report_id']);doc,units=C.prepare(src.read_text())
   report={**r,'original_text':src.read_bytes().decode('utf-8'),'segments':[u|{'paragraph_id':u.get('parent_id',u['id'])} for u in units],'citations':doc['citations'],'document':doc,'units':units};C.validate_report(report);self.reports.append(report)
   T.freeze(self.out/'reports'/r['report_id']/'document.json',doc);T.freeze(self.out/'reports'/r['report_id']/'units.json',units)
  T.freeze(self.out/'manifest.json',self.m)
  T.freeze(self.out/'readability_contract.json',{'version':RR.VERSION,'code_sha':T.sha(Path(RR.__file__)),'inputs':'query, frozen D5/D6 guides, two complete original UTF-8 reports; physical AB/BA swap; no graph, units or verification cards','evidence':'verbatim original quotes, not extracted segment IDs'})
  T.freeze(self.out/'structural_contract.json',{'version':'compat-v1','code_sha':T.sha(Path(compat.__file__)),'policy':'Optional fields normalized; unassigned claims remain searchable; self-edges quarantined; invalid mapped assertions retained in diagnostics without blocking valid siblings; no fabricated evidence or scores.'})
  T.freeze(self.out/'protocol.json',{'version':self.cfg['version'],'query_sha':C.digest(self.query),'rubrics_sha':self.m['rubrics_sha256'],'routing_sha':self.m['routing_sha256'],'runtime':settings.config(),'models':{'judge':self.cfg['model'],'reasoning':self.cfg['reasoning_effort'],'verifier':self.cfg['verifier_model'],'thinking':'disabled'},'reports':len(self.reports),'pairs':len(self.reports)*(len(self.reports)-1)//2,'sampling':'all selected cohort reports and frozen PT/PW guides; score-relevant checks','retrieval_budget':'All bound original URLs considered within acquisition time budget; unread URLs explicitly recorded; supplement <=2 searches, <=6 candidates, <=2 acquired bodies. Public-address checks remain enabled.','aggregation':'PT/PW lane means equally combined within dimension; five dimension weights30/30/10/10/20; per-task arithmetic diagnostic only; use run.py aggregate for paper ordinal scores; D5D6 average; equal queries; physical AB/BA signed arithmetic mean; agreement and support rate diagnostic only','completion':'Real responses required for graph/location/differences/plan/scoring; format warnings allowed; no fabricated judgments; technical failures separate from legitimate no-material verdicts','cache':'request + code-contract identity; valid results reused after offline validation; failures retried within frozen budget'})
  T.save(self.out/'preflight.json',{'reports':[{'report_id':r['report_id'],'units':len(r['units']),'citation_units':sum(bool(u['citation_ids']) for u in r['units']),'citation_occurrences':sum(len(u['citation_ids']) for u in r['units']),'table_context_rows':sum('nearby_context_ids' in u for u in r['units'])} for r in self.reports],'pointwise':len(self.suite['pointwise']),'pairwise':len(self.suite['pairwise'])})

 def build_graph(self,r):
  data=graph.payload(self.query,r['units']);text=graph.format_input(data)
  def valid(o,d):
   compat.graph_output(o,r['units'])
  valid.soft_context={'units':r['units']}
  g=self.call('graph_'+r['report_id'],graph.PROMPT,text,valid,32000,True);g=copy.deepcopy(g);g['report_id']=r['report_id']
  for c in g['claims']:c['segment_ids']=list(dict.fromkeys(c['block_ids']+c['condition_block_ids']))
  for e in g['relations']:e['segment_ids']=e['block_ids']
  r['graph']=g;T.save(self.out/'reports'/r['report_id']/'graph.json',g);return r

 def verify(self,c,r):
  c=copy.deepcopy(c);ident={k:c.get(k) for k in ('question','quote','original_id','original_units','citations','search_query')};ident['report_sha']=r['sha256'];ident['verification_protocol']='formal-original-first-v3';ident['verifier_model']=self.cfg['verifier_model'];ident['prompts']=[pt.v2.VERIFY,pt.v2.FOLLOW];ident['retrieval']=A.R.CONFIG;ident['implementation']=settings.contract_hash();ident['acquisition_seconds']=self.cfg['acquisition_seconds'];ident['code']=[T.sha(Path(A.__file__)),T.sha(Path(A.R.__file__)),T.sha(Path(compat.__file__))];key='K'+C.digest(ident)[:24];c['check_id']=key
  with self.lock:lock=self.check_locks.setdefault(key,threading.Lock())
  with lock:
   saved=self.out/'check_results'/f'{key}.json'
   card=T.load(saved) if saved.exists() else None
   attempts=card.get('outer_attempts',0) if card else 0
   if card is None or (card.get('execution')=='failed' and attempts<self.cfg['check_attempts']):
    if card is not None:T.save(self.out/'check_history'/key/f'failure_{attempts}.json',card)
    try:
     card=A.verify(c,self.verify_rules,self.out,self.cfg)
    except Exception as ex:
     partial=self.out/'checks'/key/'citation_input.json';ev=T.load(partial).get('evidence',[]) if partial.exists() else []
     card={'check_id':key,'origins':c.get('origins',[]),'original_id':c['original_id'],'question':c['question'],'execution':'failed','error':str(ex),'evidence':ev}
    card|={'outer_attempts':attempts+1,'identity':ident,'report_id':r['report_id'],'report_sha':r['sha256'],'quote':c.get('quote'),'lane':c.get('lane','request'),'original_id':c['original_id'],'question':c['question'],'origins':c.get('origins',[])};T.save(saved,card)
   with self.lock:self.cards[key]=card
  return card

 def pointwise(self,r):
  rid=r['report_id'];report=[{'id':u['id'],'text':u['text']} for u in r['segments']];sha=T.digest(report);modes={x['id']:x for x in self.routing['items']};rb={x['id']:x for x in self.suite['pointwise']}
  data={'query':self.query,'report':report,'rubrics':self.suite['pointwise']}
  prompt=pt.v2.INITIAL+'\nThe following IDs are report-only and must return verification_request:null: '+', '.join(i for i,x in modes.items() if x['mode']=='report_only')+'. For these explicitly evidence-dependent IDs: '+', '.join(i for i,x in modes.items() if x['mode']=='required')+', request ONE concrete representative factual/citation check tied to an exact original passage. If no eligible assertion exists, return null and explain that report-observable absence in reason. Other criteria request a check only if it could change the score. Code binds ALL explicit URLs in that original unit and attempts them before supplemental search. Paragraph membership is only candidate attribution: ask whether those citations actually support the quoted assertion, not all facts in the paragraph. Never request a whole-report citation audit. A narrow check does not certify the whole report.'
  def validate(o,d):
   pt.v2.validate_initial(o,d)
   for x in o['scores']:
    if modes[x['rubric_id']]['mode']=='report_only':need(x['verification_request'] is None,'report-only check')
  validate.soft_context={'report_only':[i for i,x in modes.items() if x['mode']=='report_only']}
  unmapped=[];failed_maps=[];cards=[];requests=[];request_cards={}
  with cf.ThreadPoolExecutor(max_workers=self.m['budget'].get('local_stage_workers',20)) as pool:
   first=pool.submit(self.call,'pt_'+rid+'_initial',prompt,data,validate)
   initial=first.result();requests=pt.v2.bind(initial['scores'],sha,r['segments'],r['citations']);checks=requests
   T.save(self.out/'pointwise'/rid/'initial.json',initial);T.save(self.out/'pointwise'/rid/'requests.json',checks)
   futures={pool.submit(self.verify,c,r):c for c in checks}
   for f in cf.as_completed(futures):
    c=futures[f];card=f.result();cards.append(card)
    for origin in c.get('origins',[]):request_cards.setdefault(origin['rubric_id'],[]).append(card)
  cards=list({c['check_id']:c for c in cards}.values());T.save(self.out/'pointwise'/rid/'checks.json',{'cards':cards,'unmapped':unmapped,'failed_maps':failed_maps})
  final={x['rubric_id']:{'state':'scored',**x,'stage':'initial'} for x in initial['scores']};um={u['id']:u for u in report}
  def finish(item):
   i,mode=item
   row=next(x for x in initial['scores'] if x['rubric_id']==i);q=row['verification_request']
   if not q:return i,final[i]
   use=request_cards.get(i,[])
   if not use or any(c.get('execution')=='failed' for c in use):raise RuntimeError('Verification technical failure or missing binding; initial score retained, review not completed')
   d={'query':self.query,'condition':'verified','items':[{'rubric':rb[i],'initial':row,'original_context':[um[u] for u in sorted(set(row['original_ids'])|{q['original_id']})],'verification':sorted(use,key=lambda c:c['check_id'])}]}
   out=self.call('pt_'+rid+'_'+i,pt.v2.REVIEW,d,pt.v2.validate_review);return i,{'state':'scored',**out['reviews'][0]}
  with cf.ThreadPoolExecutor(max_workers=20) as pool:
   futures={pool.submit(finish,x):x[0] for x in modes.items()}
   for f in cf.as_completed(futures):
    try:i,value=f.result();final[i]=value
    except Exception as ex:
     i=futures[f];final[i]=final[i]|{'stage':'initial_retained_after_review_failure','review_error':str(ex),'review_complete':False}
     T.save(self.out/'soft_errors'/('pt_review_'+rid+'_'+i+'.json'),{'action':'retain_actual_initial_score','error':str(ex),'rubric_id':i})
  out={'final':final,'scores_complete':set(final)==set(rb) and all(x['state']=='scored' for x in final.values()),'complete':set(final)==set(rb) and all(x['state']=='scored' and x.get('review_complete',True) for x in final.values()),'mapping_failures':failed_maps,'unmapped':unmapped,'check_ids':sorted(c['check_id'] for c in cards)};T.save(self.out/'pointwise'/rid/'result.json',out);self.event('pointwise_'+rid,'completed' if out['complete'] else 'failed');return out

 def differences(self,pair):
  key='_'.join(r['report_id'] for r in pair);routing={g['id']:g['mode'] for g in self.routing['pairwise']};gs=[g for g in self.suite['pairwise'] if routing[g['id']]=='graph_content'];diffs=[]
  def batch(n,gg):
   data={'query':self.query,'reports':[loc.compact(r) for r in pair],'comparison_questions':gg}
   selection=self.call(f'loc_{key}_{n}',loc.LOC,data,lambda o,d:loc.validate_location(o,d,{r['report_id']:r for r in pair}),24000)
   packets=[];union={r['report_id']:set() for r in pair}
   for row in selection['locations']:
    ss=[loc.local(r,next(s for s in row['sides'] if s['report_id']==r['report_id'])) for r in pair]
    for s in ss:union[s['report_id']].update(s['allowed_original_ids'])
    packets.append({'guide':next(g for g in gg if g['id']==row['guide_id']),'sides':[{k:v for k,v in s.items() if k not in ('retrieval_reasons','selection')} for s in ss],'alignment_reason':row['alignment_reason'],'coverage_limit':row['coverage_limit']})
   dd={'query':self.query,'report_pools':[{'report_id':r['report_id'],'originals':[{'id':u['id'],'kind':u['kind'],'text':u['text']} for u in r['segments'] if u['id'] in union[r['report_id']]]} for r in pair],'guide_packets':packets}
   out=self.call(f'diff_{key}_{n}',loc.DIFF,dd,loc.validate_difference,24000)
   T.save(self.out/'pairs'/key/'guide_coverage'/f'{n}.json',{'locations':selection,'results':out,'input_sha':T.digest(dd)})
   return [d|{'id':row['guide_id']+'.'+d['id'],'guide_id':row['guide_id']} for row in out['results'] for d in row['differences']]
  with cf.ThreadPoolExecutor(max_workers=20) as pool:
   for rows in pool.map(lambda j:batch(*j),[(n,gs[i:i+4]) for n,i in enumerate(range(0,len(gs),4))]):diffs+=rows
  T.save(self.out/'pairs'/key/'differences.json',diffs);return diffs

 def pairwise(self,pair,diffs,include_readability=True):
  key='_'.join(r['report_id'] for r in pair);ps=[]
  with self.lock:available=[c for c in getattr(self,'frozen_pt_cards',self.cards.values()) if c.get('execution') in ('completed','no_material')]
  for d in diffs:
   sides=[]
   for side in d['sides']:
    r=next(r for r in pair if r['report_id']==side['report_id'])
    sides.append(side|{'originals':[u for u in r['segments'] if u['id'] in side['segment_ids']],'candidate_cards':[{'check_id':c['check_id'],'original_id':c['original_id'],'question':c['question'],'result':c.get('result'),'execution':c['execution']} for c in available if c['report_id']==r['report_id'] and c.get('original_id') in side['segment_ids']]})
   ps.append(d|{'sides':sides})
  route={g['id']:g['mode'] for g in self.routing['pairwise']};data={'query':self.query,'guides':[g for g in self.suite['pairwise'] if route[g['id']]=='graph_content'],'differences':ps}
  plan=self.call('plan_'+key,pw.p.PLAN,data,pw.p.valid_plan);checks,bindings=pw.p.bind_checks(plan,pair)
  # Consolidate exact assertion objects, retaining every distinct requested scope.
  groups=pw.group_checks(checks,{r['report_id']:r['sha256'] for r in pair});alias={}
  def work(g):
   c=copy.deepcopy(g['members'][0]);c['origins']=[o for m in g['members'] for o in m['origins']]
   if len(g['questions'])>1:c['question']='Verify the quoted assertion for all requested scopes: '+json.dumps(g['questions'],ensure_ascii=False)
   r=next(r for r in pair if r['report_id']==c['report_id']);return g,self.verify(c,r)
  with cf.ThreadPoolExecutor(max_workers=20) as pool:
   for g,c in pool.map(work,groups):
    for member in g['members']:alias[member['check_id']]=c['check_id']
  for b in bindings:b['new_check_ids']=list(dict.fromkeys(alias[i] for i in b['new_check_ids']))
  with self.lock:cards=copy.deepcopy(self.cards)
  needed={i for b in bindings for i in b.get('new_check_ids',[])}
  if any(cards.get(i,{}).get('execution')=='failed' for i in needed):raise RuntimeError('Pairwise verification has technical failure; content judgment not silently downgraded')
  T.save(self.out/'pairs'/key/'bindings.json',bindings)
  results={'pair':key,'report_ids':[r['report_id'] for r in pair]}
  def judge(order):
   direct,content=RR.split_guides(self.suite);outputs=[]
   if content:
    d=pw.p.packet({'query':self.query},self.suite|{'pairwise':content},pair,diffs,bindings,cards,'verified',order);packed=pw.packed(d);need(pw.unpacked(packed)==d,'lossy pooled packet')
    coverage={}
    for f in sorted((self.out/'pairs'/key/'guide_coverage').glob('*.json')):
     stored=T.load(f)
     for row in stored['results']['results']:coverage[row['guide_id']]={'difference_limits':row.get('limitations'),'extraction_acceptance':stored['results'].get('_soft_acceptance'),'localization':next(x for x in stored['locations']['locations'] if x['guide_id']==row['guide_id'])}
    rank={r['report_id']:i for i,r in enumerate(packed['reports'])}
    for gp in packed['guide_packets']:
     scoped=copy.deepcopy(coverage.get(gp['guide']['id'],{'status':'coverage_record_missing'}))
     if 'localization' in scoped:scoped['localization']['sides'].sort(key=lambda s:rank[s['report_id']])
     gp['upstream_coverage']=scoped
    outputs.append(self.call('judge_'+key+'_'+order,JL.without_forced_language(pw.JUDGE),packed,pw.valid_judge))
   if direct and include_readability:
    raw_data=RR.payload(self.query,direct,pair,order)
    outputs.append(self.call('readability_raw_'+key+'_'+order,JL.without_forced_language(RR.PROMPT),raw_data,RR.validate))
   return order,RR.merge(self.suite if include_readability else self.suite|{'pairwise':content},*outputs)
  with cf.ThreadPoolExecutor(max_workers=2) as pool:
   for order,result in pool.map(judge,['AB','BA']):results[order]=result
  T.save(self.out/'pairs'/key/('result.json' if include_readability else 'content_result.json'),results);return results

 def readability(self,pair):
  key='_'.join(r['report_id'] for r in pair);direct,_=RR.split_guides(self.suite)
  def judge(order):
   if not direct:return order,{'judgments':[]}
   d=RR.payload(self.query,direct,pair,order)
   return order,self.call('readability_raw_'+key+'_'+order,JL.without_forced_language(RR.PROMPT),d,RR.validate)
  with cf.ThreadPoolExecutor(max_workers=2) as pool:result=dict(pool.map(judge,['AB','BA']))
  T.save(self.out/'pairs'/key/'readability_result.json',result);return result

 def run(self):
  start=time.time();self.preflight();points={};pairs=[];failures=[];raw_results={};content_results={}
  import itertools
  combinations=list(itertools.combinations(self.reports,2))
  with cf.ThreadPoolExecutor(max_workers=self.cfg['local_stage_workers']) as pool:
   graphs={pool.submit(self.build_graph,r):r for r in self.reports};pts={pool.submit(self.pointwise,r):r for r in self.reports}
   raw_jobs={pool.submit(self.readability,p):p for p in combinations}
   for f in cf.as_completed(graphs):
    try:f.result()
    except Exception as ex:failures.append({'stage':'graph','report_id':graphs[f]['report_id'],'error':str(ex)})
   diffs={pool.submit(self.differences,p):p for p in combinations if all('graph' in r for r in p)}
   for f in cf.as_completed(pts):
    try:
     value=f.result();points[pts[f]['report_id']]=value
     if not value['complete']:failures.append({'stage':'pointwise_review','report_id':pts[f]['report_id'],'error':'Initial scores present but required review did not complete'})
    except Exception as ex:failures.append({'stage':'pointwise','report_id':pts[f]['report_id'],'error':str(ex)})
   registry=self.out/'frozen_pt_verification_registry.json'
   with self.lock:self.frozen_pt_cards=T.load(registry) if registry.exists() else copy.deepcopy(sorted(self.cards.values(),key=lambda c:c['check_id']))
   T.freeze(registry,self.frozen_pt_cards)
   jobs={}
   for f in cf.as_completed(diffs):
    pair=diffs[f]
    try:jobs[pool.submit(self.pairwise,pair,f.result(),False)]=pair
    except Exception as ex:failures.append({'stage':'differences','pair':[r['report_id'] for r in pair],'error':str(ex)})
   for f in cf.as_completed(jobs):
    try:content_results['_'.join(r['report_id'] for r in jobs[f])]=f.result()
    except Exception as ex:failures.append({'stage':'pairwise','pair':[r['report_id'] for r in jobs[f]],'error':str(ex)})
   for f in cf.as_completed(raw_jobs):
    try:raw_results['_'.join(r['report_id'] for r in raw_jobs[f])]=f.result()
    except Exception as ex:failures.append({'stage':'readability','pair':[r['report_id'] for r in raw_jobs[f]],'error':str(ex)})
  for pair in combinations:
   ids=[r['report_id'] for r in pair];key='_'.join(ids)
   if key not in raw_results or key not in content_results:continue
   merged={'pair':key,'report_ids':ids}
   for order in ('AB','BA'):merged[order]=RR.merge(self.suite,content_results[key][order],raw_results[key][order])
   T.save(self.out/'pairs'/key/'result.json',merged);pairs.append(merged)
  cards=sorted(self.cards.values(),key=lambda c:c['check_id']);T.save(self.out/'verification_registry.json',cards)
  try:result=C.aggregate(self.suite,self.reports,points,pairs,cards);T.save(self.out/'aggregate.json',result)
  except Exception as ex:
   result={'direction_agreement':{},'total_status':'aggregation_failed'};failures.append({'stage':'aggregation','error':str(ex)})
  usage=[]
  for path in list((self.out/'calls').glob('*/response*.json'))+list((self.out/'deepseek_calls').glob('*/response*.json')):
   a=T.load(path);usage.append({'path':str(path),'model':a['raw'].get('model'),'usage':a['raw'].get('usage',{}),'seconds':a.get('seconds')})
  T.save(self.out/'summary.json',{'seconds':time.time()-start,'scoring_complete':len(points)==len(self.reports) and all(p.get('complete') for p in points.values()) and len(pairs)==len(combinations) and not failures,'failures':failures,'mapping_failures':{r:p.get('mapping_failures',[]) for r,p in points.items()},'check_failures':[c['check_id'] for c in cards if c['execution']=='failed'],'new_usage_all_returned_attempts':usage,'unknown_usage_errors':[str(p) for p in (self.out/'calls').glob('*/error*.json')],'cache_reuse_events':[e for e in self.events if 'cache' in e['state']],'aggregation':result['direction_agreement'],'total_status':result['total_status']})
  s=T.load(self.out/'summary.json');s['soft_contracts']={'version':'formal-soft-contracts-v2','errors':[str(p) for p in sorted((self.out/'soft_errors').glob('*.json'))]};s['framework_complete']=s['scoring_complete'] and not s['check_failures'];T.save(self.out/'summary.json',s)
  self.event('pipeline','finished',failures=len(failures))

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--manifest',required=True);ap.add_argument('--out',required=True);ap.add_argument('--execute',action='store_true');a=ap.parse_args();r=Runner(a.manifest,a.out)
 if a.execute:r.run()
 else:r.preflight();print('PREFLIGHT COMPLETE; no API calls')
if __name__=='__main__':main()
