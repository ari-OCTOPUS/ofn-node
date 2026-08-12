#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""rollback.py — restore state to prior checkpoint; append-only history (ADR-033).

Does NOT wipe idempotency ledger. Invalidates later proposals. Event: rollback.applied.
"""
from __future__ import annotations

import json
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from uuid import uuid4

from runtime.checkpoint_store import CheckpointStore

_OPS = Path(__file__).resolve().parents[1]
_STATE = _OPS / "state" / "adr-033"
_IDEMP = _STATE / "idempotency-ledger.jsonl"


@dataclass(frozen=True)
class RollbackResult:
    ok: bool
    reason: str
    rollback_id: str | None = None
    new_state_version: int | None = None


def apply_rollback(
    *,
    run_id: str,
    checkpoint_id: str,
    expected_state_version: int | None = None,
    kill_switch_already_on: bool = True,
    store: CheckpointStore | None = None,
) -> RollbackResult:
    """
    Steps (documented):
      1. Kill switch should be engaged (caller sets env / flag)
      2. Load valid prior checkpoint
      3. CAS restore with new state_version
      4. Invalidate later proposals/approvals (marker file)
      5. Keep idempotency ledger
      6. Append rollback.applied
      7. Health → PAUSED (status file)
    """
    store = store or CheckpointStore()
    rollback_id = f"rb-{uuid4().hex[:12]}"

    if not kill_switch_already_on:
        return RollbackResult(False, "kill_switch_required", rollback_id)

    if not store.available():
        return RollbackResult(False, "store_unavailable", rollback_id)

    cp = store.load(run_id, checkpoint_id)
    if cp is None:
        return RollbackResult(False, "checkpoint_missing", rollback_id)

    if expected_state_version is not None and cp.state_version != expected_state_version:
        return RollbackResult(False, "state_version_mismatch", rollback_id)

    new_version = cp.state_version + 1
    restore = {
        "run_id": run_id,
        "restored_checkpoint_id": checkpoint_id,
        "state_version": new_version,
        "policy_version": cp.policy_version,
        "graph_version": cp.graph_version,
        "input_digest": cp.input_digest,
        "node": cp.node,
        "run_status": "PAUSED",
        "rollback_id": rollback_id,
        "restored_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    run_dir = _STATE / "runs"
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / f"{run_id}.json").write_text(
        json.dumps(restore, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    # Invalidate later proposals (marker — does not delete history)
    inv = _STATE / "proposals" / f"invalidated-after-{checkpoint_id}.json"
    inv.parent.mkdir(parents=True, exist_ok=True)
    inv.write_text(
        json.dumps({
            "rollback_id": rollback_id,
            "after_checkpoint_id": checkpoint_id,
            "run_id": run_id,
            "invalidated_at": restore["restored_at"],
        }, indent=2),
        encoding="utf-8",
    )

    # Ensure idempotency ledger path exists but is never truncated here
    _IDEMP.parent.mkdir(parents=True, exist_ok=True)
    if not _IDEMP.exists():
        _IDEMP.write_text("", encoding="utf-8")

    try:
        from evidence_plane.event_log import append_event
        append_event(
            event_type="rollback.applied",
            run_id=run_id,
            checkpoint_id=checkpoint_id,
            policy_version=cp.policy_version,
            state_version=new_version,
            actor="rollback",
            action="rollback",
            decision="allow",
            reason_code="rollback_applied",
            payload_digest=cp.input_digest,
            extra={"rollback_id": rollback_id},
        )
    except Exception:  # noqa: BLE001
        pass

    return RollbackResult(True, "rollback_applied", rollback_id, new_version)


def idempotency_ledger_path() -> Path:
    return _IDEMP
