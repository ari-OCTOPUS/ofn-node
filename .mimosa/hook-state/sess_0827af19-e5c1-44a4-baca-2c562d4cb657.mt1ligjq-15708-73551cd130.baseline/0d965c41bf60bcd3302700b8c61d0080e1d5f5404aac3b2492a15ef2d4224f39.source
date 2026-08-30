#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""event_log.py — append-only JSONL forensic log (ADR-033).

Never stores DM text, prompts, tokens, or raw payloads — digests only.
Honors OPS_DIR for sandbox/tests (live_state_guard compatible).
"""
from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Any
from uuid import uuid4


def _ops() -> Path:
    return Path(os.environ["OPS_DIR"]) if os.environ.get("OPS_DIR") else Path(__file__).resolve().parents[1]


def _root() -> Path:
    return _ops() / "state" / "adr-033"


def root_dir() -> Path:
    return _root()


def append_event(
    *,
    event_type: str,
    run_id: str,
    checkpoint_id: str | None = None,
    proposal_id: str | None = None,
    policy_version: str = "ADR-033-v1",
    state_version: int = 0,
    actor: str = "system",
    action: str | None = None,
    decision: str | None = None,
    reason_code: str | None = None,
    payload_digest: str | None = None,
    trace_id: str | None = None,
    extra: dict[str, Any] | None = None,
) -> str:
    event_id = f"evt_{uuid4().hex[:16]}"
    day = time.strftime("%Y-%m-%d", time.gmtime())
    rec = {
        "event_id": event_id,
        "occurred_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "event_type": event_type,
        "run_id": run_id,
        "checkpoint_id": checkpoint_id,
        "proposal_id": proposal_id,
        "policy_version": policy_version,
        "state_version": state_version,
        "actor": actor,
        "action": action,
        "decision": decision,
        "reason_code": reason_code,
        "payload_digest": payload_digest,
        "trace_id": trace_id or event_id,
        "schema_version": 1,
    }
    if extra:
        safe = {k: v for k, v in extra.items()
                if k not in {"text", "prompt", "payload", "dm", "content"}}
        rec["extra"] = safe

    events = _root() / "events"
    events.mkdir(parents=True, exist_ok=True)
    path = events / f"{day}.jsonl"
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")

    if event_type.startswith("context.quarantine") or decision == "quarantine":
        quarantine = _root() / "quarantine"
        quarantine.mkdir(parents=True, exist_ok=True)
        qpath = quarantine / f"{day}.jsonl"
        with qpath.open("a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")

    try:
        from evidence_plane.trust_metrics import note_event
        note_event(event_type=event_type, decision=decision, reason_code=reason_code)
    except Exception:  # noqa: BLE001
        pass

    return event_id


def read_events(day: str | None = None, *, limit: int = 200) -> list[dict[str, Any]]:
    day = day or time.strftime("%Y-%m-%d", time.gmtime())
    path = _root() / "events" / f"{day}.jsonl"
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return rows[-limit:]
