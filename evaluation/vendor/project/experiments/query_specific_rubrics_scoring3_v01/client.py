"""Isolated API cache: language-specific technical retries, no score-based retries."""
import concurrent.futures as cf
import hashlib
import json
import os
import re
import threading
import time
import urllib.request
import uuid
from pathlib import Path

BASE = Path(__file__).resolve().parent
ROOT = BASE.parents[1]


def load(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def digest(x):
    return hashlib.sha256(json.dumps(x, ensure_ascii=False, sort_keys=True).encode()).hexdigest()


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def save(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + f'.{os.getpid()}.{threading.get_ident()}.{uuid.uuid4().hex}.tmp')
    tmp.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    tmp.replace(path)


def check(condition, message):
    if not condition:
        raise ValueError(message)


def freeze(path, value):
    if Path(path).exists():
        check(load(path) == value, 'frozen input changed: ' + str(path))
    else:
        save(path, value)


def config():
    from provider_config import runtime_config
    return runtime_config() | {'max_tokens': 9000, 'temperature': None, 'new_search_budget': 0}


class Client:
    def call(self, name, prompt, data, validator, language='en', category='scoring'):
        c = config()
        key = __import__('provider_config').api_key('judge')
        body = {'model': c['model'], 'reasoning_effort': c['reasoning_effort'],
                'max_tokens': c['max_tokens'], 'stream': False,
                'messages': [{'role': 'system', 'content': prompt},
                             {'role': 'user', 'content': json.dumps(data, ensure_ascii=False)}]}
        identity = {'name': name, 'category': category, 'language': language,
                    'body': body, 'endpoint': c['endpoint'], 'config': c,
                    'implementation': sha(Path(__file__))}
        call_key = digest(identity)
        folder = BASE / 'calls' / call_key
        freeze(folder / 'identity.json', identity)
        if (folder / 'success.json').exists():
            out = load(folder / 'success.json')
            validator(out['result'], data)
            return out
        check(os.environ.get('MULTIDIM_OFFLINE') != '1', 'offline cache miss')
        count = len(list(folder.glob('request_*.json')))
        prior = None
        error = 'attempt budget exhausted'
        if count and (folder / f'error_{count-1}.json').exists():
            error = load(folder / f'error_{count-1}.json')['error']
        if count and (folder / f'response_{count-1}.json').exists():
            try:
                prior = load(folder / f'response_{count-1}.json')['raw']['choices'][0]['message']['content']
            except (KeyError, IndexError):
                pass
        for attempt in range(count, c['attempts']):
            request_body = dict(body)
            if prior:
                repair = ('Repair only this output-contract error. Keep the same criteria; do not retry to obtain a preferred score: '
                          if language == 'en' else '仅修复以下输出结构错误，保持评分标准，不因分数或胜负重试：')
                request_body['messages'] = body['messages'] + [
                    {'role': 'assistant', 'content': prior}, {'role': 'user', 'content': repair + error}]
            save(folder / f'request_{attempt}.json', request_body)
            started = time.time()
            try:
                req = urllib.request.Request(c['endpoint'], json.dumps(request_body).encode(),
                                             {'Content-Type': 'application/json', 'Authorization': 'Bearer ' + key})
                with urllib.request.build_opener(urllib.request.ProxyHandler({})).open(
                        req, timeout=c['request_timeout_seconds']) as response:
                    raw = json.load(response)
                raw = json.loads(json.dumps(raw).replace(key, '[REDACTED]'))
                save(folder / f'response_{attempt}.json', {
                    'raw': raw, 'seconds': time.time()-started,
                    'utc': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())})
                choice = raw['choices'][0]
                check(choice.get('finish_reason') != 'length', 'truncated response')
                prior = choice['message']['content']
                out = json.loads(re.sub(r'^```(?:json)?\s*|\s*```$', '', prior.strip()))
                validator(out, data)
                accepted = {'result': out, 'call_key': call_key, 'usage': raw.get('usage'),
                            'returned_model': raw.get('model'), 'accepted_attempt': attempt}
                save(folder / 'success.json', accepted)
                print(name, 'OK', flush=True)
                return accepted
            except Exception as ex:
                error = str(ex).replace(key, '[REDACTED]')
                save(folder / f'error_{attempt}.json', {'error': error, 'seconds': time.time()-started})
                print(name, 'ERROR', attempt+1, error[:170], flush=True)
        raise RuntimeError(name + ': ' + error)


def batch(jobs, status_name):
    path = BASE / status_name
    status = load(path) if path.exists() else {}
    with cf.ThreadPoolExecutor(max_workers=config()['workers']) as pool:
        pending = {pool.submit(job): name for name, job in jobs}
        for f in cf.as_completed(pending):
            name = pending[f]
            try:
                f.result()
                status[name] = {'state': 'completed'}
            except Exception as ex:
                status[name] = {'state': 'failed', 'error': str(ex)}
            save(path, status)
    return status
