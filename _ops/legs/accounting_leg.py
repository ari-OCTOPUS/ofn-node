#!/usr/bin/env python3
"""accounting_leg.py — WP-F · LEG-01: پای Accounting (status صادق، بی‌PII).

قرارداد مشترک: helperِ فقط‌خواندنیِ سطحِ ماژول:
  accounting_status() -> {"leg","live","signal","note"}

صداقت + خط‌قرمزِ PII: منبعِ دادهٔ واقعی (workbookهای xlsx در پوشهٔ Accounting) وجود دارد،
ولی این‌ها PII دارند. مثلِ ingest_raw، این پا **هرگز** مقدار/ردیف/نام نمی‌خواند —
فقط *وجود، تعداد و mtimeِ* workbookها (metadata، صفر مقدار). برنامه ۷ (صداقتِ پاها):
live=True فقط وقتی تازه‌ترین workbook ≤ ACCT_MAX_AGE_DAYS روز لمس شده باشد —
«داده جریان دارد»، نه «فایلی وجود دارد». سیگنال = تعدادِ workbook + کلیدِ افزودهٔ age_days.

خط قرمز: صفر echoِ مقدار/نام، صفر منطقِ حساب‌داریِ جعلی، صفر side-effect، صفر secret.
propose-only · $0 آفلاین · stdlib-only · منبعِ خام دست‌نخورده.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))
try:
    from leg_freshness import age_days, fresh
except ImportError:                                       # fail-closed: سنِ نامعلوم → live=False
    def age_days(_p):  # type: ignore[misc]
        return None

    def fresh(_p, _d):  # type: ignore[misc]
        return False

VAULT = _HERE.parents[1]                                  # _ops/legs → _ops → vault root
# همان مسیرِ ingest_raw.ACCT (workbookهای مالی — PII؛ فقط شمارش/mtime، صفر خواندنِ مقدار)
ACCT_DIR = VAULT / "03 - Projects" / "Accounting" / "data" / "حساب کتاب"
# آستانهٔ تازگی: چرخهٔ دفترها ماهانه است — >~۳۵ روز دست‌نخورده یعنی داده جریان ندارد.
ACCT_MAX_AGE_DAYS = 35.0


def accounting_status() -> dict:
    """snapshotِ فقط‌خواندنیِ وضعیتِ پای Accounting. هرگز crash نمی‌کند.
    ⚠️ صفر مقدار/نام/عددِ مالی خوانده یا echo نمی‌شود — فقط تعداد + mtimeِ workbookها (metadata).
    برنامه ۷: live=True فقط اگر تازه‌ترین workbook تازه باشد (fresh ≤ ACCT_MAX_AGE_DAYS)؛
    age_days = سنِ تازه‌ترین workbook (گرد به ۰٫۱ روز، یا null). سیگنالِ بی‌PII."""
    leg = "accounting"
    adir = ACCT_DIR
    try:
        exists = adir.exists()
    except OSError:
        exists = False
    if not exists:
        return {"leg": leg, "live": False, "signal": "no-data", "age_days": None,
                "note": "پوشهٔ Accounting پیدا نشد — skeleton، منتظرِ afferent/ingest."}
    try:
        wbs = list(adir.glob("*.xlsx"))
    except OSError:
        wbs = []
    n_wb = len(wbs)
    if n_wb > 0:
        try:
            newest = max(wbs, key=lambda p: p.stat().st_mtime)
        except (OSError, ValueError):
            newest = None
        a = age_days(newest)
        live = fresh(newest, ACCT_MAX_AGE_DAYS)
        return {"leg": leg, "live": live, "signal": f"workbooks={n_wb}",
                "age_days": round(a, 1) if a is not None else None,
                "note": ("منبعِ مالی موجود — فقط تعداد/mtimeِ workbook دیده شد؛ "
                         "صفر مقدار/نام/عدد خوانده شد (خط‌قرمزِ PII، فقط‌خواندنی). "
                         + (f"دادهٔ تازه (≤{ACCT_MAX_AGE_DAYS:g} روز) — جریان دارد."
                            if live else
                            f"workbookها >{ACCT_MAX_AGE_DAYS:g} روز دست‌نخورده‌اند → "
                            f"live=False (داده جریان ندارد)."))}
    return {"leg": leg, "live": False, "signal": "empty", "age_days": None,
            "note": "پوشهٔ Accounting هست ولی بدونِ workbook — skeleton."}


if __name__ == "__main__":
    print(json.dumps(accounting_status(), ensure_ascii=False, indent=2))
