"""Portable offline paper replay. No API clients, secrets, or original run paths.

Levels: main table is refitted from criterion-level judgments; human metrics,
cross-judge diagnostics and sparse-entry summaries are recomputed from frozen
scores/predictions/trials. These are NOT reruns of the LLM evaluator.
"""
import argparse
import collections
import hashlib
import itertools
import json
import math
import os
from pathlib import Path
import re
import socket
import sys
import time

for key in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','VECLIB_MAXIMUM_THREADS'):
    os.environ.setdefault(key,'1')

def forbid_network(*args,**kwargs):
    raise RuntimeError('This reproduction package is offline-only.')

socket.socket=forbid_network
socket.create_connection=forbid_network
socket.getaddrinfo=forbid_network

import numpy as np
import scipy
from scipy.stats import spearmanr, kendalltau
import frozen_ordinal as O
import remaining_tables

ROOT=Path(__file__).resolve().parent
SIX=['D1','D2','D3','D4','D5','D6']
DIMS=['D1','D2','D3','D4','D5_D6']
WEIGHTS=np.array([30,30,10,10,20])
RESULTS={}
CHECKS=[]

def read(rel): return json.loads((ROOT/rel).read_text(encoding='utf-8'))

def check(name,ok,detail=None):
    CHECKS.append({'check':name,'passed':bool(ok),'detail':detail})
    if not ok: raise AssertionError((name,detail))

def verify_inputs():
    hashes=read('INPUT_HASHES.json')
    hashes.update(read('INPUT_HASHES.extra.json'))
    hashes.update(read('INPUT_HASHES.remaining.json'))
    hashes.update(read('INPUT_HASHES.confirmation.json'))
    hashes.update(read('INPUT_HASHES.selected.json'))
    for name,h in hashes.items():
        check('sha256:'+name,hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==h)

def paper_values(label,prefix,skip=1):
    block=next(t['latex'] for t in read('data/paper_tables.json') if t['label']==label)
    # Some appendix tables are physically on a single source line.
    lines=block.replace('\\\\','\n').splitlines()
    line=next(l for l in lines if re.search(re.escape(prefix)+r'\s*&',l))
    cells=line.split('&')[skip:]
    # TeX double hyphens delimit intervals; single minus signs carry direction.
    return [float(s) for c in cells for s in re.findall(r'(?<![A-Za-z0-9.])[-+]?(?:\d*\.\d+|\d+)',c.replace(',','').replace('--',' ').replace('−','-'))]

def paper_check(label,prefix,values,digits,skip=1):
    expected=paper_values(label,prefix,skip)
    if isinstance(digits,int):digits=[digits]*len(values)
    got=[float(f'{float(v):.{d}f}') for v,d in zip(values,digits)]
    check(label+':'+prefix,len(got)==len(expected) and np.allclose(got,expected,atol=1e-10,rtol=0),{'computed':got,'paper':expected})

def combine(pt,pw):
    n=np.isfinite(pt).astype(int)+np.isfinite(pw).astype(int)
    six=np.divide(np.nan_to_num(pt)+np.nan_to_num(pw),n,out=np.full_like(pt,np.nan),where=n>0)
    five=np.concatenate([six[...,:4],np.nanmean(six[...,4:6],axis=-1)[...,None]],axis=-1)
    check('five dimensions finite',np.isfinite(five).all())
    return np.concatenate([five,(five@WEIGHTS/100)[...,None]],axis=-1)

def benchmark():
    b=read('data/benchmark.json'); counts=collections.Counter(); dims=collections.Counter(); prov=collections.Counter()
    for q,r in b['rubrics'].items():
        counts[(q.split('_')[0],r['language'])]+=1
        for mode in ('pointwise','pairwise'):
            check('unique criterion ids:'+q+':'+mode,len({x['id'] for x in r[mode]})==len(r[mode]))
            for x in r[mode]:
                dim='D5_D6' if x['dimension'] in ('D5','D6') else x['dimension']
                dims[(mode,dim)]+=1;prov[x.get('provenance',{}).get('kind','unspecified')]+=1
    table={}
    for key,label in [('drb1','DRB-I'),('drb2','DRB-II'),('rr','ResearchRubrics')]:
        vals=[counts[key,'zh'],counts[key,'en']]; vals.append(sum(vals));table[label]=vals
    total=np.sum(list(table.values()),axis=0)
    # The current manuscript transposes the original source/language inventory.
    # Derive the added rows from the frozen report manifest and human-pair records.
    source_keys=['drb1','drb2','rr']
    reports=collections.Counter(r['query'].split('_')[0] for r in b['report_manifest'])
    pairs=collections.Counter(r['task'].split('_')[0] for r in read('data/human80.json')['rows'])
    inventory={
        'Chinese queries':[v[0] for v in table.values()]+[total[0]],
        'English queries':[v[1] for v in table.values()]+[total[1]],
        'All queries':[v[2] for v in table.values()]+[total[2]],
        r'Share of queries (\%)':[100*v[2]/total[2] for v in table.values()]+[100],
        'Collected reports':[reports[k] for k in source_keys]+[sum(reports.values())],
        'Human-annotated report pairs':[pairs[k] for k in source_keys]+[sum(pairs.values())],
    }
    for label,vals in inventory.items():paper_check('tab:benchmark_resources',label,vals,0)
    rubtable={}
    for dim,label in zip(DIMS,['Responsiveness','Evidence','Reasoning','Synthesis','Readability']):
        vals=[dims['pointwise',dim],dims['pairwise',dim]];vals.append(sum(vals));rubtable[label]=vals
        paper_check('tab:rubric_distribution',label,vals,0,skip=2)
    paper_check('tab:rubric_distribution','Total',np.sum(list(rubtable.values()),axis=0),0,skip=2)
    RESULTS['benchmark']={'task_distribution':table,'rubric_distribution':rubtable,'provenance_counts':dict(prov)}

def checked_fit(rows,n):
    """Enforce frozen-fit postconditions even when Python assertions are disabled."""
    model=O.fit(rows,n=n)
    if len(rows):
        if model is None or not model.get('success'):
            raise ValueError('Ordinal optimizer did not converge successfully.')
        theta=np.asarray(model['theta']);tau=np.asarray(model['tau'])
        if not np.isfinite(theta).all() or not np.isfinite(tau).all():
            raise ValueError('Ordinal fit contains non-finite parameters.')
        if np.max(np.abs(theta.mean(axis=1)))>=1e-6:
            raise ValueError('Ordinal fit is not centered.')
    return model

def main_scores():
    data=read('data/main_judgments.json'); b=read('data/benchmark.json'); qs=data['queries']; ids=data['systems']
    qi={q:i for i,q in enumerate(qs)}; ri={r:i for i,r in enumerate(ids)}
    buckets=collections.defaultdict(list); observations={d:[] for d in SIX}
    for q,r,g,d,s in data['pointwise']: buckets[(q,r,d)].append((s-1)*25)
    pt=np.full((40,9,6),np.nan)
    for (q,r,d),v in buckets.items():pt[qi[q],ri[r],SIX.index(d)]=np.mean(v)
    gids={q:{g['id']:g['dimension'] for g in b['rubrics'][q]['pairwise']} for q in qs}
    # Preserve the historical order: query, report pair, physical AB/BA, guide.
    for q,a,z,g,order,level in data['pairwise']:
        observations[gids[q][g]].append([qi[q],ri[a],ri[z],level+2])
    check('main observations equal frozen archive',observations==read('data/expected_observations.json'))
    models=[]
    for d in SIX:
        rows=np.array(observations[d],dtype=int).reshape(-1,4)
        models.append(checked_fit(rows,n=9))
        print('refit',d,'items',len(rows),flush=True)
    pw=O.full_pw(models,9)
    for di,d in enumerate(SIX):
        active={r[0] for r in observations[d]}
        for i in range(40):
            if i not in active:pw[i,:,di]=np.nan
    score=combine(pt,pw); expected=np.array(read('data/expected_main.json')['ordinal'])
    max_error=float(np.max(abs(score-expected)))
    check('main per-query score regression',max_error<1e-6,{'max_abs_error':max_error,'tolerance':1e-6})
    table=[]
    for i in np.argsort(-score.mean(0)[:,-1]):
        rid=ids[i];model,harness=b['systems'][rid]; v=score.mean(0)[i]
        paper_check('tab:system_results',model if model else '---',v,2,skip=2)
        table.append({'id':rid,'model':model,'harness':harness,'values':v.tolist()})
    RESULTS['main']={'table':table,'per_query':score.tolist(),'max_abs_error':max_error,
       'fit_diagnostics':[{k:v for k,v in m.items() if k not in ('theta','tau','categories')} if m else None for m in models]}

def metric(y,p,labels=('B','tie','A')):
    assert len(y)==len(p) and len(y)>0
    conf=np.zeros((len(labels),len(labels)),dtype=int)
    for a,b in zip(y,p):conf[labels.index(a),labels.index(b)]+=1
    n=int(conf.sum());correct=int(conf.trace());acc=correct/n
    chance=float(conf.sum(0)@conf.sum(1))/n**2
    f1=[2*conf[i,i]/(conf[i,:].sum()+conf[:,i].sum()) if conf[i,:].sum()+conf[:,i].sum() else 0 for i in range(len(labels))]
    return {'n':n,'correct':correct,'accuracy':acc,'kappa':(acc-chance)/(1-chance) if chance<1 else 1.0,
            'macro_f1':float(np.mean(f1)),'confusion':conf.tolist()}

def bootstrap(rows,values):
    tasks=sorted({r['task'] for r in rows}); rng=np.random.default_rng(20260923)
    draws=[]
    for source in ('drb1','drb2','rr'):
        indexes=[i for i,t in enumerate(tasks) if t.startswith(source+'_')]
        if indexes:draws.append(rng.choice(indexes,size=(10000,len(indexes))))
    ix=np.concatenate(draws,axis=1)
    num=np.array([sum(v for r,v in zip(rows,values) if r['task']==t) for t in tasks])
    den=np.array([sum(r['task']==t for r in rows) for t in tasks])
    return np.quantile(num[ix].sum(1)/den[ix].sum(1),[.025,.975])

def human():
    data=read('data/human80.json'); rows=data['rows']; check('human80 unique pairs',len(rows)==len({r['pair_id'] for r in rows})==80)
    results={}
    for m,expected in data['expected_metrics'].items():
        for r in rows:
            if m in data['scores']:
                sides=data['scores'][m][r['pair_id']]; totals={}
                for side in ('A','B'):
                    vals=sides[side]; keys=[d for d in DIMS if vals.get(d) is not None]
                    weights={d:WEIGHTS[DIMS.index(d)] for d in keys}
                    totals[side]=sum(vals[d]*weights[d] for d in keys)/sum(weights.values())
                delta=totals['A']-totals['B'];pred='tie' if abs(delta)<1 else ('A' if delta>0 else 'B')
                check('human score-to-preference:'+m+':'+r['pair_id'],pred==r['predictions'][m]['overall'])
        results[m]={}
        for field in expected:
            valid=[r for r in rows if field in r['predictions'][m]]
            if not valid:continue
            y=[r['human'][field] for r in valid];p=[r['predictions'][m][field] for r in valid]
            result=metric(y,p);result['ci95']=bootstrap(valid,[a==b for a,b in zip(y,p)]).tolist()
            for k in ('n','correct','accuracy','kappa','macro_f1'):
                check('human archive:'+m+':'+field+':'+k,abs(result[k]-expected[field][k])<1e-12)
            check('human CI:'+m+':'+field,np.allclose(result['ci95'],expected[field]['ci95'],atol=1e-12))
            results[m][field]=result
    for m,label in [('B0','Hybrid framework'),('D0','Direct'),('OPENRS','OpenRS'),('SOURCE','Source protocols')]:
        v=results[m]['overall'];paper_check('tab:human_agreement',label,[v['accuracy']*100,v['kappa'],v['macro_f1'],*[x*100 for x in v['ci95']]],[2,3,3,2,2])
    for m,label in [('B0','Full framework'),('A4','PT-only'),('A5','PW-only'),('A3','No verification scoring feedback'),('SUMMARY','Summary representation')]:
        v=results[m]['overall'];vals=[v['accuracy']*100,v['kappa'],v['macro_f1']];digits=[2,3,3]
        # Validate both magnitude and direction of the reported percentage-point change.
        if m!='B0':vals.append((v['accuracy']-results['B0']['overall']['accuracy'])*100);digits.append(2)
        paper_check('tab:ablations',label,vals,digits)
    RESULTS['human80']=results

def seven():
    src=read('data/seven_ordinal_source.json'); a=np.array(src['ordinal'])[:,:,:5]
    a=np.concatenate([a[...,:2],a[...,2:4].mean(-1)[...,None],a[...,4:5],(a@WEIGHTS/100)[...,None]],axis=-1)
    names={'R1':'OpenAI','R2':'Gemini','R3':'Claude','R4':'LongCat','R5':'Kimi','R6':'DuMate','R7':'Qwen'}
    out={r:a.mean(0)[i].tolist() for i,r in enumerate(src['systems'])}
    for r,v in out.items():paper_check('tab:initial_system_results',names[r],v,2)
    RESULTS['seven_system']=out
    return a.mean(0)

def usage():
    ledger=read('data/usage_ledger.json'); totals={};seen=set()
    for r in ledger['responses']:
        check('usage response unique:'+r['response_sha256'],r['response_sha256'] not in seen);seen.add(r['response_sha256'])
        d=totals.setdefault(r['model'],[0,0,0]);u=r['usage']
        d[0]+=not r['usage_missing'];d[1]+=u.get('input_tokens',0);d[2]+=u.get('output_tokens',0)
    for model,label in [('GPT-5.5','GPT-5.5'),('deepseek-v4.1-flash','DeepSeek-v4.1f')]:
        n,a,b=totals[model];paper_check('tab:token_usage',label,[n,a/1e6,b/1e6,(a+b)/1e6],[0,2,2,2])
    n,a,b=np.array(list(totals.values())).sum(0);paper_check('tab:token_usage','Total',[n,a/1e6,b/1e6,(a+b)/1e6],[0,2,2,2])
    check('unknown usage not zero-filled',ledger['unknown_request_count']==1422)
    RESULTS['usage']={'totals':totals,'unknown_requests':ledger['unknown_request_count']}

def stability(rows,ids):
    margins=collections.defaultdict(dict)
    for q,a,b,g,order,s in rows:
        key=(q,a,b,g);check('physical direction unique',order not in margins[key]);margins[key][order]=s
    c=collections.Counter();edges=collections.defaultdict(dict)
    for (q,a,b,g),v in margins.items():
        assert set(v)=={'AB','BA'};x,y=v['AB'],v['BA']
        c['order_matched_items']+=1;c['direction_agree']+=np.sign(x)==np.sign(y);c['strict_reversal']+=x*y<0
        edges[q,g][a,b]=int(np.sign(x+y))
    for edge in edges.values():
        def sign(a,b):return edge[a,b] if ids.index(a)<ids.index(b) else -edge[b,a]
        for a,b,z in itertools.combinations(ids,3):
            v=[sign(a,b),sign(b,z),sign(z,a)]
            if all(v):c['eligible_non_tied_triads']+=1;c['cycles']+=len(set(v))==1
    return {k:int(v) for k,v in c.items()}

def icc(x,y):
    a=np.column_stack([np.ravel(x),np.ravel(y)]); n,k=a.shape; grand=a.mean()
    msr=k*np.sum((a.mean(1)-grand)**2)/(n-1);msc=n*np.sum((a.mean(0)-grand)**2)/(k-1)
    mse=np.sum((a-a.mean(1)[:,None]-a.mean(0)[None,:]+grand)**2)/((n-1)*(k-1))
    return (msr-mse)/(msr+(k-1)*mse+k*(msc-mse)/n)

def judges():
    d=read('data/cross_judge.json'); ids=d['systems']; qs=d['queries']; totals={};out={}
    for judge,data in d['scores'].items():
        totals[judge]=np.array([[data[q][r]['total'] for r in ids] for q in qs])
        six=np.array([[data[q][r]['six_dimensions'] for r in ids] for q in qs])
        recon=six[:,:,:4]@np.array([.3,.3,.1,.1])+six[:,:,4:6].mean(-1)*.2
        check('cross total from dimensions:'+judge,np.allclose(recon,totals[judge],atol=1e-10))
    x=totals['gpt55_historical']
    for judge,label in [('gpt55_historical','GPT-5.5'),('deepseek_on','DeepSeek-v4.1f'),('gemini25','Gemini 2.5 Pro')]:
        s=stability(d['pairs'][judge],ids); exp=d['expected_stability'][judge]
        check('cross stability archive:'+judge,all(s[k]==exp[k] for k in s))
        order=100*s['direction_agree']/s['order_matched_items'];rev=100*s['strict_reversal']/s['order_matched_items'];cyc=100*s['cycles']/s['eligible_non_tied_triads']
        vals=[order,rev];digits=[2,2];cross=None
        if judge!='gpt55_historical':
            y=totals[judge];rho=float(spearmanr(x.mean(0),y.mean(0)).statistic)
            cross=[float(icc(x,y)),rho,float(kendalltau(x.mean(0),y.mean(0)).statistic),float(np.mean([spearmanr(a,b).statistic for a,b in zip(x,y)])),float((y-x).mean())]
            paper_check('tab:cross-judge-robustness',label,cross,3)
            vals.append(rho);digits.append(3)
        paper_check('tab:judge-selection',label,vals,digits)
        paper_check('tab:judge-stability',label+' (Primary)' if judge=='gpt55_historical' else label,[order,rev,cyc],2)
        out[judge]={'counts':s,'cross':cross}
    RESULTS['judges']=out

def sparse():
    base=seven(); trials=read('data/sparse_trials.json'); seen=set();out={}
    check('sparse completed trial count',len(trials)==4200)
    for v in trials:
        key=tuple(v[k] for k in ('held','k','trial','method'));check('sparse unique trial',key not in seen);seen.add(key)
    for method in ('ipw','unweighted'):
        out[method]={}
        for k in (1,2,3):
            rows=[v for v in trials if v['method']==method and v['k']==k]; check('sparse group count',len(rows)==700)
            errors=[];ranks=[];savings=[]
            for r in rows:
                a=np.array(r['means']);h=r['held'];errors.append(abs(a[h,-1]-base[h,-1]))
                rank=int(1+np.sum(a[:,-1]>a[h,-1]+1e-10));full=int(1+np.sum(base[:,-1]>base[h,-1]+1e-10))
                check('sparse recorded rank',rank==r['new_rank'] and full==r['full_rank']);ranks.append(rank==full)
                cost=sum(r['cost'].get(m+'_'+f,0) for m in ('gpt','ds') for f in ('input','output'))
                savings.append(1-cost/r['full_tokens'])
            row=[k,40*k,100*float(np.mean(savings)),float(np.mean(errors)),float(np.quantile(errors,.95)),100*float(np.mean(ranks))]
            out[method][str(k)]=row
            if method=='ipw':paper_check('tab:new_system_sampling',str(k),row[1:],[0,2,3,3,2])
    paper_check('tab:new_system_sampling','6 (full)',[240,0,0,0,100],[0,0,0,0,0])
    RESULTS['sparse']=out

def pilot():
    data=read('data/pilot_items.json');models=['gpt55','deepseek41_flash_max','gemini25'];out={}
    def values(items,key):return [x['value'] for x in items[key].values()]
    metric_keys={'PW repeat: direction':['pw_repeat_direction'], 'PW repeat: exact level':['pw_repeat_exact'],
      'PW order: direction':['swap_direction_r1','swap_direction_r2'], 'PT repeat: exact score':['pt_repeat_exact'],
      'Content PW order: direction':['swap_direction_r1_content','swap_direction_r2_content'],
      'Readability PW order: direction':['swap_direction_r1_readability','swap_direction_r2_readability']}
    count_values=[]
    for model in models:count_values.extend([data['request_counts'][model]['completed'],data['request_counts'][model]['expected']])
    paper_check('tab:judge_pilot','Valid requests',count_values,0)
    for label,keys in metric_keys.items():
        results=[];denoms=[]
        for m in models:
            vals=[v for k in keys for v in values(data['items'][m],k)]
            results.append(100*float(np.mean(vals)));denoms.append(len(vals))
        paper_check('tab:judge_pilot',label,results,2)
        out[label]={'percent':results,'denominators':denoms}
    RESULTS['pilot']=out

def convert(x):
    if isinstance(x,np.generic):return x.item()
    if isinstance(x,np.ndarray):return x.tolist()
    raise TypeError(type(x))

def diagnostic_json(value):
    """Keep non-finite failure diagnostics readable in strict JSON."""
    if isinstance(value,np.ndarray):return diagnostic_json(value.tolist())
    if isinstance(value,np.generic):return diagnostic_json(value.item())
    if isinstance(value,float) and not math.isfinite(value):
        return {'nonfinite': 'NaN' if math.isnan(value) else ('Infinity' if value>0 else '-Infinity')}
    if isinstance(value,dict):return {k:diagnostic_json(v) for k,v in value.items()}
    if isinstance(value,(list,tuple)):return [diagnostic_json(v) for v in value]
    return value

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--output',type=Path,required=True)
    ap.add_argument('--skip-refit',action='store_true',help='Diagnostics only; does NOT mark the main table reproduced.')
    args=ap.parse_args(); output=args.output.resolve()
    if output.exists():raise SystemExit('Choose a NEW output directory; previous outputs are never overwritten.')
    output.mkdir(parents=True)
    started=time.monotonic();status='passed'; error=None
    try:
        verify_inputs();benchmark();human();usage();judges();pilot();sparse()
        remaining_tables.run(sys.modules[__name__])
        if not args.skip_refit:main_scores()
        verify_inputs()
    except Exception as e:
        status='failed';error=repr(e)
        import traceback;traceback.print_exc()
    table_statuses=remaining_tables.table_statuses(sys.modules[__name__]) if status=='passed' else {}
    audit={'status':status,'error':error,'seconds':time.monotonic()-started,'checks':CHECKS,
           'table_statuses':table_statuses,'numerically_reproduced_tables':len(table_statuses),
           'archival_provenance_tables':sum(s=='reproduced_from_archived_inputs' for s in table_statuses.values()),
           'author_attested_label_tables':sum(s=='reproduced_with_author_attested_labels' for s in table_statuses.values()),
           'all_paper_tables_fully_verified':False,
           'author_confirmation_accepted':'controlled_reproduction' in RESULTS,
           'qualification':'Offline numerical reproduction using the author-confirmed matching labels; not a new annotation or model study.',
           'passed_checks':sum(x['passed'] for x in CHECKS),'failed_checks':sum(not x['passed'] for x in CHECKS),
           'network':'Python socket access disabled; no external processes or API clients invoked',
           'model_calls':0,'python':sys.version,'numpy':np.__version__,'scipy':scipy.__version__,
           'main_refit_performed':not args.skip_refit and 'main' in RESULTS,
           'scope':'Offline recomputation from archived judgments/scores/trials; not end-to-end model regeneration.'}
    try:
        result_text=json.dumps(RESULTS,ensure_ascii=False,indent=2,default=convert,allow_nan=False)+'\n'
    except (ValueError,TypeError) as e:
        status='failed';audit.update(status='failed',error=repr(e),table_statuses={},numerically_reproduced_tables=0,archival_provenance_tables=0,author_attested_label_tables=0)
        result_text=json.dumps(diagnostic_json(RESULTS),ensure_ascii=False,indent=2,allow_nan=False)+'\n'
    (output/'RESULTS.json').write_text(result_text,encoding='utf-8')
    audit=diagnostic_json(audit)
    (output/'AUDIT.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8')
    print(json.dumps({k:v for k,v in audit.items() if k!='checks'},ensure_ascii=True,allow_nan=False),flush=True)
    if status!='passed':raise SystemExit(1)

if __name__=='__main__':main()
