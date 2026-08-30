"""
Read-only sensory bridge: the research kernel's afferent nerve into the live
octopus organism at F:\\backup.

DOCTRINE COMPLIANCE (learned from the body, 2026-07-14):
  - The kernel attaches as a Ring-2 cognitive organ: afferent (reads) broadband,
    efferent propose-only. This module is AFFERENT ONLY.
  - Risk Ladder = GREEN: it only READS the body (SQLite opened uri mode=ro) and
    only WRITES new files inside the kernel's own dir. It never writes to
    F:\\backup, never touches the TCB, never creates accounts/secrets.
  - Improve-not-rewrite: a standalone reader; the body is untouched.

It exports the organism's event stream ONCE to a local snapshot so experiments
are reproducible and the body is touched read-only a single time. If the body
is unmounted, experiments run from the snapshot.
"""
from __future__ import annotations

import json
import os
import sqlite3
from typing import Dict, List, Optional, Tuple

BODY_DB = "F:/backup/4d_system/outputs/4d_experiments.db"
_HERE = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(_HERE, "data")
SNAPSHOT = os.path.join(DATA_DIR, "organism_events.json")

# the 9-phase spinal cycle (learned from 4D.md:43) — phase index is a feature
CYCLE = ["explore", "real", "synthesize", "introspect", "create",
         "mutate", "evolve", "conclude", "guard"]


def export_snapshot(limit: Optional[int] = None) -> dict:
    """Read the body's dashboard_events READ-ONLY and write a local snapshot.
    Never writes to F:\\backup. Returns summary stats."""
    os.makedirs(DATA_DIR, exist_ok=True)
    # mode=ro + immutable=1: zero lock-risk even if a writer were live; the 4d
    # research daemon that feeds this table has been stopped since 2026-07-11
    # (WAL checkpointed to 0 bytes), so the snapshot is a stable static read.
    uri = f"file:{BODY_DB}?mode=ro&immutable=1"
    db = sqlite3.connect(uri, uri=True)
    db.row_factory = sqlite3.Row
    cur = db.cursor()
    q = "SELECT id, timestamp, trace_id, agent_id, event_name, status, " \
        "duration_ms, next_action, approval_state FROM dashboard_events ORDER BY id"
    if limit:
        q += f" LIMIT {int(limit)}"
    rows = [dict(r) for r in cur.execute(q).fetchall()]
    db.close()
    snap = {
        "source": f"{BODY_DB} (read-only)",
        "n_events": len(rows),
        "events": rows,
    }
    with open(SNAPSHOT, "w", encoding="utf-8") as f:
        json.dump(snap, f, ensure_ascii=False)
    return {"n_events": len(rows), "snapshot": SNAPSHOT}


def load_events() -> List[dict]:
    """Load the local snapshot (does NOT touch the body)."""
    if not os.path.exists(SNAPSHOT):
        export_snapshot()
    with open(SNAPSHOT, "r", encoding="utf-8") as f:
        return json.load(f)["events"]


# ---------------------------------------------------------------- live refresh
# When the owner reactivates the body's 4d research daemon, it appends fresh
# rows to dashboard_events. These helpers let the shadow cortex NOTICE fresh
# data and re-evaluate — still strictly READ-ONLY on the body (never a write).
# NOTE: while a writer may be live we must NOT use immutable=1 (that asserts the
# file never changes); a plain mode=ro read is WAL-safe for concurrent readers.
def _body_state() -> dict:
    """Read-only max(id)+count from the live body DB (mode=ro, writer-safe).
    Returns {'reachable':bool, 'n_events':int, 'max_id':int|None, 'error':str?}."""
    if not os.path.exists(BODY_DB):
        return {"reachable": False, "n_events": 0, "max_id": None,
                "error": "body DB not mounted"}
    try:
        db = sqlite3.connect(f"file:{BODY_DB}?mode=ro", uri=True, timeout=2.0)
        cur = db.cursor()
        n = cur.execute("SELECT COUNT(*) FROM dashboard_events").fetchone()[0]
        mx = cur.execute("SELECT MAX(id) FROM dashboard_events").fetchone()[0]
        db.close()
        return {"reachable": True, "n_events": int(n), "max_id": mx, "error": None}
    except Exception as e:                       # never raise into the caller
        return {"reachable": False, "n_events": 0, "max_id": None, "error": str(e)}


def _snapshot_state() -> dict:
    if not os.path.exists(SNAPSHOT):
        return {"n_events": 0, "max_id": None}
    evs = load_events()
    mx = max((e.get("id") or 0) for e in evs) if evs else None
    return {"n_events": len(evs), "max_id": mx}


def fresh_events_available() -> dict:
    """READ-ONLY: is the live body ahead of our local snapshot?
    Returns {fresh:bool, live_n, snap_n, new_rows, reachable, error?}."""
    live = _body_state()
    snap = _snapshot_state()
    if not live["reachable"]:
        return {"fresh": False, "reachable": False, "error": live["error"],
                "live_n": 0, "snap_n": snap["n_events"], "new_rows": 0}
    new_rows = max(0, live["n_events"] - snap["n_events"])
    return {"fresh": new_rows > 0, "reachable": True, "error": None,
            "live_n": live["n_events"], "snap_n": snap["n_events"],
            "new_rows": new_rows}


def live_refresh_and_reevaluate(force: bool = False) -> dict:
    """If the body has fresh events (or force), RE-SNAPSHOT (read-only) and
    RE-RUN the hybrid self-model (H-HYBRID-01) on the fresh data. Never writes
    to the body. Returns a summary the shadow cortex can log / propose from."""
    fe = fresh_events_available()
    if not fe["reachable"]:
        return {"action": "skipped", "reason": "body unreachable", **fe}
    if not fe["fresh"] and not force:
        return {"action": "no_op", "reason": "no fresh events", **fe}
    export_snapshot()                            # read-only re-export
    # re-run the frozen hybrid pipeline on the fresh snapshot
    from .hybrid_organism import _run_all, PRIMARY_K
    r = _run_all(PRIMARY_K, 0.70)
    return {"action": "reevaluated", **fe,
            "hybrid_selfpred": round(r["hybrid"], 3),
            "bottleneck_advantage": round(r["hybrid_vs_unlimited"], 3),
            "slots": r["slots"],
            "note": "propose-only; no body write, no outward action"}


# ---------------------------------------------------------------- feature space
def _bucket_dur(ms) -> int:
    if ms is None:
        return 0
    if ms == 0:
        return 0
    if ms < 100:
        return 1
    if ms < 1000:
        return 2
    if ms < 10000:
        return 3
    return 4


def event_features(events: List[dict], i: int) -> Dict[str, object]:
    """Feature vocabulary for predicting event i's outcome from its CONTEXT
    (everything knowable at/just-before i, plus the previous event in stream).
    All features are categorical ints/strings — the WM bottleneck selects a
    subset, exactly like the grid-world kernel."""
    e = events[i]
    prev = events[i - 1] if i > 0 else {}
    agent = e.get("agent_id", "?")
    phase_idx = CYCLE.index(agent) if agent in CYCLE else -1
    return {
        "agent": agent,                                  # 0
        "event_name": e.get("event_name", "?"),          # 1
        "phase_idx": phase_idx,                           # 2  position in the 9-cycle
        "prev_event": prev.get("event_name", "START"),   # 3
        "prev_status": prev.get("status", "START"),       # 4
        "prev_agent": prev.get("agent_id", "START"),      # 5
        "dur_bucket": _bucket_dur(e.get("duration_ms")),  # 6
        "same_trace_as_prev": int(e.get("trace_id") == prev.get("trace_id")),  # 7
        "approval": e.get("approval_state") or "none",    # 8
        "prev_phase": CYCLE.index(prev.get("agent_id")) if prev.get("agent_id") in CYCLE else -1,  # 9
    }


FEATURE_ORDER = ["agent", "event_name", "phase_idx", "prev_event", "prev_status",
                 "prev_agent", "dur_bucket", "same_trace_as_prev", "approval",
                 "prev_phase"]
N_FEATURES = len(FEATURE_ORDER)


def build_dataset(target: str) -> Tuple[List[tuple], List[str]]:
    """Return (feature_tuples, targets) in stream order. target in
    {'next_action','status','event_name','next_event_name'}. For
    'next_event_name' the label is the FOLLOWING event's name (behavioral
    self-prediction) and the last event is dropped."""
    events = load_events()
    X: List[tuple] = []
    Y: List[str] = []
    n = len(events)
    for i in range(n):
        if target == "next_event_name":
            if i + 1 >= n:
                break
            label = str(events[i + 1].get("event_name", "?"))
        else:
            label = str(events[i].get(target, "?"))
        feats = event_features(events, i)
        X.append(tuple(feats[k] for k in FEATURE_ORDER))
        Y.append(label)
    return X, Y


if __name__ == "__main__":
    import sys
    from collections import Counter
    stats = export_snapshot()
    print("exported:", stats)
    for tgt in ("next_action", "status", "event_name"):
        X, Y = build_dataset(tgt)
        c = Counter(Y)
        base = max(c.values()) / len(Y)
        print(f"target={tgt:12s} classes={len(c):2d} majority_baseline={base:.3f} "
              f"top={[(k[:16], v) for k, v in c.most_common(3)]}")
