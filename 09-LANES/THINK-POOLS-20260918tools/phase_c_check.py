#!/usr/bin/env python3
"""Phase C proof — classify the LIVE health record and produce routing order.

Read-only. Prints the declared status next to the derived truth so the gap is
visible, plus the routing order and any provider that came back from the dead.
"""
import json
import pathlib
import sys

# When piped over ssh there is no __file__, so the module directory is explicit.
sys.path.insert(0, "/home/ari/ofn/state/fleet-compute")
import think_pool as tp  # noqa: E402

BASE = pathlib.Path("/home/ari/ofn/state/api-budget")
HEALTH = BASE / "config" / "provider-health.jsonl"
LEDGER = BASE / "budget-ledger.jsonl"

rows = []
for line in HEALTH.read_text(errors="replace").splitlines():
    line = line.strip()
    if line:
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError:
            pass
if not rows:
    print("no health rows")
    raise SystemExit(1)

latest = rows[-1]
record = latest.get("record") or {}
prev_record = (rows[-2].get("record") or {}) if len(rows) > 1 else {}

states = tp.classify_all(record)
prev_states = tp.classify_all(prev_record)

usage = {}
for line in LEDGER.read_text(errors="replace").splitlines():
    line = line.strip()
    if not line:
        continue
    try:
        r = json.loads(line)
    except json.JSONDecodeError:
        continue
    prov = str(r.get("provider") or "unknown")
    usage[prov] = usage.get(prov, 0) + 1

print(f"health record: {latest.get('at')}  (rows={len(rows)})")
print()
print(f"{'provider':<20} {'declared':<8} {'derived':<10} {'paid':<6} reason")
print("-" * 78)
for name in sorted(states):
    declared = str((record.get(name) or {}).get("status", "?"))
    s = states[name]
    flag = ""
    if declared == "LIVE" and s["state"] != "LIVE":
        flag = "   <== declared LIVE but is NOT routable"
    print(f"{name:<20} {declared:<8} {s['state']:<10} {str(s.get('paid')):<6} {s['reason']}{flag}")

print()
order = tp.routing_order(states, usage=usage)
print("routing order (free first, then least-used):", order)
print("excluded:", [n for n in sorted(states) if n not in order])
print("recharged since previous probe:", tp.recharge_detected(prev_states, states))
print()
print("usage share (all-time ledger):", tp.usage_share(usage))
