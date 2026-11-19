"""Bounded candidate fallback; source attribution is never transferred to other papers."""
import copy,time,urllib.parse
import common as C
import retrieval_resilient as R

def canonical(url):
 p=urllib.parse.urlsplit(url)
 q=urllib.parse.urlencode([(k,v) for k,v in urllib.parse.parse_qsl(p.query) if not k.lower().startswith('utm_')])
 return urllib.parse.urlunsplit((p.scheme,p.netloc,p.path,q,''))

def verify(check,rules,root,cfg):
 with R.deadline_scope(cfg.get('acquisition_seconds',180)):
  return _verify(check,rules,root,cfg)

def _verify(check,rules,root,cfg):
 start=time.monotonic();ev=[];attempts=[];seen=set();searches=[]
 old=C.pt.v2.old;folder=root/'checks'/check['check_id']
 def fetch(url,role):
  url=canonical(url)
  if url in seen:return False
  seen.add(url)
  if old.policy.excluded({'url':url,'title':''},rules):
   attempts.append({'url':url,'role':role,'status':'excluded'});return False
  try:source=R.fetch(url,forbidden_urls=rules['urls'])
  except TimeoutError as ex:
   attempts.append({'url':url,'role':role,'status':'deadline_unread','error':str(ex)});return False
  attempts.append({'url':url,'role':role,'status':source['status'],'error':source.get('error'),'parser':source.get('parser')})
  segments=old.choose_segments(source,check['question']+' '+check['quote'])
  for e in segments:ev.append(e|{'id':role+':'+e['id'],'role':role,'url':url,'body_sha':source.get('content_sha256'),'parser':source.get('parser'),'formula_table_reliability':source.get('formula_table_reliability')})
  return bool(segments)
 urls=list(dict.fromkeys(c['url'] for c in check['citations']))
 # Every URL bound to the requested paragraph is attempted, never silently sliced.
 for u in urls:fetch(u,'original')
 initial_ev=copy.deepcopy(ev);initial_attempts=copy.deepcopy(attempts)
 data={'check_id':check['check_id'],'question':check['question'],'quote':check['quote'],'original_units':check['original_units'],'has_citation':bool(urls),'evidence':initial_ev,'acquisition':initial_attempts,'unread_original_urls':[a['url'] for a in attempts if a['status']=='deadline_unread']}
 C.T.save(folder/'citation_input.json',data)
 empty=lambda status:{'status':status,'evidence_ids':[],'supports':'','limits':'No acquired original source body; not evidence of falsehood.'}
 first={'citation':empty('insufficient_material' if urls else 'not_cited'),'fact':empty('insufficient_material'),'task_effect':'Unresolved.'}
 original_prompt=C.pt.v2.VERIFY+'\nAll explicit URLs in the requested original unit are candidate citations, not proof of attribution to every assertion. First determine whether their placement/context attributes the quoted assertion to them; then assess support only from acquired original bodies. Explain which source supports which part and retain attribution ambiguity. Do not let supplementary sources repair the original-citation judgment.'
 if initial_ev:first=old.ds_call(root,check['check_id']+'_original',original_prompt,data,lambda o,d:old.validate_card(C.normalize(o),d),cfg)['result']
 acquired=0;tried=0
 # Discovery reads search metadata, but no snippet is accepted as source-body evidence.
 for query in [check['search_query'],check['search_query']+' filetype:pdf']:
  if first['fact']['status']=='supported':break
  if acquired>=2 or tried>=6 or time.monotonic()-start>=cfg.get('acquisition_seconds',180):break
  try:found=R.search(query)
  except TimeoutError:
   searches.append({'status':'deadline_unread','query':query});break
  searches.append(found)
  candidates=[]
  failed_hosts={urllib.parse.urlsplit(s['url']).hostname for s in attempts if s['status']=='failed'}
  for item in found.get('results',[]):
   url=item.get('url') or item.get('link')
   if url and url.startswith(('http://','https://')) and canonical(url) not in seen and not old.policy.excluded({'url':url,'title':item.get('title','')},rules):candidates.append(url)
  candidates=list(dict.fromkeys(candidates))
  candidates.sort(key=lambda u:(urllib.parse.urlsplit(u).hostname in failed_hosts,not urllib.parse.urlsplit(u).path.lower().endswith('.pdf')))
  for url in candidates:
   if acquired>=2 or tried>=6 or time.monotonic()-start>=cfg.get('acquisition_seconds',180):break
   tried+=1;acquired+=fetch(url,'supplemental')
 C.T.save(folder/'searches.json',searches)
 C.T.save(folder/'acquisition.json',{'sources':attempts,'evidence':ev,'supplemental_attempts':tried,'supplemental_bodies':acquired,'seconds':time.monotonic()-start})
 final=first
 if any(e['role']=='supplemental' for e in ev):
  fd={'check_id':check['check_id'],'question':check['question'],'original_units':check['original_units'],'evidence':ev,'acquisition':attempts}
  C.T.save(folder/'follow_input.json',fd)
  follow=old.ds_call(root,check['check_id']+'_fact',C.pt.v2.FOLLOW,fd,lambda o,d:C.pt.v2.follow_valid(C.normalize(o),d),cfg)['result']
  final={'citation':first['citation'],**follow}
 result={'check_id':check['check_id'],'execution':'completed' if ev else 'no_material','result':final,'before':first,'sources':attempts,'evidence':ev,'seconds':time.monotonic()-start,'supplemental_attempts':tried,'supplemental_bodies':acquired,'search_statuses':[s['status'] for s in searches]}
 C.T.save(folder/'result.json',result);return result
