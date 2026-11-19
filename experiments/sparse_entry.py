"""Refit the sparse new-system entry study from frozen, report-bound judgments."""
import os
for k in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','VECLIB_MAXIMUM_THREADS'):os.environ.setdefault(k,'1')
import argparse,json
from pathlib import Path
import numpy as np
import sparse_math as S

ROOT=Path(__file__).resolve().parents[1]
def read(p):return json.loads((ROOT/p).read_text())
def main():
    if not __debug__:raise RuntimeError('Do not disable validation with optimized Python')
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--out',type=Path,required=True)
    ap.add_argument('--held',type=int,choices=range(7),default=0,help='zero-based held-system index')
    ap.add_argument('--opponents',type=int,choices=(1,2,3),default=2)
    ap.add_argument('--trial',type=int,choices=range(100),default=0)
    ap.add_argument('--method',choices=('ipw','unweighted'),default='ipw')
    ap.add_argument('--all',action='store_true',help='refit all 4200 configurations; CPU-intensive')
    a=ap.parse_args();a.out.mkdir(parents=True,exist_ok=False)
    data=read('data/results/studies7_judgments.json');ids=data['systems']
    init=read('data/results/sparse_initialization.json')
    designs=read('reproduction/offline/data/opponent_sampling.json')
    archived=read('reproduction/offline/data/sparse_trials.json')
    lookup={(x['held'],x['k'],x['trial'],x['method']):x for x in archived}
    pt=np.array(data['pointwise_dimensions_0_100'],float)
    obs=[np.array(x,dtype=int).reshape(-1,4) for x in data['pairwise_by_dimension']]
    full=S.scores(init['full_models'],pt,obs);S.init(obs,pt,init['reference_models'],full)
    combinations=((h,k,t,m) for h in range(7) for k in (1,2,3) for t in range(100) for m in ('ipw','unweighted')) if a.all else [(a.held,a.opponents,a.trial,a.method)]
    results=[]
    for h,k,t,m in combinations:
        d=designs[h];mask=np.zeros((40,7),bool)
        for q,js in enumerate(d['sampling'][str(k)][t]):
            mask[q,[ids.index(d['reference_systems'][j]) for j in js]]=True
        if mask[:,h].any() or not np.all(mask.sum(axis=1)==k):raise ValueError('Invalid opponent design')
        # An explicit information boundary: changes to unselected labels cannot affect selected inputs.
        for o in obs:
            if not len(o):continue
            dat,w=S.select(o,h,mask,m);changed=o.copy()
            new=(o[:,1]==h)|(o[:,2]==h);other=np.where(o[:,1]==h,o[:,2],o[:,1])
            hidden=new & ~mask[o[:,0],other];changed[hidden,3]=4-changed[hidden,3]
            dd,ww=S.select(changed,h,mask,m)
            if not np.array_equal(dat,dd) or not np.array_equal(w,ww):raise ValueError('Hidden outcome leakage')
        result=S.job((h,k,t,m,mask))
        if not result['success']:raise RuntimeError('Numerical fit failed: '+str((h,k,t,m)))
        error=float(np.max(abs(np.array(result['means'])-lookup[h,k,t,m]['means'])))
        # Match the original optimizer-regression tolerance (1e-3 score points).
        # Repeated L-BFGS fits can differ slightly across BLAS/library builds.
        if error>1e-3:raise ValueError('Archived trial mismatch: '+str(error))
        result.update(cost=lookup[h,k,t,m]['cost'],full_tokens=lookup[h,k,t,m]['full_tokens'],archived_max_error=error)
        def convert(v):return v.tolist() if isinstance(v,np.ndarray) else v.item() if isinstance(v,np.generic) else v
        (a.out/f'{m}_R{h+1}_k{k}_{t:03}.json').write_text(json.dumps(result,default=convert,allow_nan=False,indent=2)+'\n')
        results.append(error)
    summary={'trials_refitted':len(results),'max_error':max(results),'regression_tolerance':1e-3,'hidden_outcomes_excluded':True,'api_calls':0}
    (a.out/'AUDIT.json').write_text(json.dumps(summary,indent=2)+'\n');print(summary)

if __name__=='__main__':main()
