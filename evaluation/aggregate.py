"""Frozen paper aggregation, with portable I/O and no model calls."""
import collections,itertools,json,math
from types import SimpleNamespace
from pathlib import Path
import numpy as np
import completeness as V
import ordinal_model as O
E=SimpleNamespace(load=lambda p:json.loads(Path(p).read_text()),V=V,WEIGHTS=[30,30,10,10,20])
SIX=['D1','D2','D3','D4','D5','D6']
def serial(x):
    if isinstance(x,np.ndarray):return serial(x.tolist())
    if isinstance(x,np.generic):return serial(x.item())
    if isinstance(x,float) and not math.isfinite(x):return None
    if isinstance(x,dict):return {k:serial(v) for k,v in x.items()}
    if isinstance(x,(list,tuple)):return [serial(v) for v in x]
    return x

def combine(pt,pw):
    n=np.isfinite(pt).astype(int)+np.isfinite(pw).astype(int)
    six=np.divide(np.nan_to_num(pt)+np.nan_to_num(pw),n,out=np.full_like(pt,np.nan),where=n>0)
    five=np.concatenate([six[...,:4],np.nanmean(six[...,4:6],axis=-1)[...,None]],axis=-1)
    assert np.isfinite(five).all()
    return np.concatenate([five,(five@np.array(E.WEIGHTS)/100)[...,None]],axis=-1)

def collect(root,keys,ids):
    n=len(ids);pt=np.full((len(keys),n,6),np.nan);rawpw=np.full_like(pt,np.nan);obs=[[] for _ in SIX]
    stats=collections.Counter();diagnostics=collections.Counter()
    for q,t in enumerate(keys):
        m=E.load(root/'manifests'/f'{t}.json');suite=E.load(m['rubrics']);gm={g['id']:SIX.index(g['dimension']) for g in suite['pairwise']};base=root/'tasks'/t
        for i,rid in enumerate(ids):
            point=E.load(base/'pointwise'/rid/'result.json');E.V.point_rows(point,[p['id'] for p in suite['pointwise']]);rows=point['final']
            stats['pt']+=len(rows);stats['graphs']+=(base/'reports'/rid/'graph.json').exists()
            for d,dim in enumerate(SIX):
                vals=[(rows[g['id']]['score']-1)*25 for g in suite['pointwise'] if g['dimension']==dim]
                if vals:pt[q,i,d]=np.mean(vals)
        vals=[[[] for _ in SIX] for _ in ids]
        for i,j in itertools.combinations(range(n),2):
            pair=E.load(base/'pairs'/f'{ids[i]}_{ids[j]}'/'result.json');E.V.valid_pair(pair,list(gm),[ids[i],ids[j]]);orders=[];stats['pairs']+=1
            for order in ('AB','BA'):
                margins={}
                for row in pair[order]['judgments']:
                    y=0 if row['preferred_report_id']=='tie' else row['strength']*(1 if row['preferred_report_id']==ids[i] else -1)
                    d=gm[row['guide_id']];obs[d].append((q,i,j,y+2));vals[i][d].append(y);vals[j][d].append(-y);margins[row['guide_id']]=y;stats['pw']+=1
                orders.append(margins)
            for gid in gm:
                a,b=orders[0][gid],orders[1][gid];diagnostics['pairs_of_items']+=1
                diagnostics['direction_agree']+=int(np.sign(a)==np.sign(b));diagnostics['exact_agree']+=int(a==b)
                diagnostics['strict_reversal']+=int(a*b<0);diagnostics['tie_conflict']+=int((a==0)!=(b==0))
        for i in range(n):
            for d in range(6):
                if vals[i][d]:rawpw[q,i,d]=np.mean([(y+2)*25 for y in vals[i][d]])
    return pt,rawpw,[np.array(o,dtype=int).reshape(-1,4) for o in obs],dict(stats),dict(diagnostics)

def fit_matched(obs,n,qcount):
    # Inactive rows in the original 40-row fitter are independent and remain
    # zero under REG. Slice them off before computing any score or average.
    assert 1 <= qcount <= 40 and all(not len(o) or max(o[:,0])<qcount for o in obs)
    models=[O.fit(o,n=n) for o in obs];pw=O.full_pw(models,n)[:qcount]
    for d,o in enumerate(obs):
        active=set(o[:,0]) if len(o) else set()
        for q in range(qcount):
            if q not in active:pw[q,:,d]=np.nan
    return models,pw
