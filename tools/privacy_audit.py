"""Conservative pattern scan of the Git payload. Never prints matched secret values."""
import argparse,hashlib,json,re,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
PATTERNS={
 'workstation_path':r'/(?:Users|Volumes)/',
 'internal_endpoint':r'(?:agi|aigc|dev|jumper)\.sankuai\.com',
 'session_url':r'(?:chatgpt\.com/c/|local-chatgpt\x3a|gemini\.google\.com/app/[a-zA-Z0-9]{10,})',
 'private_key':r'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----',
 'openai_key':r'\bsk-(?:proj-)?[A-Za-z0-9_-]{24,}',
 'github_key':r'\b(?:gh[pousr]_[A-Za-z0-9]{25,}|github_pat_[A-Za-z0-9_]{30,})',
 'cloud_key':r'\bAKIA[A-Z0-9]{16}\b',
 'jwt':r'\beyJ[A-Za-z0-9_-]{15,}\.[A-Za-z0-9_-]{15,}\.[A-Za-z0-9_-]{15,}',
 'company_appid_file':r'friday_appid_[0-9]+',
 'assigned_appid':r'''(?i)\bapp[_-]?id\s*[=:]\s*["']?[A-Za-z0-9]{8,}''',
}
def scan():
    paths=subprocess.check_output(['git','ls-files','-co','--exclude-standard','-z'],cwd=ROOT).decode().split('\0')
    paths=sorted(set(p for p in paths if p));findings=[];total=0
    for rel in paths:
        p=ROOT/rel
        if not p.is_file():continue
        if p.is_symlink():findings.append({'path':rel,'kind':'symlink'});continue
        if p.name in ('.env','credentials.json','cookies.json') or p.suffix in ('.pem','.key'):
            findings.append({'path':rel,'kind':'credential_file'})
        raw=p.read_bytes();total+=len(raw)
        try:text=raw.decode('utf-8')
        except UnicodeDecodeError:continue
        for kind,pattern in PATTERNS.items():
            for m in re.finditer(pattern,text):findings.append({'path':rel,'line':text.count('\n',0,m.start())+1,'kind':kind})
    return {'status':'passed' if not findings else 'requires_review','files':len(paths),'bytes':total,
      'findings':findings,'scope':'Git tracked and unignored working-tree payload; pattern and path scan, not a guarantee against every possible secret.'}
def main():
    p=argparse.ArgumentParser();p.add_argument('--out',type=Path);a=p.parse_args();result=scan()
    if a.out:a.out.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2));raise SystemExit(bool(result['findings']))
if __name__=='__main__':main()
