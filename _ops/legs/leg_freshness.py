#!/usr/bin/env python3
"""leg_freshness.py — قراردادِ مشترکِ تازگیِ داده برای پاهای بیزنسی (برنامه ۷ — صداقتِ پاها).

«live» یعنی «داده جریان دارد»، نه «فایلی وجود دارد». هر پا در status() خودش این دو
helperِ فقط‌خواندنی را صدا می‌زند — ارزیابی در لحظهٔ فراخوانی (هرگز cacheِ سطحِ ماژول):

  age_days(path)        -> float | None   سنِ mtime به روز؛ None اگر مسیر نبود/stat نشد (fail-soft)
  fresh(path, max_days) -> bool           True فقط اگر سن معلوم و <= max_days (سنِ نامعلوم → False)

خط قرمز: صفر side-effect، صفر خواندنِ محتوا (فقط stat — بی‌PII)، stdlib-only.
"""
from __future__ import annotations

import time
from pathlib import Path

_DAY_S = 86400.0


def age_days(path: Path | str | None) -> float | None:
    """سنِ فایل/پوشه به روز، بر اساسِ mtime، محاسبه در لحظهٔ فراخوانی.

    fail-soft: مسیرِ None/ناموجود/غیرقابل‌stat → None (هرگز exception).
    mtimeِ آینده (ساعتِ کج) → 0.0 (سنِ منفی گزارش نمی‌شود)."""
    if path is None:
        return None
    try:
        mtime = Path(path).stat().st_mtime
    except (OSError, ValueError):
        return None
    age = (time.time() - mtime) / _DAY_S
    return age if age >= 0.0 else 0.0


def fresh(path: Path | str | None, max_days: float) -> bool:
    """True فقط وقتی سنِ داده معلوم و <= max_days باشد.

    fail-closed برای صداقت: سنِ نامعلوم (فایلِ گمشده/خطای stat) → False، نه True —
    «نمی‌دانم» هرگز «زنده» گزارش نمی‌شود."""
    a = age_days(path)
    return a is not None and a <= float(max_days)
