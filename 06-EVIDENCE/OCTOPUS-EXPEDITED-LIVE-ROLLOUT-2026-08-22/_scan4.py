from pathlib import Path
import json
root = Path(r"F:/backup/_ops/state")
hits=[]
for p in root.rglob("*"):
    if not p.is_file():
        continue
    n = p.name.lower()
    if any(k in n for k in ("writer", "lease", "heartbeat", "single-writer", "session")):
        hits.append(str(p))
print("hits", len(hits))
for h in hits[:60]:
    print(h)
lease = Path(r"F:/backup/06-EVIDENCE/OCTOPUS-EXPEDITED-LIVE-ROLLOUT-2026-08-22/_lease.json")
print("---lease---")
print(lease.read_text(encoding="utf-8")[:2500] if lease.exists() else "missing")
# also search renew helpers in rollout_ops
ops = Path(r"F:/backup/06-EVIDENCE/OCTOPUS-EXPEDITED-LIVE-ROLLOUT-2026-08-22/_rollout_ops.py")
t = ops.read_text(encoding="utf-8")
for i,l in enumerate(t.splitlines(),1):
    if any(k in l.lower() for k in ("writer", "heartbeat", "renew", "lease", "allow_live")):
        print(f"{i}: {l[:160]}")
