# -*- coding: utf-8 -*-
"""Promotion ladder. Production only after owner lock + verifier."""
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


def promote(*, experiment_id: str, verifier: dict, shadow: dict | None = None,
            canary_ok: bool = False) -> dict[str, Any]:
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
        "note": "PRODUCTION_VERIFIED requires owner lock + verifier + canary.",
    }
    append_jsonl(STATE_DIR / "promotions.jsonl", rec)
    return rec
