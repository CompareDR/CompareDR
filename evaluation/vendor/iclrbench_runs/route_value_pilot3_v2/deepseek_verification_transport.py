"""Separate verification transport and content cache; no GPT RPM usage."""
import json,re,time,urllib.request,os
from run_extract import ROOT,transport

def call(dest,name,prompt,data,validator,config):
 endpoint=config.get('verifier_endpoint',config['endpoint'])
 body={'model':'deepseek-v4.1-flash','thinking':{'type':'disabled'},'max_tokens':12000,'stream':False,'messages':[{'role':'system','content':prompt},{'role':'user','content':json.dumps(data,ensure_ascii=False)}]}
 folder=dest/'deepseek_calls'/transport.digest({'name':name,'body':body,'endpoint':endpoint})
 transport.freeze(folder/'identity.json',{'name':name,'body':body,'endpoint':endpoint})
 if (folder/'success.json').exists():
  out=transport.load(folder/'success.json');validator(out['result'],data);return out
 key=__import__('provider_config').api_key('verifier');prior=None;error=''
 for attempt in range(3):
  request=dict(body)
  if prior:request['messages']=body['messages']+[{'role':'assistant','content':prior},{'role':'user','content':'Repair only this structural error: '+error}]
  started=time.time();stamp=str(time.time_ns());transport.save(folder/f'request_{stamp}.json',request)
  try:
   req=urllib.request.Request(endpoint,json.dumps(request).encode(),{'Content-Type':'application/json','Authorization':'Bearer '+key})
   with urllib.request.build_opener(urllib.request.ProxyHandler({})).open(req,timeout=300) as r:raw=json.load(r)
   raw=json.loads(json.dumps(raw).replace(key,'[REDACTED]'));transport.save(folder/f'response_{stamp}.json',{'raw':raw,'seconds':time.time()-started})
   if raw['choices'][0].get('finish_reason')=='length':raise ValueError('truncated response')
   prior=raw['choices'][0]['message']['content'];result=json.loads(re.sub(r'^```(?:json)?\s*|\s*```$','',prior.strip()));validator(result,data)
   out={'result':result,'usage':raw.get('usage'),'returned_model':raw.get('model'),'requested_model':body['model'],'call_key':folder.name}
   transport.save(folder/'success.json',out);return out
  except Exception as e:
   error=str(e).replace(key,'[REDACTED]');transport.save(folder/f'error_{stamp}.json',{'error':error,'seconds':time.time()-started})
 raise RuntimeError(name+': '+error)

def install(chain,dest):
 freeze=transport.freeze
 def revised(path,value):
  if path.name=='protocol.json':
   path=path.with_name('protocol_pt_routed_v8.json')
   value=value|{'pointwise':'Query, original segments, rubrics only. No cards or graphs; no verification wait.','composite':'Execution completed/planned as seventh operational dimension, equal dimension weighting for connectivity demo only; quality-only score separately retained.'}
   value=value|{'verification_model':'deepseek-v4.1-flash','verification_thinking':'disabled','change':'Only verification verdict transport changed; previous protocol preserved.'}
  return freeze(path,value)
 transport.freeze=revised
 original=chain.stage
 def stage(name,prompt,data,validator):
  folder=dest/name
  # A successful frozen stage is authoritative, including successes from repair calls.
  # Check its exact input and semantic contract before reuse; never regenerate it.
  if (folder/'output.json').exists():
   transport.freeze(folder/'input.json',data)
   accepted=transport.load(folder/'output.json')
   validator(accepted['result'],data)
   return accepted['result']
  if not name.startswith('verification/'):
   try:return original(name,prompt,data,validator)
   except RuntimeError as e:
    # Some responses contain a complete JSON object followed only by surplus
    # closing brackets. Recover that object only if the full validator accepts it.
    for identity_path in sorted((dest/'calls').glob('*/identity.json')):
     identity=transport.load(identity_path)
     if not identity.get('name','').endswith(name):continue
     messages=identity.get('body',{}).get('messages',[])
     if len(messages)<2 or messages[0].get('content')!=prompt:continue
     try:matches=json.loads(messages[1]['content'])==data
     except (ValueError,KeyError):continue
     if not matches:continue
     for response_path in sorted(identity_path.parent.glob('response_*.json'),reverse=True):
      try:
       raw=transport.load(response_path)['raw'];choice=raw['choices'][0]
       if choice.get('finish_reason')=='length':continue
       text=re.sub(r'^```(?:json)?\s*|\s*```$','',choice['message']['content'].strip())
       value,end=json.JSONDecoder().raw_decode(text)
       tail=text[end:].strip()
       if not tail or not re.fullmatch(r'[\]}\s]+',tail):continue
       validator(value,data)
      except (ValueError,KeyError,TypeError,AssertionError):continue
      out={'result':value,'usage':raw.get('usage'),'returned_model':raw.get('model'),
           'call_key':identity_path.parent.name,'technical_recovery':{'source':str(response_path),'removed_trailing_closers':tail}}
      transport.freeze(folder/'input.json',data)
      transport.freeze(folder/'output.json',out)
      transport.save(folder/'trailing_closer_recovery.json',out['technical_recovery'])
      print(name,'RECOVERED trailing closers',flush=True)
      return value
    transport.save(dest/name/'repair_v8_event.json',{'original_error':str(e),'action':'One additional bounded technical retry series; no outcome-based retries.'})
    retry_round=os.environ.get('EVAL_RETRY_ROUND','')
    recovery_name=('repair_v8_'+retry_round+'_' if retry_round else 'repair_v8_')+name
    out=transport.Client().call(recovery_name,prompt,data,validator,'en','technical_recovery')
    transport.freeze(dest/name/'output.json',out)
    return out['result']
  transport.freeze(dest/name/'input.json',data)
  out=call(dest,name,prompt,data,validator,chain.CFG)
  transport.freeze(dest/name/'output.json',out)
  return out['result']
 chain.stage=stage
