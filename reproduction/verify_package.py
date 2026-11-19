"""Check the complete distribution without revealing or requiring credentials."""
from pathlib import Path
import hashlib
import json

ROOT=Path(__file__).resolve().parent

def main():
    manifest=ROOT/'PACKAGE_HASHES.json'
    entries=list(ROOT.rglob('*'))
    for p in entries:
        if p.is_symlink() or not (p.is_file() or p.is_dir()):
            raise ValueError('Package contains a symlink or non-regular entry: '+str(p.relative_to(ROOT)))
    hashes=json.loads(manifest.read_text(encoding='utf-8'))
    actual={str(p.relative_to(ROOT)) for p in entries if p.is_file() and p!=manifest}
    if actual!=set(hashes):raise ValueError('Package has added or missing files.')
    for rel,digest in hashes.items():
        p=ROOT/rel
        if p.is_symlink() or not p.resolve().is_relative_to(ROOT.resolve()):raise ValueError('Invalid package path: '+rel)
        if hashlib.sha256(p.read_bytes()).hexdigest()!=digest:raise ValueError('Checksum mismatch: '+rel)
    print(json.dumps({'status':'passed','files_verified':len(hashes)},indent=2))

if __name__=='__main__':main()
