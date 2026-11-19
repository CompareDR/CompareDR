"""Deployment configuration only; keys are read at request time, never serialized."""
import importlib.util
import json
import os
from pathlib import Path
from urllib.parse import urlsplit

ROOT=Path(__file__).resolve().parent

def endpoint(name):
    value=os.environ.get(name, 'https://unconfigured.invalid/chat/completions')
    u=urlsplit(value)
    if u.scheme!='https' or not u.hostname or u.username or u.password or u.query or u.fragment:
        raise ValueError(name+' must be an HTTPS URL without embedded credentials or query parameters')
    return value

def api_key(role='judge'):
    name='COMPAREDR_VERIFIER_API_KEY' if role=='verifier' else 'COMPAREDR_JUDGE_API_KEY'
    value=os.environ.get(name,'').strip()
    if not value:raise RuntimeError('Missing '+name+'; configure it outside the repository')
    return value

def runtime_config():
    c=json.loads((ROOT/'runtime_config.json').read_text())
    c.update(endpoint=endpoint('COMPAREDR_JUDGE_ENDPOINT'),verifier_endpoint=endpoint('COMPAREDR_VERIFIER_ENDPOINT'))
    return c

def search_endpoint():
    # The fingerprint changes when an adapter changes, without exposing its local path.
    import hashlib
    p=os.environ.get('COMPAREDR_SEARCH_ADAPTER')
    return 'adapter:'+hashlib.sha256(Path(p).read_bytes()).hexdigest() if p else 'adapter:unconfigured'

def search_request(query,top_k,timeout):
    """User adapter exports search(query, top_k, timeout) -> list of URL/title/snippet objects."""
    p=os.environ.get('COMPAREDR_SEARCH_ADAPTER')
    if not p:raise RuntimeError('Set COMPAREDR_SEARCH_ADAPTER to an external search adapter')
    spec=importlib.util.spec_from_file_location('comparedr_search_adapter',p)
    adapter=importlib.util.module_from_spec(spec);spec.loader.exec_module(adapter)
    try:rows=adapter.search(query=query,top_k=top_k,timeout=timeout)
    except Exception as exc:
        # Do not leak provider exceptions containing credentials into evidence logs.
        raise RuntimeError('Search adapter failed ('+type(exc).__name__+')') from None
    if not isinstance(rows,list):raise ValueError('Search adapter must return a list')
    result=[]
    for row in rows[:top_k]:
        if not isinstance(row,dict) or urlsplit(row.get('url','')).scheme not in ('http','https'):
            raise ValueError('Search result must contain an http(s) URL')
        result.append({k:str(row.get(k,'')) for k in ('url','title','snippet')})
    return result

def require_online():
    for role in ('judge','verifier'):
        if 'unconfigured.invalid' in endpoint('COMPAREDR_'+role.upper()+'_ENDPOINT'):
            raise RuntimeError('Configure the '+role+' endpoint before --execute')
        api_key(role)
    if not os.environ.get('COMPAREDR_SEARCH_ADAPTER'):
        raise RuntimeError('Configure a search adapter before --execute; evidence acquisition is not optional')
