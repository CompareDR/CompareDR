"""Resolve explicit/collapsed Markdown reference links without changing source text."""
import re

def key(label):return ' '.join(label.split()).casefold()

def enrich(text,doc,units):
    def code_at(pos):return any(b['kind']=='code' and b['start']<=pos<b['end'] for b in doc['blocks'])
    definitions={};duplicates=[];unresolved=[]
    pattern=re.compile(r'^ {0,3}\[([^\]\n]+)\]:\s*(?:<(https?://[^>\n]+)>|(https?://\S+))',re.M)
    for m in pattern.finditer(text):
        if code_at(m.start()):continue
        label=key(m[1]);group=2 if m[2] is not None else 3
        d={'label':m[1],'url':m[group],'start':m.start(group),'end':m.end(group),'definition_start':m.start(),'definition_end':m.end()}
        if label in definitions:
            duplicates.append({'label':label,'conflict':definitions[label]['url']!=d['url']})
            if definitions[label]['url']!=d['url']:raise ValueError('Conflicting reference definitions: '+label)
        else:definitions[label]=d
    added=[]
    refs=re.compile(r'(?<![\\!])\[([^\]\n]+)\]\[([^\]\n]*)\]')
    for b in doc['blocks']:
        if b['kind'] in ['code','whitespace']:continue
        code_spans=[(m.start(),m.end()) for m in re.finditer(r'(`+).*?\1',b['text'])]
        for m in refs.finditer(b['text']):
            if any(lo<=m.start()<hi for lo,hi in code_spans):continue
            label=key(m[2] or m[1]);d=definitions.get(label)
            if not d:
                unresolved.append({'label':label,'block_id':b['id'],'marker_start':b['start']+m.start()});continue
            cid=f"U{len(doc['citations'])+1:04d}"
            c={'id':cid,'block_id':b['id'],'url':d['url'],'start':d['start'],'end':d['end'],'format':'reference','reference_label':label,'marker_start':b['start']+m.start(),'marker_end':b['start']+m.end(),'definition_start':d['definition_start'],'definition_end':d['definition_end']}
            assert text[c['start']:c['end']]==c['url']
            assert text[c['marker_start']:c['marker_end']]==m[0]
            doc['citations'].append(c);b['citation_ids'].append(cid);added.append(c)
    blocks={b['id']:b for b in doc['blocks']}
    for u in units:
        if u['kind']=='table_row':
            parent=blocks[u['parent_id']];header=parent['rows'][0]
            for c in added:
                at=c['marker_start']
                if c['block_id']==parent['id'] and (u['start']<=at<u['end'] or header['start']<=at<header['end']):u['citation_ids'].append(c['id'])
        else:
            # Units' lists can alias their parent block; assign instead of append.
            u['citation_ids']=list(blocks[u['id']]['citation_ids'])
    doc['reference_diagnostics']={'definitions':len(definitions),'resolved_occurrences':len(added),'used_definitions':len({c['reference_label'] for c in added}),'unresolved':unresolved,'duplicates':duplicates,'supported_syntax':'explicit [label][id] and collapsed [id][] with single-line HTTP(S) definitions; shortcuts not supported'}
    assert ''.join(b['text'] for b in doc['blocks'])==text
    return doc,units
