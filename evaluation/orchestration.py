"""Seven-system frozen entry. Nothing calls a model without --execute."""
import argparse
import concurrent.futures as cf
import fcntl
import hashlib
import json
import os
import shutil
import subprocess
import sys
import threading
import time
from pathlib import Path
import completeness as V
import settings

ROOT=settings.ROOT
DEFAULT=ROOT/'full40'
SOURCE=ROOT.parent/'framework_deepseek7_20260922_v1/full40'

def save(path, obj):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    temp=path.with_name(path.name+f'.{os.getpid()}.{threading.get_ident()}.tmp')
    temp.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n');temp.replace(path)

def freeze(path, obj):
    if Path(path).exists():
        if V.load(path)!=obj:raise ValueError('Frozen artifact changed: '+str(path))
    else:save(path,obj)

def code_inventory():
    files=list(ROOT.glob('*.py'))+[ROOT/'runtime_config.json']+list((ROOT/'vendor').rglob('*.py'))+list((ROOT/'vendor').rglob('config.json'))
    return {str(p.relative_to(ROOT)):V.sha(p) for p in sorted(files) if 'framework_gpt55_seven_formal_20260922_v1' not in str(p.relative_to(ROOT))}

def copy_input(src,dst,expected):
    if V.sha(src)!=expected:raise ValueError('Source input hash changed: '+str(src))
    if dst.exists() and V.sha(dst)!=expected:raise ValueError('Existing local input changed: '+str(dst))
    dst.parent.mkdir(parents=True,exist_ok=True)
    if not dst.exists():shutil.copy2(src,dst)
    if V.sha(dst)!=expected:raise ValueError('Input copy failed')

def prepare(run,source=SOURCE):
    cfg=settings.config();tasks=[];inputs=[];warnings=[]
    for f in sorted((source/'manifests').glob('*.json')):
        m=V.load(f);V.report_set(m['reports']);key=f.stem
        for field in ('rubrics','routing'):
            old=Path(m[field]);dest=run/'inputs'/field/f.name
            copy_input(old,dest,m[field+'_sha256']);inputs.append({'path':str(dest.relative_to(run)),'sha256':m[field+'_sha256'],'source':str(old)})
            m[field]=str(dest)
        suite=V.load(m['rubrics']);routing=V.load(m['routing'])
        if suite['task_key']!=m['task_key'] or routing['task_key']!=m['task_key']:raise ValueError('Query identity mismatch')
        if routing['rubrics_sha256']!=m['rubrics_sha256']:raise ValueError('Routing/rubrics hash mismatch')
        V.unique(routing['items'],'id',[x['id'] for x in suite['pointwise']])
        routes=V.unique(routing['pairwise'],'id',[x['id'] for x in suite['pairwise']])
        for g in suite['pairwise']:
            if (routes[g['id']]['mode']=='graph_content') != (g['dimension'] not in ('D5','D6')):raise ValueError('Inconsistent PW routing')
        if not suite['full_query'].strip():raise ValueError('Empty Query')
        for r in m['reports']:
            old=Path(r['path']);dest=run/'inputs'/key/r['report_id']/'report.md'
            copy_input(old,dest,r['sha256']);inputs.append({'path':str(dest.relative_to(run)),'sha256':r['sha256'],'source':str(old)})
            r['path']=str(dest);body=dest.read_text()
            if not body.strip():raise ValueError('Empty report')
            if r['report_id']=='R4' and body.lstrip().startswith('# '):
                warnings.append({'task':m['task_key'],'report':'R4','kind':'original_H1_preserved','first_line':body.lstrip().splitlines()[0],'action':'No automatic title rewriting; frozen original preserved'})
        m['version']=cfg['version'];m['seed_dirs']=[]
        m['budget'].update(workers=cfg['workers'],local_stage_workers=cfg['local_stage_workers'],max_attempts=cfg['attempts'],ds_max_attempts=cfg['ds_attempts'])
        target=run/'manifests'/f.name;freeze(target,m)
        tasks.append({'key':key,'task_key':m['task_key'],'manifest':str(target),'sha256':V.sha(target),
                      'language':suite['language'],'pointwise':len(suite['pointwise']),'pairwise':len(suite['pairwise'])})
    if len(tasks)!=40:raise ValueError('Expected exactly 40 queries')
    counts={'queries':40,'reports':280,'graphs':280,'pt':sum(t['pointwise']*7 for t in tasks),'pairs':840,'pw':sum(t['pairwise']*42 for t in tasks)}
    if (counts['pt'],counts['pw'])!=(5432,13566):raise ValueError('Frozen rubric inventory changed')
    freeze(run/'batch.json',{'version':cfg['version'],'systems':settings.SYSTEMS,'tasks':tasks,'expected':counts,'runtime':cfg,'source':str(source),'inherited_model_results':0})
    freeze(run/'input_hashes.json',inputs);save(run/'input_warnings.json',warnings)
    save(run/'prepared.json',{'time':time.time(),'input_files':len(inputs),'counts':counts,'model_calls':0})
    return counts

def validate_inputs(run):
    batch=V.load(run/'batch.json')
    if batch['runtime']!=settings.config():raise ValueError('Runtime differs from prepared run; do not silently change attempt budgets')
    for f in V.load(run/'input_hashes.json'):
        if V.sha(run/f['path'])!=f['sha256']:raise ValueError('Frozen input changed: '+f['path'])
    for t in batch['tasks']:
        if V.sha(t['manifest'])!=t['sha256']:raise ValueError('Manifest changed: '+t['key'])
    return batch

def preflight(run):
    batch=validate_inputs(run);start=time.time()
    import pipeline
    revision=hashlib.sha256(json.dumps(code_inventory(),sort_keys=True).encode()).hexdigest()[:12]
    rows=[]
    for task in batch['tasks']:
        runner=pipeline.Runner(task['manifest'],run/'offline_preflight'/revision/task['key']);runner.preflight()
        rows.append({'task':task['key'],'reports':len(runner.reports),'units':sum(len(r['units']) for r in runner.reports)})
    report={'tasks':rows,'seconds':time.time()-start,'input_files':len(V.load(run/'input_hashes.json')),'model_calls':0,'external_code_dependencies':[]}
    for module in list(sys.modules.values()):
        file=getattr(module,'__file__',None)
        if file and file.endswith('.py') and ('iclrbench_runs' in file) and not Path(file).resolve().is_relative_to(ROOT):
            report['external_code_dependencies'].append(file)
    if report['external_code_dependencies']:raise ValueError('Unisolated code dependencies: '+str(report['external_code_dependencies']))
    save(run/'offline_preflight.json',report)
    return {'queries':len(rows),'reports':sum(r['reports'] for r in rows),'model_calls':0,'seconds':report['seconds']}

def check_snapshot(run):
    validate_inputs(run)
    if V.load(run/'code_lock.json')!=code_inventory():raise ValueError('Code/config changed after freeze; use a new revision, not an in-flight patch')

def worker(run,taskkey):
    check_snapshot(run);cfg=settings.config();batch=V.load(run/'batch.json');t=next(t for t in batch['tasks'] if t['key']==taskkey)
    from global_limits import Limits
    limits=Limits(run/'limits.sqlite',gpt=cfg['gpt_concurrency'],ds_rpm=cfg['deepseek_rpm'],ds_concurrency=cfg['deepseek_concurrency'],gpt_rpm=cfg['gpt_rpm'],gpt_tpm=cfg['gpt_tpm']);limits.install()
    import pipeline
    out=run/'tasks'/taskkey
    try:pipeline.Runner(t['manifest'],out).run()
    except Exception as ex:
        save(out/'worker_exception.json',{'error':str(ex),'time':time.time()})
    audit=V.inspect_task(V.load(t['manifest']),out);save(out/'completion_audit.json',V.compact(audit))
    return 0 if audit['framework_complete'] else 2

def watch(run):
    batch=V.load(run/'batch.json');totals={k:0 for k in ('graphs','pt','pw','pairs')};done=score_done=0;audits=[]
    for t in batch['tasks']:
        a=V.inspect_task(V.load(t['manifest']),run/'tasks'/t['key']);audits.append(V.compact(a))
        for k in totals:totals[k]+=a['counts'][k]
        done+=a['framework_complete'];score_done+=a['scoring_complete']
    result={'updated':time.time(),'counts':totals,'expected':batch['expected'],'queries_complete':done,'queries_scored':score_done,'queries':audits}
    save(run/'coverage.json',result)
    for k in totals:
        n,d=totals[k],batch['expected'][k];bar='█'*int(24*n/d)+'░'*(24-int(24*n/d));print(f'{k:7} [{bar}] {n}/{d}')
    print(f'Query complete {done}/40; scores present {score_done}/40; no fabricated replacements')
    return result

def supervise(run):
    run.mkdir(parents=True,exist_ok=True)
    with (run/'supervisor.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        validate_inputs(run);freeze(run/'code_lock.json',code_inventory());batch=V.load(run/'batch.json');cfg=settings.config()
        states={};mutex=threading.Lock()
        def persist():save(run/'status.json',{'supervisor_pid':os.getpid(),'updated':time.time(),'states':dict(states),'finished':False})
        def launch(t):
            key=t['key'];out=run/'tasks'/key
            if V.inspect_task(V.load(t['manifest']),out)['framework_complete']:
                with mutex:states[key]={'state':'complete_from_validated_cache'};persist()
                return
            (run/'logs').mkdir(exist_ok=True)
            with (run/'logs'/f'{key}.log').open('a') as log:
                p=subprocess.Popen([sys.executable,str(ROOT/'run.py'),'worker','--run',str(run),'--task',key,'--execute'],stdout=log,stderr=subprocess.STDOUT,cwd=ROOT)
                with mutex:states[key]={'state':'running','pid':p.pid,'started':time.time()};persist()
                try:code=p.wait(timeout=cfg['worker_timeout_seconds'])
                except subprocess.TimeoutExpired:
                    p.terminate()
                    try:p.wait(timeout=10)
                    except subprocess.TimeoutExpired:p.kill();p.wait()
                    code=124
                except BaseException:
                    p.terminate();p.wait(timeout=10);raise
            a=V.inspect_task(V.load(t['manifest']),out);save(out/'completion_audit.json',V.compact(a))
            with mutex:states[key]={'state':'complete' if a['framework_complete'] else 'incomplete','exit_code':code,'ended':time.time()};persist()
        # Resume passes do not reset per-call attempts. They recover interrupted work
        # and failed acquisition cards, never rerun outcomes to obtain a different winner.
        for passno in range(cfg.get('resume_passes',3)):
            with cf.ThreadPoolExecutor(max_workers=cfg['active_queries']) as pool:list(pool.map(launch,batch['tasks']))
            if all(s['state'].startswith('complete') for s in states.values()):break
        from aggregate import publish
        result=publish(run)
        save(run/'status.json',{'supervisor_pid':os.getpid(),'updated':time.time(),'finished':True,'states':states,'all_complete':result['framework_complete'],'aggregation_complete':result['system_table_complete']})
        return 0 if result['framework_complete'] else 2

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('command',choices=['prepare','preflight','freeze','run','worker','watch','aggregate']);parser.add_argument('--run',type=Path,default=DEFAULT);parser.add_argument('--source',type=Path,default=SOURCE);parser.add_argument('--execute',action='store_true');parser.add_argument('--task')
    a=parser.parse_args();run=a.run.resolve()
    if a.command in ('run','worker') and not a.execute:parser.error('Live model requests require --execute; use preflight for offline validation')
    if a.command=='prepare':print(json.dumps(prepare(run,a.source),ensure_ascii=False))
    elif a.command=='preflight':print(json.dumps(preflight(run),ensure_ascii=False))
    elif a.command=='freeze':validate_inputs(run);freeze(run/'code_lock.json',code_inventory());print('Code frozen; no model requests')
    elif a.command=='watch':watch(run)
    elif a.command=='worker':return worker(run,a.task)
    elif a.command=='run':return supervise(run)
    elif a.command=='aggregate':
        from aggregate import publish
        print(json.dumps(publish(run),ensure_ascii=False));return 0
    return 0

if __name__=='__main__':sys.exit(main())
