from pathlib import Path
# find how heartbeat was renewed in prior scripts
for p in [
 Path(r"F:/backup/06-EVIDENCE/OCTOPUS-EXPEDITED-LIVE-ROLLOUT-2026-08-22/_rollout_ops.py"),
 Path(r"F:/backup/_ops/writer_lease.py"),
]:
 t=p.read_text(encoding='utf-8')
 print('====',p.name)
 if 'heartbeat' in t:
  for i,l in enumerate(t.splitlines(),1):
   if 'heartbeat' in l.lower() or 'expires_at' in l or 'allow_live' in l:
    print(f'{i}: {l[:160]}')
# search evidence dir for renew patterns
ev=Path(r"F:/backup/06-EVIDENCE/OCTOPUS-EXPEDITED-LIVE-ROLLOUT-2026-08-22")
for p in ev.glob("*.py"):
 t=p.read_text(encoding='utf-8',errors='replace')
 if 'heartbeat' in t or 'writer.lock' in t:
  print('SCRIPT', p.name)
  for i,l in enumerate(t.splitlines(),1):
   if 'heartbeat' in l.lower() or 'writer.lock' in l or 'allow_live' in l:
    print(f'  {i}: {l[:140]}')
# also owner override evidence
ov=Path(r"F:/backup/06-EVIDENCE/OCTOPUS-OWNER-OVERRIDE-GROK-2026-08-22")
if ov.exists():
 print('OVERRIDE FILES:')
 for f in sorted(ov.iterdir()):
  print(' ',f.name)
