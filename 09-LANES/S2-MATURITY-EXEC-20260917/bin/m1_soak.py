#!/usr/bin/env python3
"""S2-MATURITY M1 — replay-path memory soak (node 138 replica, quota-caged).

Measures the CANDIDATE snapshot.py replay path over the FROZEN REAL journal
(425MB, 3.08M events) under cgroup MemoryMax=1610612736 (1536 MiB).
This is NOT the full app boot (blocked — see PREREG); it is the memory-risk
path M1's RSS criterion targets. If the from-empty replay OOMs inside the
scope, that is a MEASURED FAIL and must be preserved, not hidden.

Self-samples every 60s: /proc/self/status VmRSS/VmSwap + cgroup memory files.
65 samples hard cap. Output: soak-samples.jsonl next to this script.
"""
import json
import os
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
SRC = HERE / "src"
STATE = HERE / "state"
OUT = HERE / "soak-samples.jsonl"

import sys
sys.path.insert(0, str(SRC))
import octopus_sensorium.snapshot as SNAP  # noqa: E402

CG = Path("/sys/fs/cgroup/system.slice/s2replica-soak.scope")


def sample(i, tag):
    proc = {}
    for line in Path("/proc/self/status").read_text().splitlines():
        if line.startswith(("VmRSS", "VmSwap", "VmSize")):
            k, v = line.split(":", 1)
            proc[k] = v.strip()
    cg = {}
    for f in ("memory.current", "memory.peak", "memory.swap.current", "memory.events"):
        try:
            cg[f.replace(".", "_")] = (CG / f).read_text().strip()[:200]
        except OSError:
            cg[f.replace(".", "_")] = "NA"
    rec = {"ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "i": i,
           "tag": tag, "proc": proc, "cg": cg}
    with OUT.open("a") as fh:
        fh.write(json.dumps(rec) + "\n")
    return rec


def main():
    sample(0, "boot")
    # Phase A (light, 20 samples): snapshot-anchored replay only.
    # NOTE: replay_matches_current() deliberately EXCLUDED here — it internally
    # does load_events(after_seq=0), i.e. the from-empty materialization; the
    # first launch OOM-killed at T+16s (1.5G peak) because of exactly that.
    # The from-empty bomb is measured ONCE in Phase B instead.
    snap = SNAP.load_latest(directory=STATE / "snapshots")
    for i in range(1, 21):
        state = SNAP.replay(journal=STATE / "events.jsonl",
                            after_seq=int((snap or {}).get("journal_seq") or 0),
                            initial=snap)
        sample(i, "anchored_replay")
        time.sleep(60)
    # Phase B (the RAM test): ONE from-empty replay of the full frozen journal.
    # load_events(after_seq=0) materializes all events — the 02B risk.
    sample(20, "before_from_empty")
    t0 = time.time()
    state = SNAP.replay(journal=STATE / "events.jsonl", after_seq=0)
    sample(21, "after_from_empty")
    (HERE / "FROM-EMPTY-RESULT.json").write_text(json.dumps({
        "wall_s": round(time.time() - t0, 1),
        "state_hash": SNAP.state_hash(state),
        "observations_published": state.get("observations_published"),
    }, indent=2) + "\n")
    for i in range(22, 65):
        sample(i, "hold_after_from_empty")
        time.sleep(60)
    with OUT.open("a") as fh:
        fh.write(json.dumps({"ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                             "event": "SOAK_COMPLETED"}) + "\n")


if __name__ == "__main__":
    main()
