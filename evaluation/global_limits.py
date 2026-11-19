"""Cross-process HTTP limits. Applied to every real model request including retries."""
import contextlib,json,os,sqlite3,time,uuid,urllib.request
from pathlib import Path

class Limits:
 def __init__(self,path,gpt=50,ds_rpm=300,ds_concurrency=60,gpt_rpm=50,gpt_tpm=None):
  self.path=str(path);self.gpt=gpt;self.rpm=ds_rpm;self.gpt_rpm=gpt_rpm;self.gpt_tpm=gpt_tpm
  Path(path).parent.mkdir(parents=True,exist_ok=True)
  with self.db() as c:
   c.execute('CREATE TABLE IF NOT EXISTS leases (id TEXT PRIMARY KEY, model TEXT, pid INTEGER, started REAL)')
   c.execute('CREATE TABLE IF NOT EXISTS requests (model TEXT, started REAL)')
   if 'tokens' not in [x[1] for x in c.execute('PRAGMA table_info(requests)')]:c.execute('ALTER TABLE requests ADD COLUMN tokens INTEGER DEFAULT 0')
   c.execute('CREATE INDEX IF NOT EXISTS requests_model_time ON requests(model,started)')
   c.execute('CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value INTEGER)')
   c.execute('INSERT OR IGNORE INTO settings VALUES(?,?)',('deepseek_concurrency',ds_concurrency))
   c.execute('INSERT OR IGNORE INTO settings VALUES(?,?)',('deepseek_rpm',ds_rpm))
   c.execute('INSERT OR IGNORE INTO settings VALUES(?,?)',('deepseek_cooldown_until',0))
   c.execute('INSERT OR IGNORE INTO settings VALUES(?,?)',('deepseek_last_backoff',0))
   c.execute('CREATE TABLE IF NOT EXISTS rate_errors (started REAL, status INTEGER, pid INTEGER)')
   c.execute('CREATE INDEX IF NOT EXISTS rate_errors_time ON rate_errors(started)')
   c.execute('CREATE TABLE IF NOT EXISTS rate_backoffs (started REAL, errors INTEGER, requests INTEGER, old_rpm INTEGER, new_rpm INTEGER)')
   c.execute('CREATE TABLE IF NOT EXISTS gpt_rate_errors (started REAL, status INTEGER, pid INTEGER)')
   c.execute('INSERT OR IGNORE INTO settings VALUES(?,?)',('gpt_rpm',gpt_rpm))
 @contextlib.contextmanager
 def db(self):
  c=sqlite3.connect(self.path,timeout=30)
  try:
   with c:yield c
  finally:c.close()
 def acquire(self,model,tokens=0):
  if model=='gpt' and self.gpt_tpm and tokens>self.gpt_tpm:raise ValueError('Single request reservation exceeds configured GPT TPM; adjust quota/config before launch')
  while True:
   now=time.time();ok=False;key=uuid.uuid4().hex
   with self.db() as c:
    c.execute('BEGIN IMMEDIATE')
    halt=c.execute("SELECT value FROM settings WHERE key='authorization_halt'").fetchone()
    if halt and halt[0]:raise RuntimeError('Model gateway authorization failed; batch halted. Confirm credentials/permission before explicit resume.')
    for (p,) in c.execute('SELECT DISTINCT pid FROM leases').fetchall():
     try:os.kill(p,0)
     except ProcessLookupError:c.execute('DELETE FROM leases WHERE pid=?',(p,))
    active=c.execute('SELECT count(*) FROM leases WHERE model=?',(model,)).fetchone()[0]
    if model=='gpt':
     count,last,used=c.execute('SELECT count(*),max(started),coalesce(sum(tokens),0) FROM requests WHERE model=? AND started>?',(model,now-60)).fetchone()
     rate=min(self.gpt_rpm,c.execute("SELECT value FROM settings WHERE key='gpt_rpm'").fetchone()[0])
     ok=active<self.gpt and count<rate and (last is None or now-last>=60/rate) and (self.gpt_tpm is None or used+tokens<=self.gpt_tpm)
    else:
     count,last=c.execute('SELECT count(*),max(started) FROM requests WHERE model=? AND started>?',(model,now-60)).fetchone()
     cap=c.execute("SELECT value FROM settings WHERE key='deepseek_concurrency'").fetchone()[0]
     rate=min(self.rpm,c.execute("SELECT value FROM settings WHERE key='deepseek_rpm'").fetchone()[0])
     cooldown=c.execute("SELECT value FROM settings WHERE key='deepseek_cooldown_until'").fetchone()[0]
     ok=now>=cooldown and count<rate and (last is None or now-last>=60/rate) and active<cap
    if ok:
     c.execute('INSERT INTO leases VALUES(?,?,?,?)',(key,model,os.getpid(),now));c.execute('INSERT INTO requests(model,started,tokens) VALUES(?,?,?)',(model,now,tokens))
   if ok:return key
   time.sleep(.03)
 def release(self,key):
  with self.db() as c:c.execute('DELETE FROM leases WHERE id=?',(key,))
 def backoff(self):
  now=time.time()
  with self.db() as c:
   c.execute('BEGIN IMMEDIATE')
   c.execute('INSERT INTO rate_errors VALUES(?,?,?)',(now,429,os.getpid()))
   errors=c.execute('SELECT count(*) FROM rate_errors WHERE status=429 AND started>?',(now-60,)).fetchone()[0]
   requests=c.execute("SELECT count(*) FROM requests WHERE model='deepseek' AND started>?",(now-60,)).fetchone()[0]
   # Fixed pacing per latest user instruction. Errors remain observable and
   # consume the existing bounded per-request retries; never change global RPM.
   burst=errors>=10 and errors/max(1,requests)>=0.05
   return {'errors_60s':errors,'requests_60s':requests,'burst':burst,'backoff_applied':False}
 def gpt_backoff(self):
  now=time.time()
  with self.db() as c:
   c.execute('BEGIN IMMEDIATE')
   c.execute('INSERT INTO gpt_rate_errors VALUES(?,?,?)',(now,429,os.getpid()))
   n=c.execute('SELECT count(*) FROM gpt_rate_errors WHERE started>?',(now-60,)).fetchone()[0]
   requests=c.execute("SELECT count(*) FROM requests WHERE model='gpt' AND started>?",(now-60,)).fetchone()[0]
   old=c.execute("SELECT value FROM settings WHERE key='gpt_rpm'").fetchone()[0]
   if old>15 and n>=3 and n/max(1,requests)>=0.1:
    new=max(15,old//2)
    c.execute("UPDATE settings SET value=? WHERE key='gpt_rpm'",(new,))
    c.execute('INSERT INTO rate_backoffs VALUES(?,?,?,?,?)',(now,n,requests,old,new))
 def install(self):
  original=urllib.request.OpenerDirector.open;limiter=self
  class Response:
   def __init__(self,response,key):self.response=response;self.key=key
   def __getattr__(self,k):return getattr(self.response,k)
   def __enter__(self):return self
   def close(self):
    try:self.response.close()
    finally:
     if self.key:limiter.release(self.key);self.key=None
   def __exit__(self,*args):self.close()
  def opened(opener,request,*args,**kwargs):
   body=getattr(request,'data',None);model=None
   if body:
    try:
     name=json.loads(body).get('model','')
     if 'gpt-5.5' in name or 'gpt-5.6-sol' in name:model='gpt'
     elif 'deepseek' in name:model='deepseek'
    except (ValueError,TypeError,AttributeError):pass
   if not model:return original(opener,request,*args,**kwargs)
   obj=json.loads(body);reserved=len(body)+obj.get('max_tokens',obj.get('max_completion_tokens',0))
   key=limiter.acquire(model,reserved)
   try:return Response(original(opener,request,*args,**kwargs),key)
   except BaseException as ex:
    limiter.release(key)
    if model=='deepseek' and getattr(ex,'code',None)==429:limiter.backoff()
    if model=='gpt' and getattr(ex,'code',None)==429:limiter.gpt_backoff()
    if getattr(ex,'code',None) in (401,403):
     with limiter.db() as db:db.execute('INSERT OR REPLACE INTO settings VALUES(?,?)',('authorization_halt',getattr(ex,'code')))
    raise
  urllib.request.OpenerDirector.open=opened
