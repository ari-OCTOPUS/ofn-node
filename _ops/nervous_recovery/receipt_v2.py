# -*- coding: utf-8 -*-
"""Receipt envelope v2 + legacy adapter. Never fabricates task_id."""
from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from typing import Any

SCHEMA_VERSION = 2
OUTCOMES = ("ok", "error", "skipped", "unattributed")


def _utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def new_receipt_id() -> str:
    return "rcpt_" + uuid.uuid4().hex


def envelope(
    *,
    task_id: str | None,
    run_id: str | None,
    agent_id: str,
    capability_id: str,
    outcome: str,
    evidence_ref: str,
    timestamp_utc: str | None = None,
    receipt_id: str | None = None,
) -> dict[str, Any]:
    if outcome not in OUTCOMES:
        raise ValueError(f"outcome must be one of {OUTCOMES}")
    tid = (task_id or "").strip()
    rid = (run_id or "").strip()
    if not tid:
        outcome = "unattributed"
        tid = ""  # never synthesize
    return {
        "receipt_id": receipt_id or new_receipt_id(),
        "timestamp_utc": timestamp_utc or _utc(),
        "task_id": tid,
        "run_id": rid,
        "agent_id": agent_id,
        "capability_id": capability_id,
        "outcome": outcome,
        "evidence_ref": evidence_ref,
        "schema_version": SCHEMA_VERSION,
    }


def adapt_legacy(row: dict, *, run_to_task: dict[str, str] | None = None) -> dict[str, Any]:
    """Map an existing cost-receipt / paid-call row. No fake IDs."""
    run_to_task = run_to_task or {}
    task = str(row.get("task_id") or "").strip()
    run = str(row.get("run_id") or "").strip()
    if not task and run and run in run_to_task:
        resolved = str(run_to_task[run]).strip()
        if resolved:
            task = resolved
    ts = str(row.get("created_at") or row.get("request_timestamp")
             or row.get("ts") or _utc())
    evidence = str(row.get("trace_id") or row.get("receipt_id") or row.get("input_sha256") or "")
    outcome = "ok"
    status = str(row.get("status") or row.get("receipt_status") or "").lower()
    if "error" in status or status in ("fail", "failed"):
        outcome = "error"
    if not task:
        outcome = "unattributed"
    return envelope(
        task_id=task or None,
        run_id=run or None,
        agent_id=str(row.get("process_id") or row.get("agent_id") or "legacy"),
        capability_id=str(row.get("capability_id") or "model.call.paid"),
        outcome=outcome,
        evidence_ref=evidence,
        timestamp_utc=ts if ts.endswith("Z") or "+" in ts else ts,
        receipt_id=str(row.get("receipt_id") or "") or None,
    )


def attribution_ratio(envelopes: list[dict]) -> dict[str, Any]:
    n = len(envelopes)
    attributed = sum(1 for e in envelopes if e.get("outcome") != "unattributed"
                     and str(e.get("task_id") or "").strip())
    ratio = (attributed / n) if n else 0.0
    return {
        "n": n,
        "attributed": attributed,
        "unattributed": n - attributed,
        "ratio": round(ratio, 4),
        "gate_95pct": ratio >= 0.95,
    }


def scan_jsonl(path, *, limit: int = 200000, run_to_task: dict[str, str] | None = None,
               since_iso: str | None = None) -> dict[str, Any]:
    from pathlib import Path
    p = Path(path)
    rows: list[dict] = []
    skipped_old = 0
    if p.exists():
        with p.open(encoding="utf-8", errors="replace") as f:
            for i, line in enumerate(f):
                if i >= limit:
                    break
                line = line.strip()
                if not line:
                    continue
                try:
                    raw = json.loads(line)
                except ValueError:
                    continue
                if since_iso:
                    ts = str(raw.get("created_at") or raw.get("request_timestamp")
                             or raw.get("ts") or "")
                    if ts and ts < since_iso:
                        skipped_old += 1
                        continue
                rows.append(adapt_legacy(raw, run_to_task=run_to_task))
    stats = attribution_ratio(rows)
    stats["source"] = str(p)
    stats["since_iso"] = since_iso
    stats["skipped_older_than_since"] = skipped_old
    return stats
