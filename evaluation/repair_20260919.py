"""Versioned runtime repair overlay; original frozen source files remain unchanged."""
import copy,json,re,sys,time,os,signal,subprocess,concurrent.futures,shutil,threading,unicodedata
from pathlib import Path
ROOT=Path(__file__).resolve().parent

def span(quote,text):
    if not isinstance(quote,str) or not quote.strip():return None
    if quote in text:return quote
    # Whitespace only. NFKC would conflate x² and x2; punctuation may be semantic.
    pattern=r'\s+'.join(re.escape(t) for t in quote.split())
    matches=list(re.finditer(pattern,text))
    return matches[0].group(0) if len(matches)==1 else None

def packed(data,C):
    out=copy.deepcopy(data);ep={};cp={}
    for gp in out['guide_packets']:
        ids=[]
        for card in gp.pop('verification_cards'):
            c=copy.deepcopy(card);mapping={};refs=[]
            for e in c.pop('evidence'):
                eid='E'+C.T.digest(e);ep[eid]=e;mapping[e['id']]=eid;refs.append(eid)
            for branch in ('fact','citation'):
                if c.get('result') and branch in c['result']:
                    c['result'][branch]['evidence_ids']=[mapping[i] for i in c['result'][branch]['evidence_ids']]
            # Preserve EVERY occurrence, including same legacy ID / different payload.
            c['evidence_refs']=refs;cid=c['check_id']
            C.need(cid not in cp or cp[cid]==c,'conflicting check ID');cp[cid]=c;ids.append(cid)
        gp['verification_card_ids']=ids
    out['verification_card_pool']=list(cp.values());out['evidence_pool']=[{'evidence_ref':k,'source':v} for k,v in ep.items()]
    return out

def readability(out,data,old):
    texts={r['report_id']:r['text'] for r in data['reports']};aliases=dict(zip(('A','B'),texts));all_seen=set();diag=[]
    for row in out.get('judgments',[]):
        kept=[]
        for e in row.get('evidence',[]):
            rid=aliases.get(e.get('report_id'),e.get('report_id'))
            if rid not in texts:raise ValueError('Unknown report identity')
            q=e.get('quote');actual=span(q,texts[rid])
            if actual:
                kept.append(dict(e,report_id=rid,quote=actual));all_seen.add(rid)
            else:
                # Keep prose as unverified commentary, NOT an authenticated quotation.
                row.setdefault('unverified_excerpt_diagnostics',[]).append(e)
                diag.append({'guide_id':row.get('guide_id'),'report_id':rid,'action':'quarantine_unmatched_excerpt'})
        row['evidence']=kept
    # Never borrow another guide's evidence to make validation appear successful.
    old(out,data)
    if diag:out.setdefault('_structural_diagnostics',[]).extend(diag)

def install():
    import pipeline as P
    C=P.C
    C.pw.packed=lambda data:packed(data,C)
    old=P.RR.validate;P.RR.validate=lambda o,d:readability(o,d,old)
    P.compat.exact_whitespace_span=span
    original=C.normalize
    def normalize(o):
        o=original(o)
        if not any(k in o for k in ('fact','citation')):return o
        for key in ('fact','citation'):
            if key not in o:continue
            for field in ('supports','limits'):
                v=o[key].get(field)
                if not isinstance(v,str):
                    o[key][field]='' if v is None else json.dumps(v,ensure_ascii=False)
                    o.setdefault('_structural_diagnostics',[]).append({'action':'normalize_scope_field','branch':key,'field':field,'original':v})
        if not o.get('task_effect'):
            o['task_effect']='Not separately specified by verifier; no additional task-level inference.'
            o.setdefault('_structural_diagnostics',[]).append({'action':'missing_optional_task_effect'})
        return o
    C.normalize=normalize
    # Cache creation is first-success-wins, not equality of independently timestamped responses.
    retr=P.A.R;oldsave=retr.save_attempt;lock=threading.Lock()
    def save_attempt(kind,key,out):
        with lock:
            p=retr.BASE/kind/key/'success.json'
            if p.exists():
                retr.transport.save(retr.BASE/kind/key/(str(time.time_ns())+'.json'),out)
                return retr.transport.load(p)
            return oldsave(kind,key,out)
    retr.save_attempt=save_attempt

if __name__=='__main__':
    raise SystemExit('Compatibility helpers only. Use the formal run.py entry; no historical retry escalation.')
