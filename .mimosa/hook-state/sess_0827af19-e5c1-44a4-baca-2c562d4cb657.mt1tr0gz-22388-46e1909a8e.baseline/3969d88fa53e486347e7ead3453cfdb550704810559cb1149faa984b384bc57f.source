# -*- coding: utf-8 -*-
"""Canary restart protocol. EXECUTE is always false in this module.

Owner must grant a separate restart permit. This file plans order, stop
conditions, and a read-only baseline snapshot. It never kills a process.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

EXECUTE = False  # hard lock — no producer restart from this code

_OPS = Path(__file__).resolve().parent.parent
_ROOT = _OPS.parent
RECEIPTS = _OPS / "state" / "cortex" / "cost-receipts.jsonl"
MEM_LATEST = _OPS / "state" / "pulse" / "memory-read-latest.json"
ORGANISM_STATE = _OPS / "state" / "ORGANISM-STATE.json"

# Only confirmed cost-receipt producer is cortex (model_router → cost-receipts.jsonl).
# live: write:no. organism: not a cost-receipt writer. daemon: UNLOCATED as writer.
PRODUCER_GRAPH = {
    "cortex": {
        "port": 8772,
        "entry": "_ops/cortex/cortex.py",
        "writes_cost_receipts": True,
        "depends_on": [],
        "canary_rank": 1,
    },
    "brain.daemon": {
        "port": None,
        "entry": "python -m brain.daemon",
        "writes_cost_receipts": "UNKNOWN",
        "depends_on": [],
        "canary_rank": 2,
        "note": "undeclared member; do not restart until writer-status is located",
    },
    "live": {
        "port": 8773,
        "entry": "_ops/live/server.py",
        "writes_cost_receipts": False,
        "depends_on": [],
        "canary_rank": 3,
        "note": "not a receipt producer; skip for attribution canary",
    },
}

STOP = (
    "port_or_heartbeat_missing_in_window",
    "duplicate_or_unexpected_reorder",
    "task_id_bound_to_closed_or_foreign_run",
    "unresolved_converted_to_guessed_id",
    "memory_streak_reset_or_readback_not_ok",
    "paid_call_or_actuator_or_wave_state_change",
    "raw_vs_audit_count_delta_over_limit",
)


def canary_order() -> list[str]:
    """One producer at a time. Never daemon+live+cortex together."""
    ranked = sorted(
        ((v["canary_rank"], k) for k, v in PRODUCER_GRAPH.items()
         if v.get("writes_cost_receipts") is True),
        key=lambda x: x[0],
    )
    return [k for _, k in ranked]


def _line_count(path: Path) -> int:
    if not path.exists():
        return 0
    n = 0
    with path.open(encoding="utf-8", errors="replace") as f:
        for line in f:
            if line.strip():
                n += 1
    return n


def snapshot_baseline(*, dest: Path | None = None) -> dict[str, Any]:
    """Read-only checkpoint. Does not restart anything."""
    mem = None
    if MEM_LATEST.exists():
        try:
            mem = json.loads(MEM_LATEST.read_text(encoding="utf-8"))
        except ValueError:
            mem = {"error": "UNPARSEABLE"}
    beat = None
    if ORGANISM_STATE.exists():
        try:
            st = json.loads(ORGANISM_STATE.read_text(encoding="utf-8"))
            beat = st.get("beat") or (st.get("cardiac") or {}).get("beat")
        except ValueError:
            beat = None
    snap = {
        "schema": "canary-baseline/1",
        "ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "execute": EXECUTE,
        "receipt_lines": _line_count(RECEIPTS),
        "memory_latest": {
            "beat": (mem or {}).get("beat"),
            "reads": (mem or {}).get("memory_reads_per_cycle"),
            "readback": (mem or {}).get("readback"),
            "status": (mem or {}).get("status"),
        } if mem else None,
        "organism_beat": beat,
        "first_canary": canary_order()[:1],
        "simultaneous_restart_forbidden": ["daemon", "live", "cortex"],
        "stop_conditions": list(STOP),
        "wave1_unlocked": False,
        "owner_permit": "NOT_GRANTED",
    }
    if dest is not None:
        dest = Path(dest)
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(json.dumps(snap, ensure_ascii=False, indent=2), encoding="utf-8")
    return snap


def plan() -> dict[str, Any]:
    return {
        "schema": "canary-restart-plan/1",
        "execute": EXECUTE,
        "owner_permit_required": True,
        "order": canary_order(),
        "graph": PRODUCER_GRAPH,
        "per_producer": [
            "checkpoint state + receipt counters",
            "baseline process/port/beat/active task context",
            "restart ONE producer",
            "wait >= 3 healthy beats",
            "measure that producer's attribution",
            "rollback on regression",
            "then next producer",
        ],
        "stop": list(STOP),
        "wave1_unlocked": False,
    }


if __name__ == "__main__":
    p = plan()
    b = snapshot_baseline(
        dest=_ROOT / "06-EVIDENCE" / "NERVOUS-RECOVERY-2026-08-20" / "CANARY-BASELINE.json")
    print(json.dumps({"plan": p, "baseline": b}, ensure_ascii=False, indent=2))
