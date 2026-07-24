#!/usr/bin/env python3
"""events.py — wrapper سبک روی events.py مرکزیِ اختاپوس.

events.py مرکزی (طبقِ کاوشِ 2026-07-19) یک **logger ساختاریافته** است، نه bus.
ما فقط emit می‌کنیم (append-only به _ops/state/events.jsonl) — هرگز subscription
یا mutation. تمام ایمپورت‌ها اختیاری‌اند تا اگر _ops در scope نباشد، fail-soft شود.

agent_id پیش‌فرضِ همه‌ی emitهای ما = "pf_os" (هویتِ واحدِ OS جدید).
correlation_id از contextvars به ارث می‌رسد اگر set شده باشد.

$0 آفلاین، stdlib-only، fail-soft.
"""
from __future__ import annotations

import sys
from typing import Optional

from . import config

_OPS = config.VAULT + "/_ops"
if _OPS not in sys.path:
    sys.path.insert(0, _OPS)

_emit = None  # lazy
_begin_run = None
_end_run = None
_AVAILABLE: Optional[bool] = None

AGENT = "pf_os"


def _ensure():
    """lazy import — اگر _ops/events.py نبود، fail-soft."""
    global _emit, _begin_run, _end_run, _AVAILABLE
    if _AVAILABLE is not None:
        return _AVAILABLE
    try:
        import events as _ev  # noqa: E402
        _emit = getattr(_ev, "emit", None)
        _begin_run = getattr(_ev, "begin_run", None)
        _end_run = getattr(_ev, "end_run", None)
        _AVAILABLE = callable(_emit)
    except Exception:  # noqa: BLE001
        _AVAILABLE = False
    return _AVAILABLE


def emit(event_name: str, *, status: str = "ok", summary: str = "",
         duration_ms: int = 0, next_action: str = "",
         approval_state: str = "unknown") -> bool:
    """emit به events.jsonl مرکزی. True اگر موفق، False اگر fail-soft (نبودِ events).

    event_name باید یکی از ۷ نوعِ شناخته‌شده باشد (طبقِ _ops/events.py:33):
      task.started, task.completed, task.failed, task.blocked,
      handoff.created, system.heartbeat, approval.required

    هرگز PII/محتوا در summary نمی‌ریزیم — فقط metadata (content-free).
    """
    if not _ensure():
        return False  # fail-soft: _ops در scope نیست (تست/shadow)
    try:
        _emit(event_name, AGENT, status=status,
              summary=str(summary)[:300],
              duration_ms=int(duration_ms),
              next_action=str(next_action)[:200],
              approval_state=approval_state)
        return True
    except Exception:  # noqa: BLE001
        return False


def begin_run(correlation_id: str = ""):
    """شروعِ یک run با correlation_id مشترک. اختیاری."""
    if not _ensure() or not callable(_begin_run):
        return None
    try:
        return _begin_run(correlation_id)
    except Exception:  # noqa: BLE001
        return None


def end_run(token) -> None:
    """پایانِ run. token از begin_run آمده."""
    if not _ensure() or not callable(_end_run) or token is None:
        return
    try:
        _end_run(token)
    except Exception:  # noqa: BLE001
        pass


def available() -> bool:
    """آیا events.py مرکزی در scope است؟"""
    return bool(_ensure())
