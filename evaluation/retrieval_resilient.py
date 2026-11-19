"""Bounded source acquisition. Adapted from serial3 retrieval and pinned-v1.

No legacy workflow imports. Failed attempts are recorded, never cached as success.
"""
import hashlib
import http.client
import ipaddress
import json
import re
import socket
import ssl
import subprocess
import time
import threading
import contextlib
import queue
import urllib.parse
import urllib.request
from html.parser import HTMLParser
from pathlib import Path
from run_extract import ROOT,config,transport

BASE=Path(__file__).resolve().parent/'evidence'
_budget=threading.local()
@contextlib.contextmanager
def deadline_scope(seconds):
    old=getattr(_budget,'deadline',None);_budget.deadline=time.monotonic()+seconds
    try:yield
    finally:_budget.deadline=old
def remaining(cap=12):
    deadline=getattr(_budget,'deadline',None)
    left=cap if deadline is None else min(cap,deadline-time.monotonic())
    if left<=0:raise TimeoutError('acquisition deadline reached')
    return left
CONFIG={'version':'resilient-fetch-formal-v2','byte_cap':12000000,'text_cap':180000,
        'chunk_chars':1000,'source':'serper-search','top_k':8,
        'search_endpoint':__import__('provider_config').search_endpoint()}

def cache_key(obj):return transport.digest(obj)
def save_attempt(kind,key,out):
    transport.save(BASE/kind/key/(str(time.time_ns())+'.json'),out)
    if out['status']=='completed':transport.freeze(BASE/kind/key/'success.json',out)
    return out

def search(query):
    from provider_config import search_request
    body={'query':query,'top_k':CONFIG['top_k']}
    key=cache_key({'body':body,'endpoint':CONFIG['search_endpoint']})
    cached=BASE/'search'/key/'success.json'
    if cached.exists():return transport.load(cached)
    out={'request':body,'utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime())}
    try:
        rows=search_request(query, CONFIG['top_k'], remaining(45) if 'remaining' in globals() else 45)
        out.update(status='completed',results=rows)
    except Exception as exc:out.update(status='failed',error=str(exc))
    return save_attempt('search',key,out)

class HTMLText(HTMLParser):
    def __init__(self):super().__init__();self.parts=[];self.skip=0
    def handle_starttag(self,tag,attrs):
        if tag in ['script','style','noscript','svg']:self.skip+=1
    def handle_endtag(self,tag):
        if tag in ['script','style','noscript','svg']:self.skip=max(0,self.skip-1)
    def handle_data(self,data):
        if not self.skip and data.strip():self.parts.append(data.strip())

def decode_text(raw,content_type):
    """Plain source code must not pass through an HTML parser."""
    mime=content_type.split(';',1)[0].strip().lower()
    match=re.search(r'charset\s*=\s*[\"\']?([^;\s\"\']+)',content_type,re.I)
    text=raw.decode(match.group(1) if match else 'utf-8',errors='strict')
    html=mime in ('text/html','application/xhtml+xml')
    if not mime:
        html=bool(re.match(r'\s*(?:<!doctype\s+html|<html\b)',text,re.I))
    if html:
        decoder=HTMLText();decoder.feed(text)
        return '\n'.join(decoder.parts),'html-text-v1'
    if mime and not (mime.startswith('text/') or mime in ('application/json','application/javascript','application/typescript')):
        raise ValueError('nontext source')
    return text,'plain-text-v2'

def segment_prefix(raw_digest,pages,parser):
    # Same bytes parsed differently must never alias old evidence fragment IDs.
    parsed_digest=cache_key({'pages':pages,'parser':parser})[:16]
    return raw_digest[:16]+'.T'+parsed_digest

def resolve(host,port):
    # libc DNS lookup has no per-call timeout; a daemon avoids blocking query exit.
    result=queue.Queue(maxsize=1)
    def lookup():
        try:result.put((True,socket.getaddrinfo(host,port,type=socket.SOCK_STREAM)))
        except Exception as ex:result.put((False,ex))
    threading.Thread(target=lookup,daemon=True).start()
    try:ok,value=result.get(timeout=remaining(12))
    except queue.Empty:raise TimeoutError('DNS acquisition deadline')
    if not ok:raise value
    return value

def connection(url):
    p=urllib.parse.urlsplit(url)
    if p.scheme not in ['http','https'] or not p.hostname or p.username or p.password or p.port not in [None,80,443]:
        raise ValueError('invalid public URL')
    port=p.port or (443 if p.scheme=='https' else 80)
    answers=resolve(p.hostname,port);remaining()
    if not answers or not all(ipaddress.ip_address(a[4][0]).is_global for a in answers):raise ValueError('nonpublic address')
    answer=answers[0]
    class Pinned(http.client.HTTPConnection):
        def connect(self):
            sock=socket.socket(answer[0],answer[1],answer[2]);sock.settimeout(self.timeout)
            try:
                sock.connect(answer[4])
                self.sock=ssl.create_default_context().wrap_socket(sock,server_hostname=p.hostname) if p.scheme=='https' else sock
            except Exception:sock.close();raise
    return Pinned(p.hostname,port,timeout=remaining(12)),p

def _fetch(url,forbidden_urls=()):
    def canonical(u):
        p=urllib.parse.urlsplit(u)
        return (p.hostname or '').lower(),p.path.rstrip('/')
    blocked={canonical(u) for u in forbidden_urls}
    key=cache_key({'url':url,'config':CONFIG,'forbidden_urls':sorted(forbidden_urls)})
    cached=BASE/'sources'/key/'success.json'
    if cached.exists():return transport.load(cached)
    out={'requested_url':url,'utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'segments':[],'redirects':[]}
    current=url
    try:
        for hop in range(8):
            if canonical(current) in blocked:raise ValueError('source withheld by task')
            con,p=connection(current)
            try:
                target=urllib.parse.urlunsplit(('','',p.path or '/',p.query,''))
                con.request('GET',target,headers={'User-Agent':'Mozilla/5.0','Accept-Encoding':'identity'})
                response=con.getresponse()
                out.update(http_status=response.status,final_url=current)
                if response.status in [301,302,303,307,308]:
                    location=response.getheader('Location')
                    if not location or hop==7:raise ValueError('invalid redirect')
                    current=urllib.parse.urljoin(current,location);out['redirects'].append(current);continue
                if not 200<=response.status<300:raise ValueError('HTTP '+str(response.status))
                chunks=[];size=0
                while size<=CONFIG['byte_cap']:
                    if con.sock:con.sock.settimeout(remaining(12))
                    remaining();part=response.read(min(65536,CONFIG['byte_cap']+1-size))
                    if not part:break
                    chunks.append(part);size+=len(part)
                raw=b''.join(chunks)
                if len(raw)>CONFIG['byte_cap']:raise ValueError('source too large')
                content_type=response.getheader('Content-Type','')
                break
            finally:con.close()
        digest=hashlib.sha256(raw).hexdigest()
        path=BASE/'raw'/digest;path.parent.mkdir(parents=True,exist_ok=True)
        if path.exists():assert path.read_bytes()==raw
        else:path.write_bytes(raw)
        out.update(content_sha256=digest,raw_path=str(path),content_type=content_type)
        if raw.lstrip().startswith(b'%PDF'):
            proc=subprocess.run(['pdftotext','-layout',str(path),'-'],capture_output=True,text=True,timeout=remaining(35))
            if proc.returncode:raise ValueError('PDF parse failed')
            pages=proc.stdout.split('\f')
            out.update(parser='pdftotext-layout',formula_table_reliability='unverified',visual_checked=False)
        else:
            body,parser=decode_text(raw,content_type)
            pages=[body];out['parser']=parser
            if any(t in pages[0][:2000].lower() for t in ['verify you are human','just a moment...','access denied','checking your browser']):raise ValueError('access challenge')
        if sum(map(len,pages))<300:raise ValueError('insufficient parsed body')
        text_remaining=CONFIG['text_cap']
        prefix=segment_prefix(digest,pages,out['parser'])
        for page,body in enumerate(pages,1):
            part=body[:text_remaining];text_remaining-=len(part)
            for start in range(0,len(part),CONFIG['chunk_chars']):
                out['segments'].append({'id':prefix+f'.P{page}.C{start}',
                    'text':part[start:start+CONFIG['chunk_chars']],'page':page if out['parser']=='pdftotext-layout' else None})
        out.update(status='completed',truncated=sum(map(len,pages))>CONFIG['text_cap'])
    except Exception as exc:out.update(status='failed',error=str(exc),segments=[])
    return save_attempt('sources',key,out)

# Limit load by source host, share concurrent requests, and expire transient failures.
_guard=threading.Lock();_hosts={};_keys={};_recent={}
def fetch(url,forbidden_urls=()):
    key=cache_key({'url':url,'forbidden_urls':sorted(forbidden_urls),'config':CONFIG})
    host=urllib.parse.urlsplit(url).hostname
    with _guard:
        lock=_keys.setdefault(key,threading.Lock());semaphore=_hosts.setdefault(host,threading.BoundedSemaphore(2))
    if not lock.acquire(timeout=remaining(180)):raise TimeoutError('source singleflight deadline')
    try:
        previous=_recent.get(key)
        if previous and time.monotonic()-previous[0]<60:return previous[1]
        if not semaphore.acquire(timeout=remaining(180)):raise TimeoutError('source host deadline')
        try:
            result=_fetch(url,forbidden_urls)
            if result['status']=='failed' and any(x in result.get('error','').lower() for x in ('timed out','http 429','http 502','http 503','http 504')):
                time.sleep(min(.5,remaining()));result=_fetch(url,forbidden_urls)
        finally:semaphore.release()
        _recent[key]=(time.monotonic(),result)
        return result
    finally:lock.release()
