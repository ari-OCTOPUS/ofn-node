# -*- coding: utf-8 -*-
"""Read-only hunters for loops unit tests never catch.

No process mutation. No live send. No memory write.
"""
from __future__ import annotations

import ast
import json
from pathlib import Path
from typing import Any

_OPS = Path(__file__).resolve().parent.parent
_ROOT = _OPS.parent


def _read(rel: str) -> str:
    p = _ROOT / rel
    try:
        return p.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def hunt_dual_ingest() -> dict[str, Any]:
    """T-21: webhook + polling both active would duplicate ingestion."""
    center = _read("_ops/telegram_center/center.py")
    mentions_get = "getUpdates" in center
    mentions_webhook = "setWebhook" in center or "webhook" in center.lower()
    comment_no_get = "هرگز getUpdates صدا نمی‌زند" in center or "never getUpdates" in center
    return {
        "hunter": "D14_webhook_plus_polling",
        "center_mentions_getUpdates": mentions_get,
        "center_mentions_webhook": mentions_webhook,
        "comment_claims_no_getUpdates": comment_no_get,
        "verdict": "NO_DUAL_INGEST_IN_CENTER_SOURCE" if comment_no_get else "REVIEW",
        "note": "WORKLOCK: center.py not edited. Hunt is source-level.",
    }


def hunt_self_reply_ingest() -> dict[str, Any]:
    """Bot ingesting its own replies."""
    hits = []
    for rel in ("_ops/telegram_center/center.py",
                "_ops/loops/telegram_organ.py",
                "_ops/intel_spine/telegram_adapter.py"):
        text = _read(rel)
        if "from.id" in text or "from_id" in text or "is_bot" in text:
            hits.append(rel)
    return {
        "hunter": "D15_self_reply_ingest",
        "files_with_from_id": hits,
        "verdict": "NEEDS_EXPLICIT_BOT_ID_FILTER" if hits else "UNLOCATED",
        "note": "Explicit skip when from.id == bot_id must exist before live ingest.",
    }


def hunt_green_heartbeat_dead_worker() -> dict[str, Any]:
    """D17 / doctor-pulse pattern."""
    hb = _ROOT / "_memory/HEARTBEAT.md"
    missions = _ROOT / "OCTOPUS-DOCTOR/90-_meta/state/missions.json"
    open_n = 0
    stale = []
    if missions.is_file():
        try:
            raw = json.loads(missions.read_text(encoding="utf-8"))
            for m in raw if isinstance(raw, list) else []:
                if isinstance(m, dict) and m.get("state") in (
                        "proposed", "running", "awaiting-merge"):
                    open_n += 1
                    stale.append({"id": m.get("mission_id"), "state": m.get("state"),
                                  "created": m.get("created")})
        except (OSError, ValueError):
            pass
    return {
        "hunter": "D17_green_heartbeat_dead_worker",
        "heartbeat_exists": hb.is_file(),
        "open_missions": open_n,
        "open_preview": stale[:5],
        "verdict": "DEADLOCK_CANDIDATE" if open_n else "NO_OPEN_MISSION_IN_FILE",
        "read_only": True,
        "did_not_quarantine_live": True,
    }


def hunt_constant_04() -> dict[str, Any]:
    text = _read("_ops/doctor/self_knowledge.py")
    assign = "confidence = 0.4" in text or "confidence=0.4" in text
    ema = "_accuracy_ema" in text
    return {
        "hunter": "D08_constant_0_4",
        "literal_assign_0_4": assign,
        "ema_present": ema,
        "verdict": "HARDCODE_GONE_EMA_PRESENT" if (not assign and ema) else "STILL_HARDCODED",
    }


def hunt_calibration_reader() -> dict[str, Any]:
    text = _read("_ops/cortex/improve.py")
    reads = "calibration-latest.json" in text and "gather_signals" in text
    return {
        "hunter": "D07_calibration_reader",
        "improve_reads_calibration_latest": reads,
        "verdict": "WIRED_IN_WORKING_TREE" if reads else "DEAD_OUTPUT",
    }


def hunt_all() -> dict[str, Any]:
    rows = [
        hunt_dual_ingest(),
        hunt_self_reply_ingest(),
        hunt_green_heartbeat_dead_worker(),
        hunt_constant_04(),
        hunt_calibration_reader(),
    ]
    return {"schema": "defect-hunt/1", "n": len(rows), "hunts": rows,
            "paid_calls": 0, "memory_writes": 0, "wave1_unlocked": False}
