"""Report-native graph contract. Structural validation is not semantic approval."""
import copy
import hashlib

def require(ok, message):
    if not ok:
        raise ValueError(message)

def keyed(rows, label):
    require(isinstance(rows,list),label+' must be an array')
    require(all(isinstance(x,dict) and isinstance(x.get('id'),str) and x['id'] for x in rows),label+' IDs')
    result={x['id']:x for x in rows}
    require(len(result)==len(rows),label+' duplicate IDs')
    return result

def validate_graph(graph, report):
    require(graph.get('report_id')==report['report_id'],'report identity mismatch')
    spans=keyed(report['spans'],'spans')
    text=''.join(x['text'] for x in report['spans'])
    require(hashlib.sha256(text.encode()).hexdigest()==report['sha256'],'report hash mismatch')
    claims=keyed(graph.get('claims'),'claims')
    branches=keyed(graph.get('branches'),'branches')
    relations=keyed(graph.get('relations'),'relations')
    require(bool(claims) and bool(branches),'empty graph')
    def anchors(obj):
        ids=obj.get('span_ids')
        require(isinstance(ids,list) and bool(ids) and len(ids)==len(set(ids)), 'missing/duplicate span anchors')
        require(set(ids)<=spans.keys(),'unknown span anchor')
        return ''.join(spans[i]['text'] for i in ids)
    for c in claims.values():
        require(isinstance(c.get('statement'),str) and bool(c['statement'].strip()),'empty claim')
        require(c.get('kind') in ['reported_fact','assumption','inference','proposal'],'invalid claim kind')
        require(isinstance(c.get('conditions'),list) and all(isinstance(s,str) for s in c['conditions']),'conditions array required')
        anchors(c)
    for b in branches.values():
        require(isinstance(b.get('question'),str) and bool(b['question'].strip()),'branch question required')
        ids=b.get('claim_ids')
        require(isinstance(ids,list) and bool(ids) and set(ids)<=claims.keys(),'branch dangling claim')
    seen=set()
    for r in relations.values():
        premises=r.get('premise_ids')
        require(isinstance(premises,list) and bool(premises) and len(set(premises))==len(premises),'joint premises invalid')
        require(set(premises)<=claims.keys() and r.get('conclusion_id') in claims,'relation dangling claim')
        require(r['conclusion_id'] not in premises,'self support')
        require(r.get('relation') in ['supports','qualifies','contrasts'],'relation type invalid')
        require(type(r.get('reconstructed')) is bool,'reconstructed flag required')
        signature=(tuple(sorted(premises)),r['conclusion_id'],r['relation'])
        require(signature not in seen,'duplicate relation')
        seen.add(signature)
        anchors(r)
    links=graph.get('citation_links')
    require(isinstance(links,list),'citation_links array required')
    for link in links:
        require(link.get('claim_id') in claims,'citation dangling claim')
        url=link.get('url')
        require(isinstance(url,str) and url.startswith(('http://','https://')),'invalid citation URL')
        # Join exact adjacent fragments to support URLs crossing segment boundaries.
        ids=link.get('span_ids',[])
        anchors(link)
        positions=[list(spans).index(i) for i in ids]
        require(positions==list(range(min(positions),max(positions)+1)),'citation spans must be contiguous in order')
        require(url in ''.join(spans[i]['text'] for i in ids),'URL absent from cited original')
    require(isinstance(graph.get('diagnostics'),list),'diagnostics array required')
    return graph

def evidence_context(graph, report, claim_ids, relation_ids=()):
    """Expand necessary premise closure without promoting a relation to verified."""
    validate_graph(graph,report)
    claims={x['id']:x for x in graph['claims']}
    relations={x['id']:x for x in graph['relations']}
    require(set(claim_ids)<=claims.keys(),'unknown requested claim')
    require(set(relation_ids)<=relations.keys(),'unknown requested relation')
    wanted=set(claim_ids)
    selected=set(relation_ids)
    for rid in selected:
        wanted.update(relations[rid]['premise_ids'])
        wanted.add(relations[rid]['conclusion_id'])
    changed=True
    while changed:
        before=(len(wanted),len(selected))
        for rid,r in relations.items():
            if r['conclusion_id'] in wanted and r['relation'] in ['supports','qualifies']:
                selected.add(rid)
                wanted.update(r['premise_ids'])
        changed=before!=(len(wanted),len(selected))
    cs=[c for c in graph['claims'] if c['id'] in wanted]
    rs=[r for r in graph['relations'] if r['id'] in selected]
    links=[l for l in graph['citation_links'] if l['claim_id'] in wanted]
    span_ids={i for o in cs+rs+links for i in o['span_ids']}
    return {'report_id':report['report_id'],'report_sha256':report['sha256'],
            'claims':copy.deepcopy(cs),'relations':copy.deepcopy(rs),'citation_links':copy.deepcopy(links),
            'original_spans':[copy.deepcopy(s) for s in report['spans'] if s['id'] in span_ids],
            'extraction_diagnostics':copy.deepcopy(graph['diagnostics']),
            'status':'original_attribution_not_verified'}

def pair_packet(query, reports, graphs, questions):
    require(len(reports)==2 and len({r['report_id'] for r in reports})==2,'two distinct reports required')
    require(set(graphs)=={r['report_id'] for r in reports},'graph/report set mismatch')
    nested=[]
    for report in reports:
        graph=graphs[report['report_id']]
        validate_graph(graph,report)
        nested.append({'report_id':report['report_id'],'sha256':report['sha256'],
                       'spans':copy.deepcopy(report['spans']),'graph':copy.deepcopy(graph)})
    return {'query':query,'report_order':[r['report_id'] for r in reports],
            'representation_notice':'Spans are lossless internal character chunks, not author paragraphs or page breaks. Join their text in order before judging broken URLs or layout. Extraction diagnostics describe our representation, not report defects.',
            'reports':nested,'comparison_questions':copy.deepcopy(questions)}
