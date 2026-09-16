#!/usr/bin/env python3
"""M7 — route_scorer_shadow_log: log the static dict-tier vs the 6-signal
route_scorer tier side-by-side, WITHOUT changing routing. Additive · flag-off.

Fixes audit Axis-6 (Intelligence Coordination 2/5): the actual dispatcher is a
static lookup `want = TASK_TIERS.get(task, "local")` (model_router.py:113), while
the genuinely intelligent 6-signal scorer (route_scorer.score_route) is a SHELF
artifact with zero production callers. This wires the scorer into OBSERVABILITY
only — it records where the dumb dict and the smart scorer AGREE or DISAGREE, so
drift is measurable BEFORE any owner decision to let the scorer drive. Routing is
untouched: the dict-tier is still exactly what runs.

BEHAVIOR (only when flag-armed, at model_router.ask:113)
  log_decision(task, dict_tier, ctx) computes route_scorer.score_route(task, ctx)
  ["tier"] and appends ONE line {ts, task, dict_tier, scorer_tier, agree} to
  state/cortex/route-decisions.jsonl. fail-soft, bounded, never blocks ask().

FLAG (default OFF — checked at the call-site, so unset → not even imported)
  OCTOPUS_WIRE_ROUTE_SHADOW=1   enable the shadow log.

CALL-SITE (model_router.ask, right after `want = tier or TASK_TIERS.get(...)`):
  if os.environ.get("OCTOPUS_WIRE_ROUTE_SHADOW")=="1":
      <mod>.log_decision(task, want)

ROLLBACK: delete this module + remove the flag-gated line at model_router.ask
  (grep OCTOPUS_WIRE_ROUTE_SHADOW). Or leave the flag unset.

$0 · stdlib-only · fail-soft · does NOT change which tier runs.
"""
from __future__ import annotations

import os
import sys
import time
from pathlib import Path

_HERE = Path(__file__).resolve().parent          # _ops/now_moves
_OPS = _HERE.parent                              # _ops

FLAG = "OCTOPUS_WIRE_ROUTE_SHADOW"
_SOFT_CAP = 5000                                 # keep the shadow log from growing unbounded


def _scorer_tier(task: str, ctx=None):
    """route_scorer.score_route(task, ctx)['tier'] — read-only, fail-soft → None."""
    try:
        p = str(_OPS / "cortex")
        if p not in sys.path:
            sys.path.insert(0, p)
        import route_scorer
        r = route_scorer.score_route(task, ctx or {})
        return r.get("tier") if isinstance(r, dict) else None
    except Exception:
        return None


def _log_path():
    try:
        p = str(_OPS / "budget")
        if p not in sys.path:
            sys.path.insert(0, p)
        import opslib
        return opslib.STATE_DIR / "cortex" / "route-decisions.jsonl"
    except Exception:
        return None


def log_decision(task: str, dict_tier: str, ctx=None) -> dict | None:
    """Append one shadow record. NEVER blocks the beat loop (wedge fix v2).

    v2 (2026-09-08): time-budgeted — if file I/O exceeds 2 seconds, skip.
    Root cause fix for 5 wedges where main thread froze in _maybe_trim.
    """
    import json
    import time as _t
    _deadline = _t.time() + 2.0
    try:
        st = _scorer_tier(task, ctx)
        rec = {"ts": time.strftime("%Y-%m-%dT%H:%M:%S"), "task": str(task)[:60],
               "dict_tier": dict_tier, "scorer_tier": st,
               "agree": (st is not None and st == dict_tier)}
        p = _log_path()
        if p:
            p.parent.mkdir(parents=True, exist_ok=True)
            with open(p, "a", encoding="utf-8") as f:
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")
            if _t.time() < _deadline:
                _maybe_trim(p)
        return rec
    except Exception:
        return None


# ROOT CAUSE FIX 2026-09-08: _maybe_trim was doing readlines() on every call
# on a growing 2MB+ file — on Windows with backup I/O, this blocked the main
# thread INDEFINITELY (5 wedges on 2026-09-07, py-spy stack captured).
# New: O(1) size check + rate-limited + rename-based trim. NEVER blocks.
_last_trim_check = {"ts": 0.0}
_TRIM_CHECK_INTERVAL_S = 300.0
_TRIM_SIZE_THRESHOLD = 4 * 1024 * 1024


def _maybe_trim(p) -> None:
    """SAFE trim — O(1) size check, rate-limited, rename-based. Root cause fix."""
    import time as _time
    now = _time.time()
    if now - _last_trim_check["ts"] < _TRIM_CHECK_INTERVAL_S:
        return
    _last_trim_check["ts"] = now
    try:
        size = p.stat().st_size  # O(1), no readlines, no lock
        if size <= _TRIM_SIZE_THRESHOLD:
            return
        with open(p, "rb") as f:
            f.seek(max(0, size - 1_500_000))
            tail = f.read()
        nl = tail.find(b"\n")
        if nl >= 0:
            tail = tail[nl + 1:]
        tmp = p.with_suffix(".trim.tmp")
        tmp.write_bytes(tail)
        tmp.replace(p)  # atomic rename — no in-place write lock
    except (OSError, PermissionError):
        pass
    except Exception:
        pass


def summary(n: int = 200) -> dict:
    """Read-only: agreement rate over the last n shadow records (for a report)."""
    import json
    p = _log_path()
    if not p or not p.exists():
        return {"n": 0, "agree_pct": None, "disagreements": []}
    try:
        recs = [json.loads(x) for x in p.read_text("utf-8").splitlines() if x.strip()][-n:]
    except Exception:
        return {"n": 0, "agree_pct": None, "disagreements": []}
    if not recs:
        return {"n": 0, "agree_pct": None, "disagreements": []}
    agree = sum(1 for r in recs if r.get("agree"))
    disagree = [{"task": r.get("task"), "dict": r.get("dict_tier"),
                 "scorer": r.get("scorer_tier")} for r in recs if not r.get("agree")]
    return {"n": len(recs), "agree_pct": round(100.0 * agree / len(recs), 1),
            "disagreements": disagree[-10:]}


def main(argv=None) -> int:
    import json
    print(json.dumps(summary(), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
