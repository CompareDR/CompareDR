"""Portable entry point. Preparation, auditing and aggregation make no model calls."""
import argparse
import hashlib
import itertools
import json
import subprocess
import sys
from pathlib import Path

HERE=Path(__file__).resolve().parent
REPO=HERE.parent
def load(p):return json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p,x):
    p=Path(p);p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(x,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
def freeze(p,x):
    if p.exists() and load(p)!=x:raise ValueError('Existing run differs; select a new --out directory')
    if not p.exists():save(p,x)

def prepare(cohort,out):
    from provider_config import runtime_config
    m=load(REPO/f'data/reports/{cohort}/manifest.json');tasks=sorted({r['query_id'] for r in m['items']})
    for q in tasks:
        rub=REPO/f'data/evaluation/{cohort}/rubrics/{q}.json'
        rt=REPO/f'data/evaluation/{cohort}/routing/{q}.json'
        reports=[]
        for r in m['items']:
            if r['query_id']!=q:continue
            path=REPO/r['path'];assert sha(path)==r['file_sha256']
            reports.append({'report_id':r['report_id'],'system':r['system'],'path':str(path),'sha256':r['file_sha256']})
        cfg=runtime_config()
        manifest={'task_key':load(rub)['task_key'],'rubrics':str(rub),'rubrics_sha256':sha(rub),
          'routing':str(rt),'routing_sha256':sha(rt),'reports':reports,'seed_dirs':[],
          'budget':{'citation_units_per_report':None,'explicit_checks_per_report':None,'local_stage_workers':cfg['local_stage_workers']}}
        freeze(out/'manifests'/f'{q}.json',manifest)
    freeze(out/'batch.json',{'cohort':cohort,'queries':tasks,'runtime':runtime_config(),
           'manifest_hashes':{q:sha(out/'manifests'/f'{q}.json') for q in tasks}})
    return {'queries':len(tasks),'reports':len(m['items']),'api_calls':0}

def verify_run(out):
    from provider_config import runtime_config
    batch=load(out/'batch.json')
    if batch['runtime']!=runtime_config():raise ValueError('Runtime changed since preparation')
    for q,h in batch['manifest_hashes'].items():
        m=out/'manifests'/f'{q}.json';assert sha(m)==h
        v=load(m)
        for key in ('rubrics','routing'):assert sha(v[key])==v[key+'_sha256']
        for r in v['reports']:assert sha(r['path'])==r['sha256']
    return batch

def worker(out,q,execute=False):
    batch=verify_run(out);assert q in batch['queries']
    if execute:
        from provider_config import require_online
        require_online()
        from global_limits import Limits
        c=batch['runtime'];Limits(out/'limits.sqlite',gpt=c['gpt_concurrency'],ds_rpm=c['deepseek_rpm'],ds_concurrency=c['deepseek_concurrency'],gpt_rpm=c['gpt_rpm'],gpt_tpm=c['gpt_tpm']).install()
    import common as C
    import minimax_adapter
    original=C.prepare
    manifest=load(out/'manifests'/f'{q}.json')
    import completeness,scoring
    system_map={r['report_id']:r['system'] for r in manifest['reports']}
    completeness.SYSTEMS=scoring.SYSTEMS=system_map
    minimax_hashes={r['sha256'] for r in manifest['reports'] if r['report_id']=='R10'}
    C.prepare=lambda text: minimax_adapter.prepare(text,original) if hashlib.sha256(text.encode()).hexdigest() in minimax_hashes else original(text)
    import verification_fallback
    verification_fallback.install()
    import pipeline
    runner=pipeline.Runner(out/'manifests'/f'{q}.json',out/('tasks' if execute else 'preflight')/q)
    if execute:runner.run()
    else:runner.preflight()
    return {'query':q,'action':'evaluated' if execute else 'preflight','reports':len(runner.reports)}

def aggregate(out):
    batch=verify_run(out)
    import aggregate as A
    import completeness as V
    import verification_fallback as F
    keys=batch['queries'];ids=[r['report_id'] for r in load(out/'manifests'/f'{keys[0]}.json')['reports']]
    V.SYSTEMS={r['report_id']:r['system'] for r in load(out/'manifests'/f'{keys[0]}.json')['reports']}
    for q in keys:
        m=load(out/'manifests'/f'{q}.json')
        audit=F.audit_with_fallback(V.inspect_task(m,out/'tasks'/q),out/'tasks'/q)
        if not audit['framework_complete']:raise RuntimeError('Incomplete task: '+q)
    pt,raw,obs,counts,diag=A.collect(out,keys,ids)
    models,pw=A.fit_matched(obs,len(ids),len(keys));scores=A.combine(pt,pw)
    result=A.serial({'queries':keys,'systems':ids,'scores':scores,'means':scores.mean(axis=0),
                     'columns':['D1','D2','D3','D4','D5_D6','overall'],'weights':[30,30,10,10,20],
                     'counts':counts,'order_diagnostics':diag})
    save(out/'results/ordinal.json',result);save(out/'results/models.json',A.serial(models))
    return {'queries':len(keys),'systems':len(ids),'counts':counts,'api_calls':0}

def main():
    if not __debug__:raise RuntimeError('Do not disable validation with optimized Python')
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('action',choices=['prepare','preflight','run','aggregate'])
    p.add_argument('--cohort',choices=['main9','studies7'],default='main9')
    p.add_argument('--out',type=Path,required=True)
    p.add_argument('--query');p.add_argument('--execute',action='store_true')
    a=p.parse_args();out=a.out.resolve()
    if a.action=='prepare':print(prepare(a.cohort,out));return
    if a.action=='aggregate':print(aggregate(out));return
    if a.action=='run' and not a.execute:p.error('Online evaluation requires explicit --execute')
    b=verify_run(out);qs=[a.query] if a.query else b['queries']
    assert set(qs)<=set(b['queries'])
    # One process per query isolates mutable caches and module state.
    for q in qs:
        if len(qs)==1:print(worker(out,q,a.action=='run'));continue
        cmd=[sys.executable,str(HERE/'run.py'),a.action,'--out',str(out),'--query',q]
        if a.execute:cmd.append('--execute')
        subprocess.run(cmd,check=True)

if __name__=='__main__':main()
