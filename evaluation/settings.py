"""One configuration for request budgets, scheduler and published protocol."""
import json
import hashlib
import functools
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SYSTEMS = {'R1': 'OpenAI Web', 'R2': 'Gemini Web', 'R3': 'Claude Web',
           'R4': 'LongCat', 'R5': 'Kimi', 'R6': 'DuMate', 'R7': 'Qwen',
           'R9': 'GPT Researcher (GPT-5.5)', 'R10': 'MiniMax'}

def config():
    from provider_config import runtime_config
    c = runtime_config()
    if c['model'] != 'gpt-5.5' or c['verifier_model'] != 'deepseek-v4.1-flash':
        raise ValueError('Formal model roles changed; create a separately versioned run')
    for k in ('attempts', 'ds_attempts', 'workers', 'active_queries', 'gpt_rpm', 'deepseek_rpm'):
        if type(c[k]) is not int or c[k] < 1: raise ValueError(k)
    return c

@functools.lru_cache(maxsize=1)
def contract_hash():
    files=list(ROOT.glob('*.py'))+list((ROOT/'vendor').rglob('*.py'))+[ROOT/'runtime_config.json']
    hashes={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(files)}
    return hashlib.sha256(json.dumps(hashes,sort_keys=True).encode()).hexdigest()

def token_budget(name, cfg):
    prefix = 'readability_raw' if name.startswith('readability_raw_') else name.split('_')[0]
    return cfg['output_tokens'].get(prefix, cfg['output_tokens']['verifier'])

def language(prompt):
    for phrase in ('English JSON output.', 'English JSON.'):
        prompt = prompt.replace(phrase, '')
    return prompt + '\nPreserve the language of the original report in extracted descriptions and each report-specific contribution. Shared comparison descriptions use the common report language; if the reports differ in language, use the Query language for shared descriptions. Keep schema keys, IDs, enums and verbatim source quotations unchanged.'
