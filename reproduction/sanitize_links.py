"""Deterministically remove tracking query parameters, preserving source links."""
import re

TRACKING=re.compile(r'(?i)^(?:utm_[a-z0-9_]+|srsltid|fbclid|gclid|dclid|msclkid|mc_eid|igshid)$')
URL=re.compile(r'''https?://[^\s<>"\\\]\)]+''')

def clean_text(text):
    removed={}
    def clean(match):
        url=match.group()
        if '?' not in url:return url
        base,query=url.split('?',1);query,mark,fragment=query.partition('#')
        parts=query.split('&');kept=[]
        for part in parts:
            key=part.split('=',1)[0]
            if TRACKING.fullmatch(key):removed[key.lower()]=removed.get(key.lower(),0)+1
            else:kept.append(part)
        if len(kept)==len(parts):return url
        return base+('?'+'&'.join(kept) if kept else '')+(mark+fragment if mark else '')
    return URL.sub(clean,text),removed
