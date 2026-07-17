#!/usr/bin/env python3
"""knowledge_leg.py — WP-F · LEG-01: پای Knowledge (skeletonِ صادق، بدونِ منبعِ دادهٔ ماشینی).

قرارداد مشترک: helperِ فقط‌خواندنیِ سطحِ ماژول:
  knowledge_status() -> {"leg","live","signal","note"}

صداقت: پوشهٔ 07 - Knowledge پر از نوتِ دانشِ انسانی است، ولی هیچ پایپ‌لاینِ afferent یا
منبعِ دادهٔ ساختاریافته‌ای برای «پای Knowledge» به‌عنوان یک لِگِ بیزنسی سیم‌کشی نشده.
پس live=False تا مالک business-spec بدهد (این پا چه سیگنالی باید تولید کند؟).
برنامه ۷ (صداقتِ پاها): سنِ تازه‌ترین نوت (age_days، فقط stat) صادقانه گزارش می‌شود
تا دیدنی باشد آخرین بار کی دانشی وارد شده.

خط قرمز: هیچ سیگنالِ جعلی ساخته نمی‌شود. صفر side-effect، صفر secret. فقط گزارشِ صادقانه.
propose-only · $0 آفلاین · stdlib-only.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))
try:
    from leg_freshness import age_days
except ImportError:                                       # fail-soft: سنِ نامعلوم → null
    def age_days(_p):  # type: ignore[misc]
        return None

VAULT = _HERE.parents[1]                                  # _ops/legs → _ops → vault root
KNOWLEDGE_DIR = VAULT / "07 - Knowledge"


def _newest_note(kdir: Path) -> Path | None:
    """تازه‌ترین نوتِ markdown زیرِ پوشهٔ دانش (بر اساسِ mtime؛ فقط stat). fail-soft None."""
    try:
        notes = list(kdir.rglob("*.md"))
        return max(notes, key=lambda p: p.stat().st_mtime) if notes else None
    except (OSError, ValueError):
        return None


def knowledge_status() -> dict:
    """snapshotِ فقط‌خواندنیِ وضعیتِ پای Knowledge. هرگز crash نمی‌کند.
    منبعِ دادهٔ ماشینی/بیزنسی سیم‌کشی نشده → live=False (skeletonِ صادق)؛
    age_days = سنِ تازه‌ترین نوتِ 07 - Knowledge (گرد به ۰٫۱ روز، یا null)."""
    leg = "knowledge"
    try:
        has_notes = KNOWLEDGE_DIR.exists()
    except OSError:
        has_notes = False
    a = age_days(_newest_note(KNOWLEDGE_DIR)) if has_notes else None
    src = ("منبعِ دادهٔ واقعیِ بعدی: پایپ‌لاینِ afferent روی نوت‌های «07 - Knowledge» "
           + (f"(تازه‌ترین نوت ≈ {a:.0f} روز پیش)." if a is not None else "(نوتی stat نشد)."))
    note = (("skeleton — نوت‌های دانشِ انسانی هست ولی afferent/بیزنسی سیم‌کشی نشده. " if has_notes
             else "skeleton — no data source wired yet. ")
            + src + " نیازمندِ business-spec از مالک (این پا چه سیگنالی بدهد؟).")
    return {"leg": leg, "live": False, "signal": "skeleton",
            "age_days": round(a, 1) if a is not None else None, "note": note}


if __name__ == "__main__":
    print(json.dumps(knowledge_status(), ensure_ascii=False, indent=2))
