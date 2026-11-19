"""Extract explicit benchmark source exclusions; never infer product requirements."""
import ast
import re
from urllib.parse import urlsplit

def policy(query):
    marker='During the research process, you are not allowed to view the following article and urls:'
    if marker not in query:
        if 'not allowed to view' in query:
            raise ValueError('unrecognized source restriction; requires review')
        return {'urls':[], 'titles':[]}
    suffix=query.split(marker,1)[1]
    match=re.search(r'\{.*?\}',suffix,re.S)
    if not match:raise ValueError('source restriction missing structured object')
    obj=ast.literal_eval(match.group())
    urls=obj.get('urls');title=obj.get('title')
    if not isinstance(urls,list) or not urls or not all(isinstance(u,str) and urlsplit(u).scheme in ('http','https') for u in urls):
        raise ValueError('invalid source exclusion URLs')
    if not isinstance(title,str) or not title.strip():raise ValueError('missing excluded title')
    return {'urls':urls,'titles':[title]}

def excluded(candidate, rules):
    def key(url):
        p=urlsplit(url);return (p.hostname or '').lower(),p.path.rstrip('/')
    def words(s):return ' '.join(re.findall(r'\w+',s.lower()))
    return key(candidate.get('url','')) in {key(u) for u in rules['urls']} or any(
        words(t) in words(candidate.get('title','')) for t in rules['titles'])
