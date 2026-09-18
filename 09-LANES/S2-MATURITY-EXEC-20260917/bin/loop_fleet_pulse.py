#!/usr/bin/env python3
"""Loop: fleet health pulse every 6h (read-only, from the canonical heartbeat)."""
import json, re, time
from pathlib import Path
HB = Path("F:/backup/06-EVIDENCE/FLEET-HEARTBEAT-CANONICAL.md")
EV = Path("F:/backup/09-LANES/S2-MATURITY-EXEC-20260917/evidence/FLEET-PULSE.jsonl")
lines = HB.read_text(encoding="utf-8", errors="replace").splitlines()[-60:]
pat = re.compile(r"`([0-9T:\-Z]+)`\s+(\d+)\s+load1=([\w.]+)\s+leaf=(\w+)")
latest = {}
for l in lines:
    m = pat.search(l)
    if m:
        latest[m.group(2)] = {"ts": m.group(1), "load1": m.group(3), "leaf": m.group(4)}
alerts = [n for n, v in latest.items() if v["load1"] not in ("None",) and float(v["load1"]) > 4]
silent = [n for n in ("138","180","182","100","160","193","114") if n not in latest]
row = {"ts_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "nodes": latest,
       "ALERTS_high_load": alerts, "NODE_SILENT": silent}
EV.write_text((EV.read_text() if EV.exists() else "") + json.dumps(row) + "\n", encoding="utf-8")
print(json.dumps(row)[:400])
