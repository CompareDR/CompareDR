"""Paper's frozen five-category ordinal model, generalized only in system count.

Functions objective/fit/thresholds/probs/expect/terms retain the original
ordinal_pairwise_gpt55_20260923_v1/run.py definitions and REG=.002.
"""
import numpy as np
from scipy.optimize import minimize
from scipy.special import expit
REG=.002

def thresholds(x):
    a=np.exp(x[0]);gap=np.exp(x[1]);b=a+gap
    return np.array([-b,-a,a,b]),a,gap

def probs(delta,tau):
    c=expit(tau-np.asarray(delta)[...,None])
    return np.diff(np.concatenate([np.zeros_like(c[...,:1]),c,np.ones_like(c[...,:1])],axis=-1),axis=-1)

def expect(delta,tau):return probs(delta,tau)@np.arange(-2,3)

def terms(delta,y,tau):
    c=expit(tau[None,:]-delta[:,None]);f=c*(1-c)
    cc=np.concatenate([np.zeros((len(y),1)),c,np.ones((len(y),1))],axis=1)
    ff=np.concatenate([np.zeros((len(y),1)),f,np.zeros((len(y),1))],axis=1)
    ix=np.arange(len(y));lo=cc[ix,y];hi=cc[ix,y+1]
    fl=ff[ix,y];fu=ff[ix,y+1];p=np.maximum(hi-lo,1e-15)
    gd=(fu-fl)/p
    hd=((fu-fl)/p)**2-(fu*(1-2*hi)-fl*(1-2*lo))/p
    return p,gd,hd,fl,fu

def objective(x,data,n):
    q,i,j,y=data.T;nt=40*n;theta=x[:nt].reshape(40,n)
    tau,a,gap=thresholds(x[nt:]);weights=1/np.bincount(q,minlength=40)[q]
    p,gd,_,fl,fu=terms(theta[q,i]-theta[q,j],y,tau)
    value=-np.sum(weights*np.log(p))+.5*REG*np.sum(theta**2)
    g=REG*theta.copy();np.add.at(g,(q,i),weights*gd);np.add.at(g,(q,j),-weights*gd)
    gt=np.zeros(4)
    for k in range(4):
        gt[k]=np.sum(weights*np.where(y==k+1,fl/p,0))-np.sum(weights*np.where(y==k,fu/p,0))
    da=gt@np.array([-1,-1,1,1]);dg=-gt[0]+gt[3]
    return value,np.r_[g.ravel(),da*a,dg*gap]

def fit(data,n=7):
    if not len(data):return None
    x=np.r_[np.zeros(40*n),np.log([.35,1.05])]
    res=minimize(objective,x,args=(data,n),jac=True,method='L-BFGS-B',
                 bounds=[(-20,20)]*(40*n)+[(-6,4)]*2,
                 options={'maxiter':1500,'ftol':1e-12,'gtol':1e-7,'maxls':40})
    theta=res.x[:40*n].reshape(40,n);tau,_,_=thresholds(res.x[40*n:])
    assert res.success,(res.message,res.fun)
    assert np.max(np.abs(theta.mean(axis=1)))<1e-6
    return {'theta':theta,'tau':tau,'success':bool(res.success),'iterations':res.nit,
            'loss':res.fun,'max_gradient':np.max(np.abs(res.jac)),
            'at_bound':bool(np.max(np.abs(theta))>19.99 or np.any(np.abs(res.x[-2:]-np.clip(res.x[-2:],-5.999,3.999))>0)),
            'categories':np.bincount(data[:,3],minlength=5)}

def full_pw(models,n):
    out=np.full((40,n,6),np.nan)
    for d,m in enumerate(models):
        if m is None:continue
        theta=np.asarray(m['theta']);em=expect(theta[:,:,None]-theta[:,None,:],np.asarray(m['tau']))
        out[:,:,d]=50+25*em.sum(axis=2)/(n-1)
    return out
