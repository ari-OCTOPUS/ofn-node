#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""audit_logger.py — append structured audit records to _ops/state/action-audit.jsonl

Fields:
  timestamp, action_id, actor, action_type
  pre_action_snapshot (hashes/keys)
  proposal_rationale, verdict, verdict_owner
  execution_mode: dry_run / shadow / live
  result: success / failure / cancelled / expired
  rollback_class: reversible / irreversible / requires_manual / unknown

Usage (import or CLI):
  python audit_logger.py --action-id X --actor owner --action-type approve ...
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

AUDIT_LOG = Path("F:/backup/_ops/state/action-audit.jsonl")

ROLLBACK_CLASSES = frozenset({"reversible", "irreversible", "requires_manual", "unknown"})
EXECUTION_MODES = frozenset({"dry_run", "shadow", "live"})
RESULTS = frozenset({"success", "failure", "cancelled", "expired"})


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _hash_snapshot(data: dict[str, Any]) -> str:
    """Simple deterministic hash for pre-action snapshot."""
    canonical = json.dumps(data, ensure_ascii=False, sort_keys=True, default=str)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:16]


def log(
    action_id: str,
    actor: str,
    action_type: str,
    *,
    pre_action_snapshot: dict[str, Any] | None = None,
    proposal_rationale: str = "",
    verdict: str | None = None,
    verdict_owner: str | None = None,
    execution_mode: str = "dry_run",
    result: str = "success",
    rollback_class: str = "unknown",
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if execution_mode not in EXECUTION_MODES:
        raise ValueError(f"execution_mode must be one of {EXECUTION_MODES}")
    if result not in RESULTS:
        raise ValueError(f"result must be one of {RESULTS}")
    if rollback_class not in ROLLBACK_CLASSES:
        raise ValueError(f"rollback_class must be one of {ROLLBACK_CLASSES}")

    record: dict[str, Any] = {
        "timestamp": _now_iso(),
        "action_id": action_id,
        "actor": actor,
        "action_type": action_type,
        "pre_action_snapshot": {
            "hash": _hash_snapshot(pre_action_snapshot or {}),
            "keys": list((pre_action_snapshot or {}).keys()),
        },
        "proposal_rationale": proposal_rationale,
        "verdict": verdict,
        "verdict_owner": verdict_owner,
        "execution_mode": execution_mode,
        "result": result,
        "rollback_class": rollback_class,
        "extra": extra or {},
    }

    try:
        AUDIT_LOG.parent.mkdir(parents=True, exist_ok=True)
        with open(AUDIT_LOG, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False, default=str) + "\n")
    except OSError as exc:
        record["_write_error"] = str(exc)

    return record


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit Logger CLI")
    parser.add_argument("--action-id", required=True)
    parser.add_argument("--actor", required=True)
    parser.add_argument("--action-type", required=True)
    parser.add_argument("--proposal-rationale", default="")
    parser.add_argument("--verdict", default=None)
    parser.add_argument("--verdict-owner", default=None)
    parser.add_argument("--execution-mode", default="dry_run", choices=EXECUTION_MODES)
    parser.add_argument("--result", default="success", choices=RESULTS)
    parser.add_argument("--rollback-class", default="unknown", choices=ROLLBACK_CLASSES)
    args = parser.parse_args()

    record = log(
        action_id=args.action_id,
        actor=args.actor,
        action_type=args.action_type,
        proposal_rationale=args.proposal_rationale,
        verdict=args.verdict,
        verdict_owner=args.verdict_owner,
        execution_mode=args.execution_mode,
        result=args.result,
        rollback_class=args.rollback_class,
    )
    print(json.dumps(record, ensure_ascii=False, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
