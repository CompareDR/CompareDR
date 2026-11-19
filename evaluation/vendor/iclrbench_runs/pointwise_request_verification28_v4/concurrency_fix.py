"""Per-key source single-flight and lossless explanation normalization."""
import threading
_guard=threading.Lock();_locks={}
def singleflight(fn):
 def wrapped(key,*args,**kwargs):
  identity=(fn.__module__,fn.__name__,str(key),repr(sorted(kwargs.items())))
  with _guard:lock=_locks.setdefault(identity,threading.Lock())
  with lock:return fn(key,*args,**kwargs)
 return wrapped

def normalize_explanations(out):
 for branch in ('fact','citation'):
  if branch not in out:continue
  for k in ('supports','limits'):
   value=out[branch].get(k)
   if isinstance(value,list) and all(isinstance(x,str) for x in value):out[branch][k]='\n'.join(value)
 return out

def install(v2):
 v2.old.retrieval.fetch=singleflight(v2.old.retrieval.fetch)
 v2.old.retrieval.search=singleflight(v2.old.retrieval.search)
 original=v2.follow_valid
 def validator(out,data):return original(normalize_explanations(out),data)
 v2.follow_valid=validator
 v2.FOLLOW+=' supports and limits must each be a string, not an array. task_effect must explain impact rather than noop.'
