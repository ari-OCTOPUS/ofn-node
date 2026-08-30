#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""tg_poller_lease.py — گارد «یک bot_id → حداکثر یک poller» (نکتهٔ ۲ مالک، ۱۴A).

مکانیزم: فایل قفل اتمیک per token-fingerprint در _ops/state/locks/ با pid.
- poller دوم روی همان token ⇒ REFUSE_TO_START (به‌جای 409 جنگیدن).
- قفل با pid مرده = STALE → بایگانی و takeover صریح (الگوی writer_lease).
- acquire به‌ازای فرآیند یک بار؛ release اختیاری در خروج تمیز."""
from __future__ import annotations

import hashlib
import json
import os
import sys
import time
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
LOCK_DIR = _ROOT / "state" / "locks"


def _fp(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()[:12]


def _pid_alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


def acquire(token: str, poller_id: str) -> tuple[bool, str]:
    """(ok, reason). ok=False ⇒ REFUSE_TO_START (poller دیگری فعال است)."""
    LOCK_DIR.mkdir(parents=True, exist_ok=True)
    lock = LOCK_DIR / f"tg-poller-{_fp(token)}.lock"
    try:
        rec = json.loads(lock.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        rec = None
    if rec is not None and _pid_alive(int(rec.get("pid", -1))):
        if rec.get("poller_id") == poller_id:
            return True, "already-holder"
        return False, f"REFUSE_TO_START: poller {rec['poller_id']} pid={rec['pid']} active on this bot"
    if rec is not None:
        stale = lock.with_name(f"{lock.name}.stale.{int(time.time())}")
        os.replace(lock, stale)
    payload = {"schema": "tg-poller-lease/1", "poller_id": poller_id,
               "pid": os.getpid(), "token_fp": _fp(token),
               "acquired_at": time.time()}
    fd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        f.write(json.dumps(payload, ensure_ascii=False))
    return True, "ACQUIRED"


def release(token: str, poller_id: str) -> None:
    lock = LOCK_DIR / f"tg-poller-{_fp(token)}.lock"
    try:
        rec = json.loads(lock.read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        return
    if rec.get("poller_id") == poller_id:
        os.replace(lock, lock.with_name(f"{lock.name}.released.{int(time.time())}"))
