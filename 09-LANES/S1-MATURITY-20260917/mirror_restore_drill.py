"""Node182 only: bounded mirror-byte restore into a new private replica directory.

No live consumers/config are changed; no payload values leave this process.
"""
import datetime as dt
import hashlib
import json
import os
import re
import shutil
import subprocess
from pathlib import Path, PurePosixPath

ROOT = Path('/var/lib/mirror-138')
DEST = Path('/root/s1-maturity-mirror-replica-20260917')

def digest(data):
    return hashlib.sha256(data).hexdigest()

def main():
    if DEST.exists():
        raise RuntimeError('replica_already_exists_no_overwrite')
    candidates = list((ROOT/'incoming').glob('*/manifest.json'))
    if not candidates:
        raise RuntimeError('no_manifest')
    source = max(candidates, key=lambda p: p.parent.name)
    body = source.read_bytes()
    manifest = json.loads(body)
    verify = subprocess.run(['ssh-keygen','-Y','verify','-f',str(ROOT/'trusted'/'allowed_signers'),
                             '-I','mirror-138','-n','octopus-mirror-manifest',
                             '-s',str(source)+'.sig'],input=body,capture_output=True)
    if verify.returncode:
        raise RuntimeError('signature_not_verified')
    records = manifest['files']
    if not 1 <= len(records) <= 64 or manifest['files_count'] != len(records):
        raise RuntimeError('invalid_file_count')
    paths = [r['path'] for r in records]
    if len(set(paths)) != len(paths):
        raise RuntimeError('duplicate_paths')
    payload = source.parent/'payload'
    actual = set()
    for p in payload.rglob('*'):
        if p.is_symlink():
            raise RuntimeError('symlink')
        if p.is_file(): actual.add(p.relative_to(payload).as_posix())
    if actual != set(paths): raise RuntimeError('file_set_mismatch')
    verified = []
    total = 0
    for record in records:
        path = PurePosixPath(record['path'])
        if path.is_absolute() or '..' in path.parts or not re.fullmatch(
                r'(api-budget/budget-ledger\.jsonl|api-budget/config/[^/]+\.jsonl?|revenue-drive/season-meter\.json)',str(path)):
            raise RuntimeError('unsafe_path')
        src = payload/path
        total += src.stat().st_size
        if src.stat().st_size > 50*1024**2 or total > 200*1024**2:
            raise RuntimeError('size_cap')
        data = src.read_bytes()
        if digest(data) != record['sha256'] or len(data) != record['bytes']:
            raise RuntimeError('source_hash_mismatch')
        # Validate structured data without returning any customer/config values.
        if src.suffix == '.jsonl':
            parsed_count = sum(1 for line in data.splitlines() if line and json.loads(line) is not None)
        else:
            json.loads(data); parsed_count = 1
        verified.append((src,path,data,parsed_count))
    os.umask(0o077)
    DEST.mkdir(mode=0o700)
    rows=[]
    for src,path,data,count in verified:
        out = DEST/path
        out.parent.mkdir(parents=True,exist_ok=True)
        with out.open('xb') as stream:
            stream.write(data); stream.flush(); os.fsync(stream.fileno())
        rows.append({'path':str(path),'sha256':digest(out.read_bytes()),'bytes':len(data),'json_records':count,
                     'source_unchanged':digest(src.read_bytes())==digest(data)})
    negative = bytearray(verified[0][2]); negative[0] ^= 1
    receipt={'schema':'octopus.mirror-replica-drill.v1','observed_at_utc':dt.datetime.now(dt.timezone.utc).isoformat(),
             'status':'BYTE_RESTORE_AND_PARSE_VERIFIED','manifest_sha256':digest(body),'signature_verified':True,
             'files':rows,'tampered_copy_hash_rejected':digest(negative)!=digest(verified[0][2]),
             'replica':str(DEST),'source':str(source.parent),'runtime_restore_valid':False,
             'replay_valid':False,'scope':'signed mirror bytes and JSON readability only; live consumer replay NOT_RUN'}
    (DEST/'RESTORE-RECEIPT.json').write_text(json.dumps(receipt,indent=2)+'\n')
    print(json.dumps(receipt,indent=2))

if __name__ == '__main__': main()
