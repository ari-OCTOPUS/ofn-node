#!/usr/bin/env python3
"""Canary window guard — strict sequence, duplicates recorded without advancing.

The 2026-08-21 window failed because the protocol was not enforced in code:
commands were free text, duplicates created distinct tasks, and the sequence
was not checked. This module enforces the protocol at ingestion:

- A window has a canary_id and a nonce.
- Expected sequence is CANARY-01..CANARY-05 (labels are optional in text).
- A recognized next command advances the sequence.
- A duplicate of an already-seen command is RECORDED and does NOT advance.
- Anything else is OUT_OF_ORDER (recorded, no advance, no dispatch).
- State is durable (state/telegram/loop/canary-window.json) and crash-resumable.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import time
import uuid
from pathlib import Path

_OPS = Path(__file__).resolve().parent.parent

SEQUENCE = ["CANARY-01", "CANARY-02", "CANARY-03", "CANARY-04", "CANARY-05"]
_LABEL = re.compile(r"^CANARY-0([1-5])\b", re.IGNORECASE)


def hash_text(text: str) -> str:
    """پای‌لود‌هشِ متنی برای بایندِ ردیف (کوتاه، نه برای امنیت)."""
    return hashlib.sha256(str(text or "").encode("utf-8")).hexdigest()[:16]


def _state_dir() -> Path:
    base = str(os.environ.get("OCTOPUS_STATE_DIR", "") or "").strip()
    return Path(base) if base else (_OPS / "state")


def _path() -> Path:
    return _state_dir() / "telegram" / "loop" / "canary-window.json"


def _load() -> dict:
    try:
        if _path().is_file():
            d = json.loads(_path().read_text(encoding="utf-8"))
            if isinstance(d, dict):
                return d
    except (OSError, ValueError):
        pass
    return {}


def _save(d: dict) -> None:
    try:
        p = _path()
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(d, ensure_ascii=False), encoding="utf-8")
    except OSError:
        pass


def open_window(canary_id: str | None = None) -> dict:
    """Open a new window with a fresh nonce. Fails if a window is already open."""
    state = _load()
    if state.get("open"):
        return {"ok": False, "reason": "window_already_open",
                "canary_id": state.get("canary_id")}
    win = {"canary_id": canary_id or f"CANARY-{uuid.uuid4().hex[:8]}",
           "nonce": uuid.uuid4().hex[:16],
           "open": True,
           "next_index": 0,
           "seen": [],            # [{command, update_id, decision, ts}]
           "opened_at": time.time()}
    _save(win)
    return {"ok": True, **win}


def observe(text: str, update_id: int, now: float | None = None,
            payload_hash: str | None = None) -> dict:
    """Classify an inbound message against the open window.

    ACCEPTED  — matches the expected next command; sequence advances.
    DUPLICATE — command already seen OR update_id already seen; recorded,
                sequence NOT advanced.
    OUT_OF_ORDER — not the expected command; recorded, no advance.
    UNKNOWN   — no CANARY-0X label at all.
    NO_WINDOW — no open window.

    Every row is bound to update_id, payload hash (when supplied), and the
    window's canary_id + nonce. Repeating an update_id (crash replay) is
    recorded as DUPLICATE so a replayed update can never advance or dispatch
    twice.
    """
    state = _load()
    now = float(now if now is not None else time.time())
    if not state.get("open"):
        return {"ok": False, "decision": "NO_WINDOW"}
    base = {"canary_id": state.get("canary_id"), "nonce": state.get("nonce")}
    if payload_hash:
        base["payload_hash"] = str(payload_hash)[:64]
    m = _LABEL.match(str(text or "").strip())
    if not m:
        row = {"command": None, "update_id": update_id, "decision": "UNKNOWN",
               "ts": now, **base}
        state.setdefault("seen", []).append(row)
        _save(state)
        return {"ok": False, "decision": "UNKNOWN", "row": row}
    command = "CANARY-0" + m.group(1)
    idx = int(m.group(1)) - 1
    seen = state.get("seen") or []
    if any(s.get("update_id") == update_id for s in seen):
        row = {"command": command, "update_id": update_id, "decision": "DUPLICATE",
               "reason": "repeat_update_id", "ts": now, **base}
        state["seen"].append(row)
        _save(state)
        return {"ok": False, "decision": "DUPLICATE", "row": row}
    already = [s for s in seen if s.get("command") == command]
    if already:
        row = {"command": command, "update_id": update_id, "decision": "DUPLICATE",
               "reason": "repeat_command", "ts": now, **base}
        state["seen"].append(row)
        _save(state)
        return {"ok": False, "decision": "DUPLICATE", "row": row}
    if idx != int(state.get("next_index") or 0):
        row = {"command": command, "update_id": update_id, "decision": "OUT_OF_ORDER",
               "expected": SEQUENCE[int(state.get("next_index") or 0)], "ts": now,
               **base}
        state["seen"].append(row)
        _save(state)
        return {"ok": False, "decision": "OUT_OF_ORDER", "row": row}
    row = {"command": command, "update_id": update_id, "decision": "ACCEPTED",
           "ts": now, **base}
    state["seen"].append(row)
    state["next_index"] = int(state.get("next_index") or 0) + 1
    if state["next_index"] >= len(SEQUENCE):
        state["open"] = False
        state["closed_at"] = now
        state["completed"] = True
    _save(state)
    return {"ok": True, "decision": "ACCEPTED", "row": row,
            "next": SEQUENCE[state["next_index"]] if state.get("open") else None}


def close_window() -> dict:
    state = _load()
    state["open"] = False
    state["closed_at"] = time.time()
    _save(state)
    return {"ok": True}


def window_status() -> dict:
    state = _load()
    return {"open": bool(state.get("open")), "canary_id": state.get("canary_id"),
            "nonce": state.get("nonce"), "next_index": state.get("next_index"),
            "next_expected": SEQUENCE[int(state.get("next_index") or 0)]
            if state.get("open") else None,
            "seen": state.get("seen") or [], "completed": bool(state.get("completed"))}
