"""Bounded retries, then auditable warning acceptance. Never synthesize a score."""
import copy,json,re,time,urllib.request,hashlib,os
from email.utils import parsedate_to_datetime
from pathlib import Path
VERSION='formal-soft-contracts-v2'
class UnusableOutput(ValueError):pass
def text(x):return x if isinstance(x,str) else '' if x is None else json.dumps(x,ensure_ascii=False)
def arr(x):return x if isinstance(x,list) else [] if x is None else [x]
def ids(x,allowed):return list(dict.fromkeys(i for i in arr(x) if isinstance(i,str) and i in allowed))
def number(x):
    if isinstance(x,str) and re.fullmatch(r'[0-5]',x):return int(x)
    if type(x) is float and x.is_integer():return int(x)
    return x
def rows(value,key,expected):
    out={}
    for r in arr(value):
        if not isinstance(r,dict) or r.get(key) not in expected:continue
        k=r[key]
        if k in out and out[k]!=r:raise UnusableOutput('Conflicting duplicate decision: '+str(k))
        out[k]=r
    missing=set(expected)-set(out)
    if missing:raise UnusableOutput('No actual decision for: '+str(sorted(missing)))
    return [out[k] for k in expected]
def request(q,units):
    if not isinstance(q,dict):return None
    u=q.get('original_id');quote=q.get('quote')
    if u not in units or not isinstance(quote,str) or not quote or quote not in units[u]:return None
    if not isinstance(q.get('question'),str) or not q['question']:return None
    return q|{'score_dependency':text(q.get('score_dependency')),'search_query':q.get('search_query') or q['question']}
def fallback(name,value,data,context=None):
    if not isinstance(value,dict):raise UnusableOutput('No JSON object')
    o=copy.deepcopy(value)
    if name.startswith('graph_'):
        if 'claims' not in o:
            for k in ('graph','result'):
                if isinstance(o.get(k),dict) and 'claims' in o[k]:o=o[k];break
        units={u['id']:u for u in context['units']};claims=[];seen=set()
        for c in arr(o.get('claims')):
            if not isinstance(c,dict) or not isinstance(c.get('id'),str) or c['id'] in seen or not text(c.get('statement')):continue
            c['block_ids']=ids(c.get('block_ids'),units);c['condition_block_ids']=ids(c.get('condition_block_ids'),units)
            if not c['block_ids']:continue
            allowed={i for b in c['block_ids']+c['condition_block_ids'] for i in units[b]['citation_ids']}
            c['citation_ids']=ids(c.get('citation_ids'),allowed);c['statement']=text(c['statement']);c['conditions']=text(c.get('conditions'));c['kind']=text(c.get('kind'));claims.append(c);seen.add(c['id'])
        if not claims:raise UnusableOutput('Empty graph: no usable source-anchored claim after bounded retries')
        branches=[]
        for b in arr(o.get('branches')):
            if not isinstance(b,dict):continue
            b['claim_ids']=ids(b.get('claim_ids'),seen);b['question_answered']=text(b.get('question_answered'))
            if b['claim_ids'] and isinstance(b.get('id'),str):branches.append(b)
        edges=[]
        for e in arr(o.get('relations')):
            if not isinstance(e,dict) or e.get('conclusion') not in seen:continue
            e['premises']=ids(e.get('premises'),seen);e['block_ids']=ids(e.get('block_ids'),units)
            if not e['premises'] or e['conclusion'] in e['premises'] or not e['block_ids']:continue
            for k in ('id','type','dependency','rationale'):e[k]=text(e.get(k))
            e['reconstructed']=e.get('reconstructed',False);edges.append(e)
        return o|{'branches':branches,'claims':claims,'relations':edges,'limitations':[text(v) for v in arr(o.get('limitations'))]+['Graph passed with structural warnings; absent extracted nodes are not report omissions.']}
    if name.startswith('loc_'):
        actual=rows(o.get('locations'),'guide_id',[g['id'] for g in data['comparison_questions']])
        existing={r['guide_id']:r for r in actual};out=[]
        for g in data['comparison_questions']:
            r=existing.get(g['id'],{});ss={s.get('report_id'):s for s in arr(r.get('sides')) if isinstance(s,dict)};sides=[]
            for report in data['reports']:
                rid=report['report_id'];s=ss.get(rid,{});cs={c['id'] for c in report['claims']};sections={x['id'] for x in report['sections']}
                sides.append({'report_id':rid,'claim_ids':ids(s.get('claim_ids'),cs),'read_sections':[x|{'reason':text(x.get('reason'))} for x in arr(s.get('read_sections')) if isinstance(x,dict) and x.get('section_id') in sections],'focus':text(s.get('focus'))})
                if not sides[-1]['claim_ids'] and not sides[-1]['read_sections']:
                    raise UnusableOutput('No actual localized region for '+g['id']+'/'+rid)
            out.append({'guide_id':g['id'],'sides':sides,'alignment_reason':text(r.get('alignment_reason')),'coverage_limit':text(r.get('coverage_limit'))+' [Automatic localization incomplete or unvalidated; not absence evidence.]'})
        return o|{'locations':out}
    if name.startswith('diff_'):
        import compat
        actual=rows(o.get('results'),'guide_id',[p['guide']['id'] for p in data['guide_packets']])
        existing={r['guide_id']:r for r in actual};out=[]
        claim_pool={};original_pool={p['report_id']:{u['id'] for u in p['originals']} for p in data['report_pools']}
        for p in data['guide_packets']:
            for s in p['sides']:claim_pool.setdefault(s['report_id'],set()).update(c['id'] for c in s['local_graph']['claims'])
        for p in data['guide_packets']:
            r=existing.get(p['guide']['id'],{});scopes={s['report_id']:s for s in p['sides']};ds=[];seen=set()
            for d in arr(r.get('differences')):
                if not isinstance(d,dict) or not isinstance(d.get('id'),str) or d['id'] in seen:continue
                sides=[s for s in arr(d.get('sides')) if isinstance(s,dict)]
                if len(sides)!=len(scopes) or {s.get('report_id') for s in sides}!=set(scopes):continue
                for s in sides:
                    rid=s['report_id'];s['claim_ids']=ids([compat.canonical_id(i,claim_pool[rid]) for i in arr(s.get('claim_ids')) if isinstance(i,str)],claim_pool[rid]);s['segment_ids']=ids([compat.canonical_id(i,original_pool[rid]) for i in arr(s.get('segment_ids')) if isinstance(i,str)],original_pool[rid]);s['contribution']=text(s.get('contribution'))
                    if not s['segment_ids']:raise UnusableOutput('Difference has no supplied original anchor: '+rid)
                d.update(sides=sides,issue=text(d.get('issue')),task_impact=text(d.get('task_impact')),unresolved_dependencies=[text(x) for x in arr(d.get('unresolved_dependencies'))]);ds.append(d);seen.add(d['id'])
            if not ds and arr(r.get('differences')):raise UnusableOutput('All actual differences became unusable')
            if not ds and not text(r.get('limitations')).strip():raise UnusableOutput('Zero differences require actual coverage explanation')
            out.append({'guide_id':p['guide']['id'],'differences':ds,'limitations':text(r.get('limitations'))+' [Warning acceptance; no inferred report omission.]'})
        return o|{'results':out}
    if name.startswith('plan_'):
        if not isinstance(o.get('bindings'),list):raise UnusableOutput('No actual verification plan')
        originals={}
        for d in data['differences']:
            for s in d['sides']:originals.setdefault(s['report_id'],{}).update({u['id']:u['text'] for u in s['originals']})
        existing={(b.get('guide_id'),b.get('difference_id'),b.get('report_id')):b for b in arr(o.get('bindings')) if isinstance(b,dict)};out=[];budget=set()
        for d in data['differences']:
            for s in d['sides']:
                k=(d['guide_id'],d['id'],s['report_id']);b=existing.get(k,{});allowed={c['check_id'] for c in s['candidate_cards']};q=request(b.get('request'),originals[s['report_id']]);bk=(k[0],k[2])
                if k not in existing:raise UnusableOutput('Missing actual verification binding: '+str(k))
                if q and bk in budget:q=None
                if q:budget.add(bk)
                out.append({'guide_id':k[0],'difference_id':k[1],'report_id':k[2],'reuse':[x|{'relevance':text(x.get('relevance'))} for x in arr(b.get('reuse')) if isinstance(x,dict) and x.get('check_id') in allowed],'request':q,'new_check_ids':[]})
        return o|{'bindings':out}
    if name.startswith('pt_'):
        initial=name.endswith('_initial');expected=[r['id'] for r in data['rubrics']] if initial else [x['rubric']['id'] for x in data['items']];field='scores' if initial else 'reviews';rr=rows(o.get(field), 'rubric_id',expected)
        for r in rr:
            r['score']=number(r.get('score'))
            if type(r['score']) is not int or not 1<=r['score']<=5:raise UnusableOutput('No valid actual pointwise score')
            r['reason']=text(r.get('reason'))
            if not r['reason'].strip():raise UnusableOutput('Actual score needs a nonempty reason')
            if initial:
                units={u['id']:u['text'] for u in data['report']};r['original_ids']=ids(r.get('original_ids'),units);r['verification_request']=request(r.get('verification_request'),units)
                if context and r['rubric_id'] in context.get('report_only',[]):r['verification_request']=None
            else:
                item=next(x for x in data['items'] if x['rubric']['id']==r['rubric_id']);r['action']='keep' if r['score']==item['initial']['score'] else 'change'
                for k in ('changed_premise','anchor_effect'):r[k]=text(r.get(k))
                r['check_ids']=ids(r.get('check_ids'),{x['check_id'] for x in item['verification']});r['evidence_ids']=ids(r.get('evidence_ids'),{e['id'] for x in item['verification'] for e in x.get('evidence',[])})
                if r['action']=='change' and not r['check_ids']:
                    r.setdefault('_quality_warnings',[]).append('Changed score has no usable check binding; not verified improvement.')
        return o|{field:rr}
    if name.startswith(('judge_','readability_raw_')):
        import common as C
        raw=name.startswith('readability_raw_');d=data if raw else C.pw.unpacked(data);guides=d['guides'] if raw else [p['guide'] for p in d['guide_packets']];rr=rows(o.get('judgments'),'guide_id',[g['id'] for g in guides]);rids=[r['report_id'] for r in d['reports']];aliases=dict(zip(('A','B'),rids))
        for r in rr:
            r['preferred_report_id']=aliases.get(r.get('preferred_report_id'),r.get('preferred_report_id'));w=r['preferred_report_id'];v=number(r.get('strength'));r['strength']=v
            if w not in rids+['tie'] or type(v)is not int or v not in ([0] if w=='tie' else [1,2]):raise UnusableOutput('No unambiguous actual winner/strength')
            r['reason']=text(r.get('reason'));r['unresolved_dependencies']=[text(x) for x in arr(r.get('unresolved_dependencies'))];ev=[]
            if not r['reason'].strip():raise UnusableOutput('Actual winner needs a nonempty reason')
            for e in arr(r.get('evidence')):
                if not isinstance(e,dict):continue
                rid=aliases.get(e.get('report_id'),e.get('report_id'));report=next((x for x in d['reports'] if x['report_id']==rid),None)
                if report is None:continue
                if raw:
                    q=e.get('quote')
                    if isinstance(q,str) and q and q in report['text']:ev.append(e|{'report_id':rid})
                else:ev.append(e|{'report_id':rid,'segment_ids':ids(e.get('segment_ids'),{u['id'] for u in report['originals']})})
            r['evidence']=ev
            if {e['report_id'] for e in ev}!=set(rids):r.setdefault('_quality_warnings',[]).append('Incomplete original evidence coverage; decision retained, not strict evidence pass.')
            p=next((p for p in d.get('guide_packets',[]) if p['guide']['id']==r['guide_id']),{})
            r['difference_ids']=ids(r.get('difference_ids'),{x['id'] for x in p.get('differences',[])});r['check_ids']=ids(r.get('check_ids'),{x['check_id'] for x in p.get('verification_cards',[])})
        return o|{'judgments':rr}
    # DeepSeek cards: preserve verdicts as unvalidated data, isolate unsupported evidence IDs.
    if 'evidence' in data:
        ev={e['id']:e for e in data['evidence']}
        for k in ('citation','fact'):
            if k not in o:continue
            a=o[k]
            if not isinstance(a,dict) or a.get('status') not in ['supported','partial','contradicted','insufficient_material','not_cited']:raise UnusableOutput('No actual verifier status')
            old_ids=arr(a.get('evidence_ids'));a['evidence_ids']=ids(old_ids,{i for i,e in ev.items() if k=='fact' or e.get('role')=='original'})
            if (a['status'] in ['supported','partial','contradicted'] and (not a['evidence_ids'] or set(a['evidence_ids'])!=set(old_ids))) or (k=='citation' and ((a['status']=='not_cited')!=(not data.get('has_citation',True)))):
                a['unvalidated_original_status']=a['status'];a['status']='insufficient_material'
            a['supports']=text(a.get('supports'));a['limits']=text(a.get('limits'))+' [Verifier output did not pass strict validation.]'
        if 'fact' not in o:raise UnusableOutput('No fact verdict')
        o['task_effect']=text(o.get('task_effect'));return o
    raise UnusableOutput('No adapter for '+name)

def invoke(dest,name,prompt,data,validator,cfg,T,model=None,max_tokens=12000,raw=False,sem=None,context=None,credential_root=None):
    import compat
    import settings
    from provider_config import api_key
    model=model or cfg['model'];ds=model=='deepseek-v4.1-flash'
    cfg = dict(cfg, endpoint=cfg.get('verifier_endpoint', cfg['endpoint'])) if ds else cfg
    limit=cfg.get('ds_attempts',3) if ds else cfg.get('attempts',4)
    if not isinstance(limit,int) or limit<1:raise ValueError('attempt limit must be >=1')
    body={'model':model,'max_tokens':max_tokens,'stream':False,'messages':[{'role':'system','content':prompt},{'role':'user','content':data if raw else json.dumps(data,ensure_ascii=False)}]}
    body.update({'thinking':{'type':'disabled'}} if ds else {'reasoning_effort':cfg['reasoning_effort']})
    contract={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in [Path(__file__),Path(compat.__file__)]}
    identity={'body':body,'endpoint':cfg['endpoint'],'policy':VERSION,'contract':contract,'implementation':settings.contract_hash(),'run_version':cfg.get('version')};key=T.digest(identity);folder=dest/('deepseek_calls' if ds else 'calls')/key
    T.freeze(folder/'identity.json',identity)
    if True:  # Every stage is traceable, including the all-DeepSeek judge run.
        stage=dest/'stage_inputs'/f'{name}.json'
        if stage.exists() and T.load(stage).get('call_key')!=key:T.save(dest/'stage_input_history'/name/(T.load(stage)['call_key']+'.json'),T.load(stage))
        T.save(stage,{'prompt':prompt,'data':data,'call_key':key,'policy':VERSION})
    success=folder/'success.json'
    if success.exists():
        cached=T.load(success)
        try:
            if cached.get('source')=='no_parseable_response_navigation_fallback':raise UnusableOutput('No actual model response')
            checked=copy.deepcopy(cached['result'])
            if cached.get('acceptance')=='accepted_with_warnings':checked=fallback(name,checked,data,context)
            else:validator(checked,data)
            minimum(name,checked,data)
            return cached
        except Exception:
            success.replace(folder/('invalidated_success_'+str(time.time_ns())+'.json'))
    prior=None;error='';candidates=[]
    def parse(a):return compat.parse_response(a['choices'][0]['message']['content'])
    def inspect_response(a,source):
        nonlocal prior,error
        try:
            prior=a['choices'][0]['message']['content'];o=parse(a);checked=copy.deepcopy(o)
            if a['choices'][0].get('finish_reason')!='stop':raise ValueError('incomplete response: expected stop')
            returned=a.get('model','')
            if model=='gpt-5.5' and not returned.startswith('gpt-5.5'):raise ValueError('Unexpected returned model: '+returned)
            if model=='deepseek-v4.1-flash' and not returned.startswith('deepseek'):raise ValueError('Unexpected verifier model: '+returned)
            candidates.append((copy.deepcopy(o),a,source))
            validator(checked,data)
            minimum(name,checked,data)
            accepted={'result':checked,'usage':a.get('usage'),'returned_model':a.get('model'),'call_key':key,'acceptance':'strict','source':source};T.save(success,accepted);return accepted
        except Exception as ex:error=str(ex);return None
    for f in sorted(folder.glob('response_*.json')):
        accepted=inspect_response(T.load(f)['raw'],f.name)
        if accepted:return accepted
    count=len(list(folder.glob('request_*.json')))
    secret=None
    if count<limit:
        if os.environ.get('MULTIDIM_OFFLINE')=='1':raise UnusableOutput('Offline cache miss: '+name)
        secret=api_key('verifier' if ds else 'judge')
    for attempt in range(count,limit):
        req=copy.deepcopy(body)
        if prior and len(prior)<200000:req['messages'] += [{'role':'assistant','content':prior},{'role':'user','content':'Repair only this output-contract error. Preserve unrelated content and return the complete JSON object: '+error}]
        elif error:req['messages'] += [{'role':'user','content':'The previous attempt failed: '+error+'. Return the complete requested JSON; original inputs above are unchanged.'}]
        T.save(folder/f'request_{attempt:03d}.json',req);start=time.time()
        try:
            request_obj=urllib.request.Request(cfg['endpoint'],json.dumps(req).encode(),{'Content-Type':'application/json','Authorization':'Bearer '+secret})
            from contextlib import nullcontext
            with sem if sem is not None else nullcontext():
                timeout=cfg.get('ds_timeout_seconds',180) if ds else cfg.get('graph_timeout_seconds',900) if name.startswith('graph_') else cfg.get('request_timeout_seconds',600)
                with urllib.request.build_opener(urllib.request.ProxyHandler({})).open(request_obj,timeout=timeout) as response:a=json.load(response)
            a=json.loads(json.dumps(a).replace(secret,'[REDACTED]'));source=f'response_{attempt:03d}.json';T.save(folder/source,{'raw':a,'seconds':time.time()-start})
            accepted=inspect_response(a,source)
            if accepted:return accepted
        except Exception as ex:
            error=str(ex).replace(secret,'[REDACTED]');status=getattr(ex,'code',None)
            retry_after=getattr(ex,'headers',{}).get('Retry-After') if getattr(ex,'headers',None) else None
            T.save(folder/f'error_{attempt:03d}.json',{'error':error,'seconds':time.time()-start,'http_status':status,'retry_after':retry_after,'usage':'unknown'})
            if status in (400,401,403,404):break
            if attempt+1<limit:
                try:delay=max(1.0,float(retry_after)) if retry_after else min(30,2**attempt)
                except ValueError:
                    try:delay=max(1.0,parsedate_to_datetime(retry_after).timestamp()-time.time())
                    except (ValueError,TypeError,OverflowError):delay=min(30,2**attempt)
                time.sleep(delay)
            continue
        T.save(folder/f'error_{attempt:03d}.json',{'error':error,'seconds':time.time()-start,'category':'output_contract'})
    errors=[T.load(p) for p in sorted(folder.glob('error_*.json'))]
    for o,a,source in reversed(candidates):
        try:
            result=fallback(name,o,data,context);minimum(name,result,data)
        except Exception as ex:error=str(ex);continue
        note={'policy':VERSION,'stage':name,'attempt_limit':limit,'attempts_used':len(list(folder.glob('request_*.json'))),'errors':errors,'latest_validation_error':error,'source':source,'action':'accepted_with_warnings','strict_valid':False,'warning':'Invalid links may be quarantined; this is NOT a strict pass or independently verified support.'}
        result['_soft_acceptance']=note;T.save(folder/'warning_raw.json',o);T.save(folder/'warning.json',note)
        T.save(dest/'soft_errors'/f'{key}.json',note)
        accepted={'result':result,'usage':a.get('usage'),'returned_model':a.get('model'),'call_key':key,'acceptance':'accepted_with_warnings','source':source};T.save(success,accepted);return accepted
    note={'policy':VERSION,'stage':name,'action':'unusable_after_retry_limit','error':error,'attempt_limit':limit,'errors':errors};T.save(folder/'unusable.json',note);T.save(dest/'soft_errors'/f'{key}.json',note)
    raise UnusableOutput(name+': '+error)

def minimum(name,result,data):
    """Structural execution minimum, not a threshold on preferred outcomes."""
    if name.startswith('graph_') and not result.get('claims'):raise UnusableOutput('Empty graph')
    if name.startswith('loc_'):
        for row in rows(result.get('locations'),'guide_id',[g['id'] for g in data['comparison_questions']]):
            actual=rows(row.get('sides'),'report_id',[r['report_id'] for r in data['reports']])
            if any(not s.get('claim_ids') and not s.get('read_sections') for s in actual):raise UnusableOutput('Empty localization: no inspected source region')
    if name.startswith('diff_'):
        for row in rows(result.get('results'),'guide_id',[p['guide']['id'] for p in data['guide_packets']]):
            if not row.get('differences') and not text(row.get('limitations')).strip():raise UnusableOutput('Zero difference without coverage explanation')
