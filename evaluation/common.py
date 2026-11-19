"""Shared contracts; preserve the frozen experiment implementations."""
import importlib.util,sys,copy,json,hashlib
from pathlib import Path
BASE=Path(__file__).resolve().parent/'vendor'/'iclrbench_runs'
def mod(name,path):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);sys.modules[name]=m;s.loader.exec_module(m);return m
pt=mod('unified_pt',BASE/'pointwise_request_verification28_v4/run.py')
pw=mod('unified_pw',BASE/'pairwise_verification28_v2/run.py')
loc=mod('unified_loc',BASE/'graph_downstream_adapter_pilot28_v2/run.py')
graph=mod('unified_graph',BASE/'structured_graph_gpt55_single_v2_4_claude_refs/run.py')
refs=mod('reference_links',BASE/'structured_graph_gpt55_single_v2_4_claude_refs/reference_links.py')
T=pt.T
need=pt.need
def digest(x):return hashlib.sha256(json.dumps(x,ensure_ascii=False,sort_keys=True).encode()).hexdigest()
def normalize(out):
 out=pw.normalize(out)
 for branch in ('fact','citation'):
  if branch not in out:continue
  for field in ('supports','limits'):
   value=out[branch].get(field)
   if isinstance(value,dict):
    out[branch][field]=json.dumps(value,ensure_ascii=False,sort_keys=True)
    out.setdefault('_structural_diagnostics',[]).append({'action':'lossless_scope_object_serialization','branch':branch,'field':field})
 return out
def prepare(text):
 doc,units=graph.h.prepare(text);doc,units=refs.enrich(text,doc,units)
 for parent in {u['parent_id'] for u in units if u.get('parent_id')}:
  ix=[i for i,u in enumerate(units) if u.get('parent_id')==parent];a,b=min(ix),max(ix)
  nearby=[u['id'] for u in units[max(0,a-4):a]+units[b+1:b+4] if u['kind'] not in ('heading','table_row')]
  for i in ix:units[i]['nearby_context_ids']=nearby
 return doc,units
def validate_report(r):
 ids=[u['id'] for u in r['segments']];need(len(ids)==len(set(ids)),'duplicate original ID')
 ci={c['id'] for c in r['citations']};need(all(set(u['citation_ids'])<=ci for u in r['segments']),'unknown citation')
def evenly(items,cap):
 if len(items)<=cap:return items
 need(cap>0,'positive cap');return [items[(i*len(items))//cap] for i in range(cap)]
def support_fraction(cards):
 # Technical completion includes an explicit, valid no-material result, not crashes.
 unique={c['check_id']:c for c in cards};done=[c for c in unique.values() if c.get('execution') in ('completed','no_material') and c.get('result',{}).get('fact',{}).get('status') in ('supported','partial','contradicted','insufficient_material')]
 n=sum(c['result']['fact']['status']=='supported' for c in done)
 return {'supported':n,'completed':len(done),'planned_unique':len(unique),'failed':sum(c.get('execution')=='failed' for c in unique.values()),'no_material':sum(c.get('execution')=='no_material' for c in done),'rate':n/len(done) if done else None,'basis':'fact.supported / technically completed unique check_id; no_material included, crashes excluded; selected sample only; cross-lane differently scoped questions remain distinct'}

def aggregate(suite,reports,points,pairs,cards):
 from scoring import aggregate as formal_aggregate
 return formal_aggregate(suite,reports,points,pairs,cards)
