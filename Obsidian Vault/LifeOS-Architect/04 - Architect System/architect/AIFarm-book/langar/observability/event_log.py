"""
event_log.py — ثبتِ رویدادهای سیستم برای شفافیت.

روی جدولِ event_log در db می‌نویسد (db تزریق می‌شود تا تست‌پذیر بماند).
"""

from __future__ import annotations

import json


def log_event(db, etype: str, data: dict | None = None) -> None:
    if db is None:
        return
    try:
        db.log_event(etype, json.dumps(data or {}, ensure_ascii=False))
    except Exception:
        pass  # observability هرگز جریانِ اصلی را نمی‌شکند


def recent_events(db, n: int = 50):
    if db is None:
        return []
    try:
        return db.recent_events(n)
    except Exception:
        return []
