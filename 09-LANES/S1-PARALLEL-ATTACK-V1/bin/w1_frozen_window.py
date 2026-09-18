#!/usr/bin/env python3
"""S1-PARALLEL-ATTACK-V1 / L-D witness-1(+4) — 24h frozen-window watcher (node 182).

Read-only. Every 300s for 24h (288 samples, hard bound) records:
- activation timestamps + restart counts of the two apply .path/.service unit pairs
- count of running apply_signed_inbound processes (must stay 0)
- consumed/ archive entry count + bytes (witness-4: archive growth, no .path watches it)
Historical assertion at start: activations frozen since the GAP-02 fix 07:18Z.
Output: /var/lib/octopus/state/s1pa-attack/w1-frozen-window.jsonl
Rollback: kill PID; delete outputs. No service is touched.
"""
import json
import subprocess
import time
from pathlib import Path

OUT = Path("/var/lib/octopus/state/s1pa-attack/w1-frozen-window.jsonl")
UNITS = ["octopus-apply-checkpoint.path", "octopus-apply-checkpoint.service",
         "octopus-apply-registry.path", "octopus-apply-registry.service"]
CONSUMED = Path("/var/lib/octopus/state/inbound-apply/consumed")
INTERVAL = 300
SAMPLES = 288  # 24h
FIXED_PREFIX = "2026-09-17 07:18:"  # both activations inside this minute: :32 / :41 UTC
# NOTE: the first deployed copy used prefix "07:18:3" which does not match 07:18:41,
# so the W1_START header recorded historical_frozen_since_fix=false as a matching
# artifact. Baseline timestamps in that same header prove frozen (07:18:32/41).
# Verdict evaluation must compare sample timestamps to the baseline, not to that flag.


def props(unit):
    try:
        out = subprocess.run(["systemctl", "show", unit, "-p", "ActiveState",
                              "-p", "ExecMainStartTimestamp", "-p", "NRestarts"],
                             capture_output=True, text=True, timeout=15).stdout
        return dict(line.split("=", 1) for line in out.strip().splitlines() if "=" in line)
    except Exception as e:
        return {"error": type(e).__name__}


def apply_procs():
    try:
        out = subprocess.run(["pgrep", "-af", "apply_signed_inbound"],
                             capture_output=True, text=True, timeout=10).stdout
        return [l for l in out.strip().splitlines() if "pgrep" not in l]
    except Exception:
        return []


def consumed_stats():
    n = b = 0
    if CONSUMED.is_dir():
        for p in CONSUMED.iterdir():
            if p.is_dir():
                n += 1
                for f in p.iterdir():
                    try:
                        b += f.stat().st_size
                    except OSError:
                        pass
    return {"entries": n, "bytes": b}


def main():
    base = {}
    for u in UNITS:
        base[u] = props(u)
    hist_ok = all(
        FIXED_PREFIX in str(base[u].get("ExecMainStartTimestamp", ""))
        for u in UNITS if u.endswith(".service"))
    header = {"ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "sample": -1,
              "event": "W1_START", "historical_frozen_since_fix": hist_ok,
              "baseline": base}
    with OUT.open("a") as f:
        f.write(json.dumps(header) + "\n")
    for i in range(SAMPLES):
        rec = {"ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "sample": i,
               "units": {u: props(u) for u in UNITS},
               "apply_procs": apply_procs(),
               "consumed": consumed_stats()}
        with OUT.open("a") as f:
            f.write(json.dumps(rec) + "\n")
        time.sleep(INTERVAL)
    with OUT.open("a") as f:
        f.write(json.dumps({"ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                            "event": "W1_COMPLETED_BOUND_REACHED"}) + "\n")


if __name__ == "__main__":
    main()
