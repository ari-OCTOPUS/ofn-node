#!/usr/bin/env python3
"""mining_leg.py — WP-F · LEG-01: پای Mining (skeletonِ صادق، بدونِ منبعِ دادهٔ ماشینی).

قرارداد مشترک: helperِ فقط‌خواندنیِ سطحِ ماژول:
  mining_status() -> {"leg","live","signal","note"}

صداقت: پروژهٔ Mining فقط اسنادِ markdown دارد (PROJECT/runbook/research) — هیچ منبعِ
دادهٔ ساختاریافته یا پایپ‌لاینِ afferent برایش سیم‌کشی نشده. پس live=False. هیچ عددِ
هش‌ریت/سود/برقِ جعلی ساخته نمی‌شود؛ این کار نیازمندِ business-spec از مالک است.

خط قرمز: صفر منطقِ درآمد/انرژیِ جعلی، صفر side-effect، صفر secret. فقط گزارشِ صادقانهٔ «هنوز خام».
propose-only · $0 آفلاین · stdlib-only.
"""
from __future__ import annotations

import json
from pathlib import Path

_HERE = Path(__file__).resolve().parent
VAULT = _HERE.parents[1]                                  # _ops/legs → _ops → vault root
# پوشهٔ پروژه (فقط اسنادِ انسانی؛ منبعِ دادهٔ ماشینی نیست)
PROJECT_DIR = VAULT / "03 - Projects" / "Mining"


def mining_status() -> dict:
    """snapshotِ فقط‌خواندنیِ وضعیتِ پای Mining. هرگز crash نمی‌کند.
    منبعِ دادهٔ ماشینی سیم‌کشی نشده → live=False (skeletonِ صادق)."""
    leg = "mining"
    try:
        has_docs = PROJECT_DIR.exists()
    except OSError:
        has_docs = False
    note = ("skeleton — هیچ منبعِ دادهٔ ماشینی سیم‌کشی نشده؛ نیازمندِ business-spec از مالک "
            "(هش‌ریت/برق/سود). اسنادِ پروژه هست ولی داده‌ی afferent نیست."
            if has_docs else
            "skeleton — no data source wired yet؛ نیازمندِ business-spec از مالک.")
    return {"leg": leg, "live": False, "signal": "skeleton", "note": note}


if __name__ == "__main__":
    print(json.dumps(mining_status(), ensure_ascii=False, indent=2))
