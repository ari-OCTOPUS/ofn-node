#!/usr/bin/env python3
"""PERFUSION Phase 0 — angiography probe (read-only).

For every organ it can see on board 138, measure the five veins:
  telemetry  a systemd unit/timer that reports health
  brain      code that calls a provider (remote_brain / brainport / BRAIN_PROVIDER /
             local llama.cpp / T3 model service)
  data       a state directory that is actually being written
  receipt    a receipts/events ledger with recent rows
  compute    whether the organ can draw work from the base pool (fleet-compute)

Output is a compact JSON summary — never raw file dumps, and never a credential.
"""
import json
import pathlib
import re
import subprocess
import time
from datetime import datetime, timezone

OFN = pathlib.Path("/home/ari/ofn")
STATE = OFN / "state"
now = time.time()


def sh(cmd, timeout=60):
    p = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
    return p.stdout.strip()


# ---------- telemetry vein: units and timers ----------
units = {}
for line in sh("systemctl list-units 'octopus-*' --all --plain --no-legend "
               "--no-pager 2>/dev/null").splitlines():
    parts = line.split()
    if len(parts) >= 4:
        units[parts[0]] = {"active": parts[2], "sub": parts[3]}

timers = {}
for line in sh("systemctl list-timers --all --plain --no-legend --no-pager 2>/dev/null").splitlines():
    m = re.match(r"^\S+\s+\S+\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)", line)
    parts = line.split()
    for i, p in enumerate(parts):
        if p.startswith("octopus-"):
            timers[p] = {"next": parts[0] if parts[0] not in ("-",) else None,
                         "last": parts[i - 2] if i >= 2 else None}
            break

# ---------- brain vein: who actually calls a provider ----------
brain_hits = {}
for root in (OFN / "ofn", OFN / "state", OFN / "tools"):
    if not root.exists():
        continue
    for p in root.rglob("*.py"):
        if any(x in str(p) for x in ("__pycache__", "/worktree/", "/stage/")):
            continue
        try:
            t = p.read_text(errors="replace")
        except OSError:
            continue
        marks = []
        if re.search(r"remote_brain|brainport|RemoteBrain", t):
            marks.append("remote_brain")
        if re.search(r"BRAIN_PROVIDER", t):
            marks.append("BRAIN_PROVIDER")
        if re.search(r"8193", t):
            marks.append("t3:8193")
        if re.search(r"llamacpp|:8081", t, re.I):
            marks.append("llama180")
        if re.search(r"provider_failover|think_pool", t):
            marks.append("provider_registry")
        if marks:
            brain_hits[str(p.relative_to(OFN))] = marks

# ---------- data + receipt veins: state dirs, freshness, ledgers ----------
organs = {}
for d in sorted(STATE.iterdir()):
    if not d.is_dir() or d.name.startswith("."):
        continue
    newest, count24, total = 0.0, 0, 0
    for f in d.rglob("*"):
        if not f.is_file():
            continue
        total += 1
        try:
            m = f.stat().st_mtime
        except OSError:
            continue
        newest = max(newest, m)
        if now - m < 86400:
            count24 += 1
        if total > 4000:
            break
    ledgers = [str(f.relative_to(d)) for f in d.glob("*.jsonl")
               if "receipt" in f.name or "ledger" in f.name or "event" in f.name
               or "decision" in f.name or "outcome" in f.name]
    last_row = None
    for name in ledgers:
        p = d / name
        try:
            tail = p.read_text(errors="replace").strip().splitlines()[-1:]
        except OSError:
            continue
        if tail:
            try:
                row = json.loads(tail[0])
                at = str(row.get("at") or row.get("ts") or row.get("at_utc") or "")
                if at and (last_row is None or at > last_row):
                    last_row = at
            except json.JSONDecodeError:
                pass
    organs[d.name] = {
        "files": total,
        "written_24h": count24,
        "newest_age_h": round((now - newest) / 3600, 1) if newest else None,
        "ledgers": ledgers[:6],
        "last_ledger_row": last_row,
    }

# ---------- compute vein: fleet-compute wiring ----------
compute = {"control_plane": (OFN / "tools/compute_scheduler.py").exists(),
           "agent_on_this_node": pathlib.Path("/usr/local/bin/compute_worker.py").exists(),
           "timers": {k: v for k, v in timers.items() if "compute" in k}}
try:
    sys.path.insert(0, str(OFN / "tools"))
    import compute_core as cc
    compute["task_states"] = cc.Store(str(STATE / "fleet-compute/compute_tasks.db")).stats()["by_state"]
except Exception as exc:  # noqa: BLE001
    compute["task_states"] = f"unavailable: {type(exc).__name__}"

print(json.dumps({
    "at_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    "units_total": len(units),
    "units_by_sub": {s: sum(1 for u in units.values() if u["sub"] == s)
                     for s in {u["sub"] for u in units.values()}},
    "octopus_units": sorted(units),
    "timers": timers,
    "brain_consumers": brain_hits,
    "organs": organs,
    "compute_vein": compute,
}, indent=1, ensure_ascii=False))
