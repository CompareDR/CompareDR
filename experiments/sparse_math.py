"""Original sparse-entry numerical functions; offline only."""
import itertools,traceback
import numpy as np
from scipy.optimize import minimize
from scipy.stats import kendalltau
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'evaluation'))
import ordinal_model as O
from aggregate import combine
O.combine=combine
G={}
WEIGHTS=np.array([.3,.3,.1,.1,.2])
def display(a):
    v=np.asarray(a)[...,:5]
    return np.concatenate([v[...,:2],v[...,2:4].mean(axis=-1)[...,None],v[...,4:5],(v@WEIGHTS)[...,None]],axis=-1)

def vector(m,n=7,refs=None):
    t=np.zeros((40,n))
    if refs is None:t[:]=m['theta']
    else:t[:,refs]=m['theta']
    tau=m['tau'];return np.r_[t.ravel(),np.log([tau[2],tau[3]-tau[2]])]

def select(o,held,mask,method):
    q,i,j,y=o.T;new=(i==held)|(j==held);other=np.where(i==held,j,i)
    keep=(~new)|mask[q,other]
    data=o[keep];inc=new[keep]
    if method=='ipw':
        k=mask.sum(axis=1);w=np.where(inc,6/k[data[:,0]],1)/np.bincount(q,minlength=40)[data[:,0]]
    else:w=1/np.bincount(data[:,0],minlength=40)[data[:,0]]
    return data,w

def objective(x,data,w,n=7):
    q,i,j,y=data.T;nt=40*n;theta=x[:nt].reshape(40,n)
    tau,a,gap=O.thresholds(x[nt:]);p,gd,_,fl,fu=O.terms(theta[q,i]-theta[q,j],y,tau)
    value=-np.sum(w*np.log(p))+.5*O.REG*np.sum(theta**2)
    g=O.REG*theta.ravel()+np.bincount(q*n+i,w*gd,minlength=nt)-np.bincount(q*n+j,w*gd,minlength=nt)
    gt=np.bincount(y,weights=-w*fu/p,minlength=5)[:4]+np.bincount(y,weights=w*fl/p,minlength=5)[1:]
    return value,np.r_[g,(gt@np.array([-1,-1,1,1]))*a,(-gt[0]+gt[3])*gap]

def fit(data,w,x):
    r=minimize(objective,x,args=(data,w),jac=True,method='L-BFGS-B',bounds=[(-20,20)]*280+[(-6,4)]*2,
       options={'maxiter':1500,'ftol':1e-12,'gtol':1e-7,'maxls':40})
    tau,_,_=O.thresholds(r.x[280:]);theta=r.x[:280].reshape(40,7)
    return {'theta':theta,'tau':tau,'success':bool(r.success),'message':str(r.message),'iterations':r.nit,
      'loss':r.fun,'max_gradient':abs(r.jac).max(),'center_error':abs(theta.mean(axis=1)).max(),
      'at_bound':bool(abs(theta).max()>19.99 or np.any(r.x[280:]<=-5.999) or np.any(r.x[280:]>=3.999))}

def scores(models,pt,obs):
    pw=np.full_like(pt,np.nan)
    for d,m in enumerate(models):
        if m is None:continue
        t=np.asarray(m['theta']);n=t.shape[1]
        pw[:,:,d]=50+25*O.expect(t[:,:,None]-t[:,None,:],m['tau']).sum(axis=2)/(n-1)
        inactive=np.bincount(obs[d][:,0],minlength=40)==0;pw[inactive,:,d]=np.nan
    return display(O.combine(pt,pw))

def ranks(a):return 1+(a[None,:]>a[:,None]+1e-10).sum(axis=1)

def relations(a,b,ids):
    flips=ties=eligible=0;far_flips=far_n=0
    for i,j in itertools.combinations(ids,2):
        x=a[i]-a[j];y=b[i]-b[j]
        if abs(y)<=1e-10:ties+=1;continue
        eligible+=1;flips+=int(x*y < -1e-10)
        if abs(y)>=1:far_n+=1;far_flips+=int(x*y < -1e-10)
    return {'flips':flips,'eligible':eligible,'reference_ties':ties,'rate':flips/eligible if eligible else None,
      'gap1_flips':far_flips,'gap1_pairs':far_n,'gap1_rate':far_flips/far_n if far_n else None,
      'estimated_ties':sum(abs(a[i]-a[j])<=1e-10 for i,j in itertools.combinations(ids,2))}

def init(obs,pt,refs,full):G.update(obs=obs,pt=pt,refs=refs,full=full)

def job(args):
    held,k,r,method,mask=args;models=[]
    try:
        ix=[i for i in range(7) if i!=held]
        for d,o in enumerate(G['obs']):
            if not len(o):models.append(None);continue
            data,w=select(o,held,mask,method)
            models.append(fit(data,w,vector(G['refs'][held][d],refs=ix)))
        ok=all(m is None or (m['success'] and m['center_error']<1e-6) for m in models)
        diag=[None if m is None else {key:val for key,val in m.items() if key!='theta'} for m in models]
        if not ok:return {'held':held,'k':k,'trial':r,'method':method,'success':False,'fits':diag}
        s=scores(models,G['pt'],G['obs']);mean=s.mean(axis=0);f=G['full'].mean(axis=0);err=mean-f
        ref=relations(mean[:,-1],f[:,-1],ix);tau=kendalltau(mean[:,-1],f[:,-1]).statistic
        return {'held':held,'k':k,'trial':r,'method':method,'success':True,'means':mean,'per_query':s,
         'error':err,'new_error':err[held],'old_mae':abs(err[ix]).mean(axis=0),'old_max':abs(err[ix]).max(axis=0),
         'query_mae':abs(s-G['full']).mean(axis=0),'old_relations':ref,
         'new_rank':int(ranks(mean[:,-1])[held]),'full_rank':int(ranks(f[:,-1])[held]),
         'kendall':float(tau) if np.isfinite(tau) else None,'fits':diag,
         'pair_gap_mae':float(np.mean([abs((mean[i,-1]-mean[j,-1])-(f[i,-1]-f[j,-1])) for i,j in itertools.combinations(range(7),2)]))}
    except Exception:return {'held':held,'k':k,'trial':r,'method':method,'success':False,'exception':traceback.format_exc()}

def stats(a):
    a=np.asarray(a);return {'mean':a.mean(axis=0),'p025':np.quantile(a,.025,axis=0),'p95':np.quantile(a,.95,axis=0),'p975':np.quantile(a,.975,axis=0),'max':a.max(axis=0)}

def totalcost(c):return sum(c.get(m+'_'+f,0) for m in ('gpt','ds') for f in ('input','output'))
