#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""replay.py — dry-run replay from checkpoint (ADR-033).

Default: dry_run=true, forbid_external_effects=true, tool_mode=mock.
Unsafe configuration → blocked.
"""
from __future__ import annotations

import json
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable
from uuid import uuid4

from runtime.checkpoint_store import Checkpoint, CheckpointStore

_OPS = Path(__file__).resolve().parents[1]
_REPLAY_DIR = _OPS / "state" / "adr-033" / "replay"


@dataclass(frozen=True)
class ReplayRequest:
    run_id: str
    checkpoint_id: str
    policy_version: str
    graph_version: str
    dry_run: bool = True
    forbid_external_effects: bool = True


def create_replay(
    request: ReplayRequest,
    store: CheckpointStore | None = None,
    runtime_fn: Callable[[Checkpoint, str], dict[str, Any]] | None = None,
) -> str:
    store = store or CheckpointStore()
    if not store.available():
        raise RuntimeError("replay_blocked:store_unavailable")

    checkpoint = store.load(request.run_id, request.checkpoint_id)
    if checkpoint is None:
        raise RuntimeError("replay_blocked:checkpoint_missing")

    if checkpoint.policy_version != request.policy_version:
        raise RuntimeError("replay_blocked:policy_version_mismatch")

    if request.graph_version and checkpoint.graph_version != request.graph_version:
        raise RuntimeError("replay_blocked:graph_version_mismatch")

    if not request.dry_run or not request.forbid_external_effects:
        raise RuntimeError("replay_blocked:unsafe_replay_configuration")

    replay_id = f"replay-{uuid4().hex[:12]}"
    result: dict[str, Any]
    if runtime_fn is not None:
        result = runtime_fn(checkpoint, replay_id)
    else:
        # Deterministic mock replay — re-emits checkpoint metadata only
        result = {
            "ok": True,
            "tool_mode": "mock",
            "external_effects": False,
            "node": checkpoint.node,
            "input_digest": checkpoint.input_digest,
            "state_version": checkpoint.state_version,
        }

    _REPLAY_DIR.mkdir(parents=True, exist_ok=True)
    out = {
        "replay_id": replay_id,
        "request": {
            "run_id": request.run_id,
            "checkpoint_id": request.checkpoint_id,
            "policy_version": request.policy_version,
            "graph_version": request.graph_version,
            "dry_run": request.dry_run,
            "forbid_external_effects": request.forbid_external_effects,
        },
        "result": result,
        "occurred_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    path = _REPLAY_DIR / f"{request.run_id}-{replay_id}.json"
    path.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")

    try:
        from evidence_plane.event_log import append_event
        append_event(
            event_type="replay.execute",
            run_id=request.run_id,
            checkpoint_id=request.checkpoint_id,
            policy_version=request.policy_version,
            state_version=checkpoint.state_version,
            actor="replay",
            action="replay",
            decision="allow",
            reason_code="dry_run_mock",
            payload_digest=checkpoint.input_digest,
            extra={"replay_id": replay_id},
        )
    except Exception:  # noqa: BLE001
        pass

    return replay_id
