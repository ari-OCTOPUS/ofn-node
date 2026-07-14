#!/usr/bin/env python3
"""accounting_leg.py — WP-F · LEG-01: پای Accounting (status صادق، بی‌PII).

قرارداد مشترک: helperِ فقط‌خواندنیِ سطحِ ماژول:
  accounting_status() -> {"leg","live","signal","note"}

صداقت + خط‌قرمزِ PII: منبعِ دادهٔ واقعی (workbookهای xlsx در پوشهٔ Accounting) وجود دارد،
ولی این‌ها PII دارند. مثلِ ingest_raw، این پا **هرگز** مقدار/ردیف/نام نمی‌خواند —
فقط *وجود و تعدادِ* workbookها را می‌شمارد (ساختار، صفر مقدار). live=True چون منبع هست،
سیگنال = تعدادِ workbook (بدونِ هیچ عدد/نامِ مالی).

خط قرمز: صفر echoِ مقدار/نام، صفر منطقِ حساب‌داریِ جعلی، صفر side-effect، صفر secret.
propose-only · $0 آفلاین · stdlib-only · منبعِ خام دست‌نخورده.
"""
from __future__ import annotations

import json
from pathlib import Path

_HERE = Path(__file__).resolve().parent
VAULT = _HERE.parents[1]                                  # _ops/legs → _ops → vault root
# همان مسیرِ ingest_raw.ACCT (workbookهای مالی — PII؛ فقط شمارش، صفر خواندنِ مقدار)
ACCT_DIR = VAULT / "03 - Projects" / "Accounting" / "data" / "حساب کتاب"


def accounting_status() -> dict:
    """snapshotِ فقط‌خواندنیِ وضعیتِ پای Accounting. هرگز crash نمی‌کند.
    ⚠️ صفر مقدار/نام/عددِ مالی خوانده یا echo نمی‌شود — فقط *تعدادِ* workbook (وجودِ منبع).
    live=True اگر workbookی موجود باشد؛ سیگنالِ بی‌PII."""
    leg = "accounting"
    adir = ACCT_DIR
    try:
        exists = adir.exists()
    except OSError:
        exists = False
    if not exists:
        return {"leg": leg, "live": False, "signal": "no-data",
                "note": "پوشهٔ Accounting پیدا نشد — skeleton، منتظرِ afferent/ingest."}
    try:
        n_wb = len(list(adir.glob("*.xlsx")))
    except OSError:
        n_wb = 0
    if n_wb > 0:
        return {"leg": leg, "live": True, "signal": f"workbooks={n_wb}",
                "note": ("منبعِ مالی موجود — فقط تعدادِ workbook شمرده شد؛ "
                         "صفر مقدار/نام/عدد خوانده شد (خط‌قرمزِ PII، فقط‌خواندنی).")}
    return {"leg": leg, "live": False, "signal": "empty",
            "note": "پوشهٔ Accounting هست ولی بدونِ workbook — skeleton."}


if __name__ == "__main__":
    print(json.dumps(accounting_status(), ensure_ascii=False, indent=2))
