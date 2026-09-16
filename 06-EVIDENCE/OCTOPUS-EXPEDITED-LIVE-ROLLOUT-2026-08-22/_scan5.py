from pathlib import Path
import json, time
lock = Path(r"F:/backup/_ops/state/locks/octopus-writer.lock")
d = json.loads(lock.read_text(encoding="utf-8"))
# redact nothing secret expected
print(json.dumps(d, indent=2, default=str))
now = time.time()
exp = float(d.get("expires_at") or 0)
print("now", now, "expires_at", exp, "remaining_h", (exp-now)/3600 if exp else None)
# find renew heartbeat helpers
import re
ops = Path(r"F:/backup/_ops")
for p in ops.rglob("*.py"):
    if "__pycache__" in str(p) or "_bak" in str(p):
        continue
    try:
        t = p.read_text(encoding="utf-8", errors="replace")
    except Exception:
        continue
    if "octopus-writer.lock" in t or "renew_heartbeat" in t or "writer_lock" in t and "expires_at" in t:
        if "def " in t:
            for i,l in enumerate(t.splitlines(),1):
                if any(k in l for k in ["octopus-writer.lock", "renew_heartbeat", "def renew", "def heartbeat", "expires_at", "allow_live_write"]):
                    if "def " in l or "octopus-writer" in l or "renew" in l.lower():
                        print(f"{p}:{i}: {l[:140]}")
