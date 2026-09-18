"""Verify this handoff's bytes only. Does not verify runtime, signatures or claims."""
import hashlib
import json
import sys
from pathlib import Path

def verify(root):
    root = Path(root).resolve()
    manifest = json.loads((root/'MANIFEST.json').read_text(encoding='utf-8'))
    errors, seen = [], set()
    for row in manifest['files']:
        rel = row['path']
        path = (root/rel).resolve()
        if not path.is_relative_to(root) or rel in seen:
            errors.append({'path':rel,'error':'unsafe_or_duplicate_path'}); continue
        seen.add(rel)
        if not path.is_file():
            errors.append({'path':rel,'error':'missing'}); continue
        body = path.read_bytes()
        if len(body) != row['bytes'] or hashlib.sha256(body).hexdigest() != row['sha256']:
            errors.append({'path':rel,'error':'byte_mismatch'})
    actual = {p.relative_to(root).as_posix() for p in root.rglob('*') if p.is_file() and p.relative_to(root).as_posix() != 'MANIFEST.json' and '__pycache__' not in p.parts}
    for extra in sorted(actual-seen): errors.append({'path':extra,'error':'unmanifested_file'})
    return {'status':'HASHES_MATCH' if not errors else 'ERROR','checked_files':len(seen),
            'runtime_verified':False,'signature_verified':False,'errors':errors}

if __name__ == '__main__':
    result=verify(sys.argv[1] if len(sys.argv)>1 else Path(__file__).parent)
    print(json.dumps(result,ensure_ascii=False,indent=2))
    raise SystemExit(0 if result['status']=='HASHES_MATCH' else 1)
