#!/usr/bin/env python3
"""Loop: mirror freshness (run daily after 03:30Z push). Read-only."""
import json, subprocess, time
from pathlib import Path
EV = Path("F:/backup/09-LANES/S2-MATURITY-EXEC-20260917/evidence/MIRROR-FRESHNESS.jsonl")
def sh(cmd):
    return subprocess.run(["ssh","-o","BatchMode=yes","-i",str(Path.home()/".ssh/id_ed25519"),
                           "root@192.168.0.182", cmd], capture_output=True, text=True, timeout=30).stdout
led = sh("cat /var/lib/mirror-138/state/ledger.json")
try: d = json.loads(led)
except Exception: d = {}
q = sh("ls -t /var/lib/mirror-138/quarantine/ 2>/dev/null | head -1")
row = {"ts_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
       "sequence": d.get("sequence"), "sha16": str(d.get("last_manifest_sha256"))[:16],
       "updated_at": d.get("updated_at_utc"), "newest_quarantine": q.strip()[:60] or None}
age_h = None
try:
    import datetime as dt
    age_h = (dt.datetime.now(dt.timezone.utc) - dt.datetime.strptime(d["updated_at_utc"], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=dt.timezone.utc)).total_seconds()/3600
except Exception: pass
row["age_hours"] = round(age_h,1) if age_h is not None else None
row["class"] = "STALE_ALERT" if (age_h is None or age_h > 48) else "FRESH"
EV.write_text((EV.read_text() if EV.exists() else "") + json.dumps(row) + "\n", encoding="utf-8")
print(json.dumps(row))
