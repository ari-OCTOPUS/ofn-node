#!/usr/bin/env python3
"""knowledge_leg.py — WP-F · LEG-01: پای Knowledge (skeletonِ صادق، بدونِ منبعِ دادهٔ ماشینی).

قرارداد مشترک: helperِ فقط‌خواندنیِ سطحِ ماژول:
  knowledge_status() -> {"leg","live","signal","note"}

صداقت: پوشهٔ 07 - Knowledge پر از نوتِ دانشِ انسانی است، ولی هیچ پایپ‌لاینِ afferent یا
منبعِ دادهٔ ساختاریافته‌ای برای «پای Knowledge» به‌عنوان یک لِگِ بیزنسی سیم‌کشی نشده.
پس live=False تا مالک business-spec بدهد (این پا چه سیگنالی باید تولید کند؟).

خط قرمز: هیچ سیگنالِ جعلی ساخته نمی‌شود. صفر side-effect، صفر secret. فقط گزارشِ صادقانه.
propose-only · $0 آفلاین · stdlib-only.
"""
from __future__ import annotations

import json
from pathlib import Path

_HERE = Path(__file__).resolve().parent
VAULT = _HERE.parents[1]                                  # _ops/legs → _ops → vault root
KNOWLEDGE_DIR = VAULT / "07 - Knowledge"


def knowledge_status() -> dict:
    """snapshotِ فقط‌خواندنیِ وضعیتِ پای Knowledge. هرگز crash نمی‌کند.
    منبعِ دادهٔ ماشینی/بیزنسی سیم‌کشی نشده → live=False (skeletonِ صادق)."""
    leg = "knowledge"
    try:
        has_notes = KNOWLEDGE_DIR.exists()
    except OSError:
        has_notes = False
    note = ("skeleton — نوت‌های دانشِ انسانی هست ولی منبعِ دادهٔ afferent/بیزنسی سیم‌کشی نشده؛ "
            "نیازمندِ business-spec از مالک (این پا چه سیگنالی بدهد؟)."
            if has_notes else
            "skeleton — no data source wired yet؛ نیازمندِ business-spec از مالک.")
    return {"leg": leg, "live": False, "signal": "skeleton", "note": note}


if __name__ == "__main__":
    print(json.dumps(knowledge_status(), ensure_ascii=False, indent=2))
