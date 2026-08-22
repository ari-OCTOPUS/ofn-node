# -*- coding: utf-8 -*-
"""Promotion ladder. Production only after owner lock + verifier.

Promote/merge refuses without test pass + evidence path + rollback plan.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .contracts import append_jsonl, utc_now
from . import STATE_DIR

LEVELS = ("NONE", "LAB_PASS", "SHADOW_PASS", "CANARY_PASS", "PRODUCTION_VERIFIED")
_LOCK = Path(__file__).resolve().parent.parent / "state" / "wave1" / "lock.json"


def _lock() -> dict:
    try:
        return json.loads(_LOCK.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def gate_promote(*, test_ok: bool = False,
                 evidence_path: str | Path | None = None,
                 rollback_plan: dict | str | None = None) -> dict[str, Any]:
    """Smallest additive gate: refuse promote/merge without required proofs.

    Required: test_ok True, evidence_path existing file, rollback_plan non-empty.
    """
    reasons: list[str] = []
    if not test_ok:
        reasons.append("test-not-pass")
    ep_raw = "" if evidence_path is None else str(evidence_path).strip()
    if not ep_raw:
        reasons.append("missing-evidence-path")
    else:
        ep = Path(ep_raw)
        if not ep.is_file():
            reasons.append("evidence-path-missing-file")
    if rollback_plan is None:
        reasons.append("missing-rollback-plan")
    elif isinstance(rollback_plan, str):
        if not rollback_plan.strip():
            reasons.append("missing-rollback-plan")
    elif isinstance(rollback_plan, dict):
        if not rollback_plan:
            reasons.append("missing-rollback-plan")
    else:
        reasons.append("invalid-rollback-plan")
    ok = not reasons
    return {
        "ok": ok,
        "allowed": ok,
        "reasons": reasons,
        "required": ["test_ok", "evidence_path", "rollback_plan"],
    }


def promote(*, experiment_id: str, verifier: dict, shadow: dict | None = None,
            canary_ok: bool = False,
            test_ok: bool = False,
            evidence_path: str | Path | None = None,
            rollback_plan: dict | str | None = None) -> dict[str, Any]:
    gate = gate_promote(test_ok=test_ok, evidence_path=evidence_path,
                        rollback_plan=rollback_plan)
    if not gate.get("ok"):
        rec = {
            "ts": utc_now(),
            "experiment_id": experiment_id,
            "level": "NONE",
            "production": False,
            "refused": True,
            "gate": gate,
            "note": "promote refused: need test pass + evidence path + rollback plan",
        }
        append_jsonl(STATE_DIR / "promotions.jsonl", rec)
        return rec

    lock = _lock()
    unlocked = lock.get("wave1_unlocked") is True
    writes = lock.get("memory_writes") is True
    level = "NONE"
    if verifier.get("confirmed"):
        level = "LAB_PASS"
        if shadow and int(shadow.get("n") or 0) >= 10 and shadow.get("mutations", 1) == 0:
            level = "SHADOW_PASS"
            if canary_ok:
                level = "CANARY_PASS"
                if unlocked and writes:
                    level = "PRODUCTION_VERIFIED"
    rec = {
        "ts": utc_now(),
        "experiment_id": experiment_id,
        "level": level,
        "production": level == "PRODUCTION_VERIFIED",
        "wave1_unlocked": unlocked,
        "memory_writes": writes,
        "refused": False,
        "gate": gate,
        "evidence_path": str(evidence_path) if evidence_path else None,
        "note": "PRODUCTION_VERIFIED requires owner lock + verifier + canary.",
    }
    append_jsonl(STATE_DIR / "promotions.jsonl", rec)
    return rec
