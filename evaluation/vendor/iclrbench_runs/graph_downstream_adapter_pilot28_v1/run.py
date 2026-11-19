"""Frozen graph adapter pilot: localization, differences, source/edge packets only."""
import sys,json,copy,itertools,time,concurrent.futures as cf
from pathlib import Path
ROOT=Path(__file__).resolve().parent
BASE=ROOT.parent
ENGINE=BASE/'route_value_pilot3_v2'
sys.path.insert(0,str(ENGINE))
from run_extract import transport,config
from run_interface1_scope_dev27 import PROMPT as LOC
from run_graph_rubric_ablation_dev25 import location_validate
from run_guided_early_dev34 import DIFF,validate_diff
RELEASE=BASE/'route_value_rubrics40_v3/exports/versions/query-rubrics_final/rubrics/drb2_28.json'
POINTER=BASE/'structured_graph_gpt55_single_v2_4_claude_refs/CURRENT_FOUR_SYSTEMS.json'
CFG=config|{'model':'gpt-5.5','reasoning_effort':'medium','workers':20,'attempts':2,'max_tokens':24000,'request_timeout_seconds':300}
transport.BASE=ROOT
transport.config=lambda:CFG

def need(ok,msg):
 if not ok:raise ValueError(msg)

def adapt(folder,rid):
 units=transport.load(folder/'units.json');doc=transport.load(folder/'document.json');g=copy.deepcopy(transport.load(folder/'graph_output.json')['result'])
 sources={u['id']:u for u in units};citations={c['id']:c for c in doc['citations']}
 g['report_id']=rid
 for c in g['claims']:
  c['segment_ids']=list(dict.fromkeys(c['block_ids']+c.get('condition_block_ids',[])))
  need(set(c['segment_ids'])<=set(sources),'claim source ID')
  need(set(c['citation_ids'])<=set(citations),'citation ID')
 for e in g['relations']:e['segment_ids']=e['block_ids']
 segments=[u|{'paragraph_id':u.get('parent_id',u['id'])} for u in units]
 # Reference-link URLs must remain available even when the definition is
 # outside the paragraph. Metadata never asserts claim-source entailment.
 return {'report_id':rid,'segments':segments,'graph':g,'citations':list(citations.values())}

def expand(loc,reports):
 result=copy.deepcopy(loc);rs={r['report_id']:r for r in reports}
 for reg in result['regions']:
  for s in reg['sides']:
   r=rs[s['report_id']];selected=set(s['segment_ids']);conditions=set();anchors=set()
   for c in r['graph']['claims']:
    if c['id'] in s['node_ids']:
     anchors.update(c['block_ids']);conditions.update(c.get('condition_block_ids',[]))
   selected|=anchors|conditions
   parents={u['paragraph_id'] for u in r['segments'] if u['id'] in selected}
   expanded={u['id'] for u in r['segments'] if u['paragraph_id'] in parents}|selected
   s['code_added_condition_ids']=sorted(conditions-set(s['segment_ids']))
   s['code_added_claim_anchor_ids']=sorted(anchors-set(s['segment_ids']))
   s['code_added_table_context_ids']=sorted(expanded-selected)
   s['segment_ids']=[u['id'] for u in r['segments'] if u['id'] in expanded]
 return result

def packet(diff,reports):
 rows=[]
 for d in diff['differences']:
  sides=[]
  for s in d['sides']:
   r=next(r for r in reports if r['report_id']==s['report_id']);claims=[c for c in r['graph']['claims'] if c['id'] in s['claim_ids']]
   basis=set(s['segment_ids']);conditions={i for c in claims for i in c.get('condition_block_ids',[])}
   anchors={i for c in claims for i in c['block_ids']};evidence=basis|conditions|anchors
   citation_ids={i for c in claims for i in c['citation_ids']}|{i for u in r['segments'] if u['id'] in evidence for i in u.get('citation_ids',[])}
   cs=[c for c in r['citations'] if c['id'] in citation_ids]
   ids=set(s['claim_ids']);edges=[e for e in r['graph']['relations'] if ids&(set(e['premises'])|{e['conclusion']})]
   sides.append(s|{'claims':claims,'original_units':[u for u in r['segments'] if u['id'] in evidence],'citation_candidates':cs,'candidate_support_edges':[e for e in edges if e['type']=='support'],'context_relations':[e for e in edges if e['type']!='support'],'external_support_verified':False})
  rows.append(d|{'sides':sides})
 return rows

LOC_PROMPT=LOC+'''\nAdapter contract: segments are natural paragraphs/list items/table rows, not fixed character slices. Claim block_ids ground its statement; condition_block_ids ground scope. segment_ids is their compatibility union. Citation metadata is source attribution, NOT verified support. Read the full text as fallback. Code restores selected-node anchors, conditions and sibling rows of a selected table; this is context, not proof every row is relevant. Relations may be support, qualification, synthesis or rebuttal; only support is a candidate inferential dependency, still unverified.
Batch mode: comparison_questions has at most four guides. Return {"locations":[{"guide_id":"supplied ID","regions":[...],"coverage_limit":"..."}]}, exactly one per guide. Apply locator independently; no scores or differences.'''
DIFF_PROMPT=DIFF+'''\nAll report graph IDs are scoped by report_id. A citation candidate does not establish support. Preserve applicable condition_block_ids in your substantive interpretation; do not treat code-added table context as equally relevant. Synthesis, qualification and rebuttal are NOT interchangeable with support.
Batch: guide_packets has separate comparison_question and regions. Return {"results":[{"guide_id":"supplied ID","differences":[...],"limitations":"..."}]}, exactly one per guide. Use only that guide's regions and selected segments; other guides' original segments are not evidence for this one.'''

def main(execute=False):
 start=time.time();suite=transport.load(RELEASE);p=transport.load(POINTER)
 reports=[adapt(Path(x['path']),f'R{i}') for i,x in enumerate(p['reports'],1)]
 clean=lambda x:{k:v for k,v in x.items() if k in ('id','dimension','title','question','anchors','boundary','required_input')}
 guides=[clean(g) for g in suite['pairwise']];content=[g for g in guides if g['dimension'] not in ('D5','D6')]
 source_hashes={}
 for x in p['reports']:
  folder=Path(x['path']);pr=transport.load(folder/'protocol.json')
  need(transport.sha(Path(pr['source']))==pr['source_sha256'],'report changed since graph')
  need(pr['query_sha256']==__import__('hashlib').sha256(suite['full_query'].encode()).hexdigest(),'query mismatch')
  for name in ['graph_output.json','units.json','document.json']:source_hashes[str(folder/name)]=transport.sha(folder/name)
 transport.freeze(ROOT/'inputs.json',{'query':suite['full_query'],'reports':reports,'guides':guides})
 transport.freeze(ROOT/'protocol.json',{'task':suite['task_key'],'rubrics_sha':transport.sha(RELEASE),'code_sha':transport.sha(Path(__file__)),'source_hashes':source_hashes,'config':CFG,'location_prompt':LOC_PROMPT,'difference_prompt':DIFF_PROMPT,'expected_calls':24,'scope':'6 pairs x5 content guides, max4 guides/batch; 3 presentation guides direct-text bypass; no scoring, search or graph regeneration','limits':'Connectivity and semantic spot review only; no stability repeat and no graph-vs-fulltext causal comparison'})
 print('PREFLIGHT PASS: 4 graphs, 5 content guides, 3 direct-text guides',flush=True)
 if not execute:return
 def job(pair,n,gs):
  key='_'.join(r['report_id'] for r in pair)+f'/batch{n}';folder=ROOT/'pairs'/key
  try:
   data={'query':suite['full_query'],'reports':pair,'comparison_questions':gs}
   def vl(o,d):
    rows=o['locations'];need(len(rows)==len(gs) and {x['guide_id'] for x in rows}=={g['id'] for g in gs},'location guide coverage')
    for row in rows:location_validate({'regions':row['regions'],'coverage_limit':row['coverage_limit']},d)
   transport.freeze(folder/'location_input.json',data)
   loc=transport.Client().call(key+'_loc',LOC_PROMPT,data,vl,'en','location');transport.save(folder/'location_output.json',loc)
   contexts={};packets=[];union={r['report_id']:set() for r in pair}
   for row in loc['result']['locations']:
    guide=next(g for g in gs if g['id']==row['guide_id']);ex=expand({'regions':row['regions'],'coverage_limit':row['coverage_limit']},pair)
    rs=[]
    for r in pair:
     ids={i for reg in ex['regions'] for s in reg['sides'] if s['report_id']==r['report_id'] for i in s['segment_ids']};union[r['report_id']]|=ids
     rs.append(r|{'segments':[u for u in r['segments'] if u['id'] in ids]})
    contexts[guide['id']]={'query':suite['full_query'],'reports':rs,'regions':ex['regions'],'comparison_question':guide}
    packets.append({'comparison_question':guide,'regions':ex['regions']})
   dd={'query':suite['full_query'],'reports':[r|{'segments':[u for u in r['segments'] if u['id'] in union[r['report_id']]]} for r in pair],'guide_packets':packets}
   def vd(o,d):
    rows=o['results'];need(len(rows)==len(gs) and {x['guide_id'] for x in rows}=={g['id'] for g in gs},'difference guide coverage')
    for row in rows:validate_diff(row,contexts[row['guide_id']])
   transport.freeze(folder/'difference_input.json',dd)
   out=transport.Client().call(key+'_diff',DIFF_PROMPT,dd,vd,'en','difference');transport.save(folder/'difference_output.json',out)
   evidence=[{'guide_id':row['guide_id'],'differences':packet(row,pair),'limitations':row['limitations']} for row in out['result']['results']]
   transport.save(folder/'evidence_packets.json',evidence)
   state={'key':key,'status':'completed','guides':len(gs),'differences':sum(len(r['differences']) for r in evidence)}
  except Exception as e:state={'key':key,'status':'failed','error':str(e)}
  transport.save(folder/'status.json',state);print(json.dumps(state),flush=True);return state
 jobs=[(list(pair),n,content[i:i+4]) for pair in itertools.combinations(reports,2) for n,i in enumerate(range(0,len(content),4))]
 rows=[]
 with cf.ThreadPoolExecutor(max_workers=20) as pool:
  futures=[pool.submit(job,*j) for j in jobs]
  for f in cf.as_completed(futures):
   rows.append(f.result());transport.save(ROOT/'progress.json',{'finished_batches':len(rows),'total_batches':len(jobs),'rows':rows})
 transport.save(ROOT/'summary.json',{'seconds':time.time()-start,'rows':rows,'completed':sum(r['status']=='completed' for r in rows),'total':len(jobs),'all_pass':all(r['status']=='completed' for r in rows)})

if __name__=='__main__':main('--execute' in sys.argv)
