#!/usr/bin/env python3
"""Canonical LIVE-TELEGRAM.flag + writer-lock send gate.

Unlock (flag enabled) != send. Send only when an active send_exception
exists on the writer lock while respecting forbidden live sendMessage.
Reversible: delete this module / stop importing it.
"""
from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Any

LIVE_FLAG_NAME = "LIVE-TELEGRAM.flag"
DEFAULT_LOCK = Path(__file__).resolve().parents[1] / "state" / "locks" / "octopus-writer.lock"


def ops_root() -> Path:
    return Path(__file__).resolve().parents[1]


def flag_path() -> Path:
    env = str(os.environ.get("OCTOPUS_LIVE_TELEGRAM_FLAG", "")).strip()
    if env:
        return Path(env)
    return ops_root() / LIVE_FLAG_NAME


def read_flag(path: Path | None = None) -> dict[str, Any]:
    p = Path(path) if path is not None else flag_path()
    if not p.is_file():
        return {"present": False, "enabled": False, "path": str(p), "raw_schema": None, "note": "missing"}
    try:
        raw = json.loads(p.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {"present": True, "enabled": True, "path": str(p), "raw_schema": None, "note": "present_non_json_treated_as_enabled"}
    if not isinstance(raw, dict):
        return {"present": True, "enabled": True, "path": str(p), "raw_schema": None, "note": "present_non_object_treated_as_enabled"}
    enabled = bool(raw.get("enabled", True))
    return {"present": True, "enabled": enabled, "path": str(p), "raw_schema": raw.get("schema"), "note": raw.get("note"), "armed_at": raw.get("armed_at")}


def _read_lock(path: Path | None = None) -> dict[str, Any]:
    p = Path(path) if path is not None else Path(str(os.environ.get("OCTOPUS_WRITER_LOCK", "")).strip() or DEFAULT_LOCK)
    if not p.is_file():
        return {"present": False, "path": str(p), "data": {}}
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {"present": True, "path": str(p), "data": {}, "corrupt": True}
    return {"present": True, "path": str(p), "data": data if isinstance(data, dict) else {}}


def _active_send_exceptions(lock_data: dict[str, Any], *, now: float | None = None) -> list[dict]:
    now = time.time() if now is None else float(now)
    ex = lock_data.get("send_exceptions") or []
    if not isinstance(ex, list):
        return []
    active = []
    for row in ex:
        if not isinstance(row, dict):
            continue
        exp = row.get("expires_at")
        if exp is not None:
            try:
                if float(exp) < now:
                    continue
            except (TypeError, ValueError):
                continue
        active.append(row)
    return active


def evaluate(*, flag: Path | None = None, lock: Path | None = None, now: float | None = None) -> dict[str, Any]:
    f = read_flag(flag)
    lk = _read_lock(lock)
    data = lk.get("data") or {}
    forbidden = list(data.get("forbidden_actions") or [])
    live_send_forbidden = "live sendMessage" in forbidden
    exceptions = _active_send_exceptions(data, now=now)
    live_mode_allowed = bool(f.get("enabled"))
    send_allowed = bool(live_mode_allowed and exceptions)
    return {
        "schema": "live-telegram-gate/1",
        "flag": f,
        "lock_path": lk.get("path"),
        "lock_present": bool(lk.get("present")),
        "live_sendMessage_forbidden": live_send_forbidden,
        "active_send_exceptions": len(exceptions),
        "live_mode_allowed": live_mode_allowed,
        "send_allowed": send_allowed,
        "reason": (
            "send_allowed_via_exception" if send_allowed else (
                "flag_disabled_or_missing" if not live_mode_allowed else "no_active_send_exception"
            )
        ),
    }


def live_mode_allowed(**kwargs) -> bool:
    return bool(evaluate(**kwargs).get("live_mode_allowed"))


def send_allowed(**kwargs) -> bool:
    return bool(evaluate(**kwargs).get("send_allowed"))
