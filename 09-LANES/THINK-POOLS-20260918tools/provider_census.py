#!/usr/bin/env python3
"""Phase A3 — provider census for the THINK-POOLS mission.

Reads only. Prints provider names, status, and per-provider usage/spend from the
budget ledger. Never prints a key value: only key NAMES appear anywhere.
"""
import collections
import datetime
import json
import pathlib

BASE = pathlib.Path("/home/ari/ofn/state/api-budget")
HEALTH = BASE / "config" / "provider-health.jsonl"
LEDGER = BASE / "budget-ledger.jsonl"

print("=== health rows: true shape ===")
rows = []
for line in HEALTH.read_text(errors="replace").splitlines():
    line = line.strip()
    if not line:
        continue
    try:
        rows.append(json.loads(line))
    except json.JSONDecodeError:
        continue
print("health rows:", len(rows))
if rows:
    print("all keys seen:", sorted({k for r in rows for k in r.keys()}))
    print("--- last 3 rows ---")
    for r in rows[-3:]:
        print(json.dumps(r, ensure_ascii=False)[:900])

print()
print("=== per-provider latest health (rows nest providers under 'record') ===")
latest = {}
for r in rows:
    rec = r.get("record") or r
    for name, val in rec.items():
        if name.startswith("_") or not isinstance(val, dict):
            continue
        latest[name] = {"at": r.get("at"), **val}
for name, r in sorted(latest.items()):
    fields = {k: r[k] for k in ("status", "http_status", "models_count", "consecutive_failures",
                               "cooldown_until", "paid", "evidence") if k in r}
    print(f"  {name:<12} {json.dumps(fields, ensure_ascii=False)[:230]}")
print("  providers seen in health:", sorted(latest.keys()))

print()
print("=== budget ledger: usage per provider ===")
lrows = []
for line in LEDGER.read_text(errors="replace").splitlines():
    line = line.strip()
    if not line:
        continue
    try:
        lrows.append(json.loads(line))
    except json.JSONDecodeError:
        continue
print("ledger rows:", len(lrows))
if lrows:
    print("all keys seen:", sorted({k for r in lrows for k in r.keys()}))
    byp = collections.Counter()
    cost = collections.Counter()
    last = collections.defaultdict(str)
    day = collections.Counter()
    for r in lrows:
        prov = str(r.get("provider") or r.get("brain") or r.get("model") or "unknown")
        byp[prov] += 1
        try:
            cost[prov] += float(r.get("cost_usd") or r.get("cost") or 0)
        except (TypeError, ValueError):
            pass
        at = str(r.get("at") or r.get("ts") or r.get("timestamp") or "")
        if at > last[prov]:
            last[prov] = at
        if at[:10]:
            day[at[:10]] += 1
    print("calls per provider:", dict(byp))
    print("cost_usd per provider:", {k: round(v, 4) for k, v in cost.items()})
    print("last call per provider:", dict(last))
    print("calls per day (last 10 days present):", dict(sorted(day.items())[-10:]))

print()
print("=== staleness ===")
import os
now = datetime.datetime.now(datetime.timezone.utc)
for p in (HEALTH, LEDGER, BASE / "providers.py", BASE / "provider_failover.py"):
    if p.exists():
        mtime = datetime.datetime.fromtimestamp(p.stat().st_mtime, datetime.timezone.utc)
        age_h = (now - mtime).total_seconds() / 3600.0
        print(f"  {p.name:<28} mtime={mtime.strftime('%Y-%m-%dT%H:%M:%SZ')} age_h={age_h:.1f}")
