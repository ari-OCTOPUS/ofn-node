#!/usr/bin/env python3
"""mining_leg.py — WP-F · LEG-01: پای Mining (skeletonِ صادق، بدونِ منبعِ دادهٔ ماشینی).

قرارداد مشترک: helperِ فقط‌خواندنیِ سطحِ ماژول:
  mining_status() -> {"leg","live","signal","note"}

صداقت: پروژهٔ Mining دادهٔ ماشینیِ واقعی دارد (تصمیم‌های coordinatorِ ربات‌ها در
DECISIONS_PATH) ولی هیچ پایپ‌لاینِ afferent/scorerی به این پا سیم‌کشی نشده → live=False
می‌ماند (scorerِ زنده جعل نمی‌شود). برنامه ۷ (صداقتِ پاها): سنِ همان منبعِ واقعی
(age_days، فقط stat) صادقانه گزارش می‌شود تا راکد بودنِ داده دیدنی باشد.

خط قرمز: صفر منطقِ درآمد/انرژیِ جعلی، صفر side-effect، صفر secret. فقط گزارشِ صادقانهٔ «هنوز خام».
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
# پوشهٔ پروژه (فقط اسنادِ انسانی؛ منبعِ دادهٔ ماشینی نیست)
PROJECT_DIR = VAULT / "03 - Projects" / "Mining"
# منبعِ دادهٔ ماشینیِ واقعیِ بعدی: تصمیم‌های coordinatorِ ربات‌های Ai (فقط stat، صفر خواندنِ محتوا)
# مسیرِ واقعی (تأییدشده روی درختِ زنده): coordinator/data/decisions.jsonl
DECISIONS_PATH = (VAULT / "03 - Projects" / "Mining" / "02 - Code" / "Ai bots"
                  / "coordinator" / "data" / "decisions.jsonl")


def mining_status() -> dict:
    """snapshotِ فقط‌خواندنیِ وضعیتِ پای Mining. هرگز crash نمی‌کند.
    scorer/afferent سیم‌کشی نشده → live=False (skeletonِ صادق)؛ ولی age_days سنِ
    منبعِ دادهٔ واقعی (coordinator/data/decisions.jsonl) را صادقانه گزارش می‌کند."""
    leg = "mining"
    try:
        has_docs = PROJECT_DIR.exists()
    except OSError:
        has_docs = False
    a = age_days(DECISIONS_PATH)
    if a is not None:
        src = (f"منبعِ دادهٔ واقعیِ بعدی: «02 - Code/Ai bots/coordinator/data/decisions.jsonl» "
               f"(سن ≈ {a:.0f} روز — راکد؛ تا جریانِ تازه، scorerِ زنده جعل نمی‌شود).")
    else:
        src = ("منبعِ دادهٔ واقعیِ بعدی: «02 - Code/Ai bots/coordinator/data/decisions.jsonl» — "
               "فایل پیدا نشد.")
    note = (("skeleton — اسنادِ پروژه هست ولی afferent/scorer سیم‌کشی نشده. " if has_docs else
             "skeleton — no data source wired yet. ")
            + src + " نیازمندِ business-spec از مالک (هش‌ریت/برق/سود).")
    return {"leg": leg, "live": False, "signal": "skeleton",
            "age_days": round(a, 1) if a is not None else None, "note": note}


if __name__ == "__main__":
    print(json.dumps(mining_status(), ensure_ascii=False, indent=2))
