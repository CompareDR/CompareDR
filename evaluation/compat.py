"""Structural compatibility only. Never manufacture claims, sources or scores."""
import copy,re,json
import common as C

def parse_response(text):
    text=re.sub(r'^```(?:json)?\s*|\s*```$','',text.strip())
    try:return json.loads(text)
    except json.JSONDecodeError:
        obj,end=json.JSONDecoder().raw_decode(text)
        tail=text[end:].strip()
        if tail and re.fullmatch(r'[\]}\s]+',tail):
            if isinstance(obj,dict):obj.setdefault('_structural_diagnostics',[]).append({'action':'ignore_extra_closing_delimiters','trailing':tail})
            return obj
        # Only discard a duplicate serialization, never a different second answer.
        if tail and json.loads(tail)!=obj:raise ValueError('ambiguous multiple JSON answers')
        return obj

def validate_output(name,out,data,validator):
    events=[];scope=data
    if name.startswith('judge_'):
        unpacked=C.pw.unpacked(data)
        scope=copy.deepcopy(unpacked);validator=C.pw.p.valid_judge
        supplied_cards={c['check_id']:c for p in unpacked['guide_packets'] for c in p['verification_cards']}
        for packet in scope['guide_packets']:
            used={r.get('guide_id'):r.get('check_ids',[]) for r in out.get('judgments',[])}.get(packet['guide']['id'],[])
            own={c['check_id'] for c in packet['verification_cards']}
            borrowed=[i for i in used if i not in own and i in supplied_cards]
            if borrowed:
                packet['verification_cards'] += [supplied_cards[i] for i in borrowed]
                events.append({'action':'reuse_card_supplied_in_same_pair_packet','guide_id':packet['guide']['id'],'check_ids':borrowed})
        aliases=dict(zip(('A','B'),[r['report_id'] for r in unpacked['reports']]))
        for row in out.get('judgments',[]):
            for obj,field in [(row,'preferred_report_id')]+[(s,'report_id') for s in row.get('evidence',[])]:
                if obj.get(field) in aliases:
                    events.append({'action':'physical_order_alias','from':obj[field],'to':aliases[obj[field]]})
                    obj[field]=aliases[obj[field]]
            for side in row.get('evidence',[]):
                allowed=[u['id'] for r in unpacked['reports'] if r['report_id']==side.get('report_id') for u in r['originals']]
                side['segment_ids']=[canonical_id(i,allowed) for i in side.get('segment_ids',[])]
                invalid=[i for i in side['segment_ids'] if i not in allowed]
                if invalid and any(i in allowed for i in side['segment_ids']):
                    events.append({'action':'quarantine_invalid_extra_anchors','guide_id':row.get('guide_id'),'report_id':side.get('report_id'),'invalid_ids':invalid})
                    side['segment_ids']=[i for i in side['segment_ids'] if i in allowed]
    if name.startswith('plan_'):
        scope=copy.deepcopy(data)
        originals={}
        for d in data['differences']:
            for s in d['sides']:
                originals.setdefault(s['report_id'],{}).update({u['id']:u for u in s['originals']})
        for d in scope['differences']:
            for s in d['sides']:s['originals']=list(originals[s['report_id']].values())
        sides={(d['guide_id'],d['id'],s['report_id']):s for d in scope['differences'] for s in d['sides']}
        for b in out.get('bindings',[]):
            q=b.get('request');side=sides.get((b.get('guide_id'),b.get('difference_id'),b.get('report_id')))
            if not q or not side:continue
            matches=[(u['id'],exact_whitespace_span(q.get('quote'),u['text'])) for u in side['originals']]
            matches=[m for m in matches if m[1] is not None]
            selected=next((m for m in matches if m[0]==q.get('original_id')),matches[0] if len(matches)==1 else None)
            if selected:
                if (q.get('original_id'),q.get('quote'))!=selected:events.append({'action':'restore_exact_quote_binding','original_id':selected[0]})
                q['original_id'],q['quote']=selected
            else:
                raise ValueError('Request quote is not an exact span in the supplied report originals: '+str({'guide_id':b.get('guide_id'),'difference_id':b.get('difference_id'),'report_id':b.get('report_id'),'original_id':q.get('original_id'),'allowed_ids':[u['id'] for u in side['originals']]})+'. Select a verbatim passage from these supplied originals; do not reconstruct a quote.')
    if name.startswith('diff_'):
        # A batched call sees the union of selected regions. Permit references to
        # material actually supplied in that same report, not unseen graph nodes.
        scope=copy.deepcopy(data)
        for packet in scope['guide_packets']:
            for side in packet['sides']:
                rid=side['report_id'];claims={}
                for p in data['guide_packets']:
                    for s in p['sides']:
                        if s['report_id']==rid:claims.update({c['id']:c for c in s['local_graph']['claims']})
                side['allowed_original_ids']=[u['id'] for p in data['report_pools'] if p['report_id']==rid for u in p['originals']]
                side['local_graph']['claims']=list(claims.values())
        for row in out.get('results',[]):
            for diff in row.get('differences',[]):
                for side in diff.get('sides',[]):
                    pools=[s for p in scope['guide_packets'] for s in p['sides'] if s['report_id']==side['report_id']]
                    if pools:
                        side['claim_ids']=[canonical_id(i,[c['id'] for c in pools[0]['local_graph']['claims']]) for i in side.get('claim_ids',[])]
                        side['segment_ids']=[canonical_id(i,pools[0]['allowed_original_ids']) for i in side.get('segment_ids',[])]
        events.append({'action':'validate_against_supplied_batch_scope'})
    if name.startswith('pt_') and not name.endswith('_initial'):
        for row in out.get('reviews',[]):
            if row.get('action')=='keep':
                for field in ('changed_premise','anchor_effect'):
                    if row.get(field) is None:row[field]='';events.append({'action':'optional_empty','field':field})
    validator(out,scope)
    if events:out.setdefault('_structural_diagnostics',[]).extend(events)

def canonical_id(value,allowed):
    if value in allowed:return value
    key=lambda s:re.sub(r'\d+',lambda m:str(int(m.group())),s)
    matches=[i for i in allowed if key(i)==key(value)]
    return matches[0] if len(matches)==1 else value

def recover_deepseek(original):
    if getattr(original,'soft_contracts',False):return original
    transport=original.__globals__['transport']
    credential_root=original.__globals__.get('ROOT',transport.ROOT)
    def call(dest,name,prompt,data,validator,config):
        import soft_contracts as S
        return S.invoke(dest,name,prompt,data,lambda o,d:validator(C.normalize(o),d),config,transport,model='deepseek-v4.1-flash',credential_root=credential_root)
    call.soft_contracts=True
    return call

def graph_output(out,units):
    g=copy.deepcopy(out);events=copy.deepcopy(out.get('_structural_diagnostics',[])) if isinstance(out,dict) else []
    if isinstance(g,dict) and 'claims' not in g:
        for key in ('graph','result'):
            if isinstance(g.get(key),dict) and 'claims' in g[key]:
                g=g[key];events.append({'action':'unwrap','field':key});break
    C.need(isinstance(g,dict) and isinstance(g.get('claims'),list),'complete graph with claims required')
    g,normalizations=C.graph.v.normalize_conditions(g);events+=normalizations
    # Report identity is supplied by the caller, not inferred by the model.
    g['report_id']='R1'
    for key in ('relations','limitations'):
        if g.get(key) is None:g[key]=[];events.append({'action':'optional_empty','field':key})
    if isinstance(g['limitations'],str):g['limitations']=[g['limitations']]
    for c in g['claims']:
        for key in ('condition_block_ids','citation_ids'):
            if c.get(key) is None:c[key]=[]
        for key in ('block_ids','condition_block_ids','citation_ids'):
            if isinstance(c.get(key),str):c[key]=[c[key]]
    kept=[]
    for edge in g['relations']:
        if edge.get('conclusion') in edge.get('premises',[]):
            # Do not guess which endpoint was intended; retain the object in diagnostics.
            events.append({'action':'quarantine_self_edge','object':edge});continue
        kept.append(edge)
    g['relations']=kept
    errors=C.graph.validate(g,units)
    soft=[e for e in errors if e.startswith('Unassigned claims:') or e=='Duplicate relation endpoints/type' or e.endswith(' missing branch question')]
    C.need(not [e for e in errors if e not in soft],'graph unusable: '+str([e for e in errors if e not in soft]))
    for branch in g['branches']:
        branch.setdefault('question_answered','')
    events += [{'action':'warning','message':e} for e in soft]
    # Unassigned claims remain in the full claim index and can still be located.
    g['_structural_diagnostics']=events
    out.clear();out.update(g)
    return events

def exact_whitespace_span(quote,text):
    """Allow only whitespace rendering changes; return actual source characters."""
    if not isinstance(quote,str) or not quote.strip():return None
    if quote in text:return quote
    pattern=r'\s+'.join(re.escape(t) for t in quote.split())
    matches=list(re.finditer(pattern,text))
    return matches[0].group(0) if len(matches)==1 else None

def mapping_output(out,data):
    units={u['id']:u for u in data['units']};rows=out['units'];events=copy.deepcopy(out.get('_structural_diagnostics',[]))
    C.need(len(rows)==len(units) and {r['original_id'] for r in rows}==set(units),'map unit coverage')
    for row in rows:
        u=units[row['original_id']];links=row['links']
        C.need(len(links)==len(u['citations']) and {x['citation_id'] for x in links}=={x['id'] for x in u['citations']},'map citation coverage')
        for link in links:
            C.need(isinstance(link.get('claims'),list),'map claims list required')
            if not link.get('no_claim_reason'):
                link['no_claim_reason']='' if link['claims'] else 'No assertion mapped; model supplied no explanation.'
            if isinstance(link['no_claim_reason'],list):link['no_claim_reason']='; '.join(map(str,link['no_claim_reason']))
            accepted=[];rejected=[]
            for claim in link['claims']:
                exact=exact_whitespace_span(claim.get('quote'),u['text'])
                if exact is None or not isinstance(claim.get('question'),str) or not claim['question'].strip():
                    rejected.append(claim)
                    events.append({'action':'quarantine_claim','original_id':u['id'],'citation_id':link['citation_id'],'object':copy.deepcopy(claim),'reason':'quote not found or question missing'})
                    continue
                if exact!=claim['quote']:events.append({'action':'restore_source_whitespace','original_id':u['id']})
                claim['quote']=exact
                C.need(isinstance(claim.get('question'),str) and claim['question'].strip(),'map question required')
                if not claim.get('search_query'):
                    claim['search_query']=claim['question'];events.append({'action':'question_as_search_query','original_id':u['id']})
                accepted.append(claim)
            link['claims']=accepted
            if rejected:link['no_claim_reason']+=' Unresolved mapping: '+str(len(rejected))+' assertion(s) quarantined; see structural diagnostics.'
    out['_structural_diagnostics']=events
    return events
