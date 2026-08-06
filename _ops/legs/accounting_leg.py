#!/usr/bin/env python3
"""accounting_leg.py — WP-F · LEG-01: پای Accounting (status صادق، بی‌PII).

قرارداد مشترک: helperِ فقط‌خواندنیِ سطحِ ماژول:
  accounting_status() -> {"leg","live","signal","note"}

صداقت + خط‌قرمزِ PII: منبعِ دادهٔ واقعی (workbookهای xlsx در پوشهٔ Accounting) وجود دارد،
ولی این‌ها PII دارند. مثلِ ingest_raw، این پا **هرگز** مقدار/ردیف/نام نمی‌خواند —
فقط *وجود، تعداد و mtimeِ* workbookها (metadata، صفر مقدار). برنامه ۷ (صداقتِ پاها):
live=True فقط وقتی تازه‌ترین workbook ≤ ACCT_MAX_AGE_DAYS روز لمس شده باشد —
«داده جریان دارد»، نه «فایلی وجود دارد». سیگنال = تعدادِ workbook + کلیدِ افزودهٔ age_days.

سیگنالِ دوم (۲۰۲۶-۰۸-۰۷، فیکسِ خودآگاهیِ کاذب): xlsxِ محلی تنها منبعِ واقعی نیست —
pipeline ِ PocketSmith/ledger_core (پشتِ OCTOPUS_WIRE_ACCT_BEAT) هر بار که می‌چرخد
سایدکارِ اتمیکِ ORGANISM-STATE.accounting را می‌نویسد (wiring.acct_beat؛ فقط شمار،
صفر PII). این سایدکار = «آخرین فعالیتِ واقعیِ pipeline»، مستقل از اینکه مالک اخیراً
xlsx دستی export کرده یا نه. live = تازگیِ xlsx **یا** تازگیِ این سایدکار (هرکدام
تازه‌تر بود). نبودِ سایدکار یا کهنه‌بودنش هرگز رفتارِ قدیمی (فقط xlsx) را نمی‌شکند —
fail-soft در هر دو جهت.

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
# سایدکارِ ضربانِ حسابداری (wiring.acct_beat → opslib.STATE_DIR / "ORGANISM-STATE.accounting").
# فقط mtime دیده می‌شود (همان قاعدهٔ بی‌PIIِ بالا) — صفر خواندنِ محتوا لازم نیست.
ACCT_BEAT_SIDECAR = VAULT / "_ops" / "state" / "ORGANISM-STATE.accounting"
# کادانسِ پیش‌فرضِ acct_beat: هر ۲۴۰ تیک × TICK_SECONDS=300s ≈ ۲۰ ساعت. آستانه چند
# چرخهٔ ازدست‌رفته (خواب/ری‌استارتِ ارگانیسم) را هم تحمل می‌کند، نه فقط یک miss.
ACCT_BEAT_MAX_AGE_DAYS = 3.0


def _acct_beat_signal() -> tuple[float | None, bool]:
    """سنِ سایدکارِ acct_beat + تازگی. fail-soft: نبود/خطای stat → (None, False) —
    هرگز رفتارِ قدیمیِ فقط-xlsx را نمی‌شکند، فقط ممکن است سیگنالِ اضافه ندهد."""
    try:
        a = age_days(ACCT_BEAT_SIDECAR)
    except Exception:  # noqa: BLE001 — این پا هرگز crash نمی‌کند
        return None, False
    return a, (a is not None and a <= ACCT_BEAT_MAX_AGE_DAYS)


def accounting_status() -> dict:
    """snapshotِ فقط‌خواندنیِ وضعیتِ پای Accounting. هرگز crash نمی‌کند.
    ⚠️ صفر مقدار/نام/عددِ مالی خوانده یا echo نمی‌شود — فقط تعداد + mtimeِ workbookها (metadata).
    برنامه ۷: live=True اگر تازه‌ترین workbook تازه باشد (fresh ≤ ACCT_MAX_AGE_DAYS) **یا**
    سایدکارِ ضربانِ حسابداری (PocketSmith/ledger_core، از wiring.acct_beat) ≤ ACCT_BEAT_MAX_AGE_DAYS
    روز پیش نوشته شده باشد — هرکدام تازه‌تر بود. age_days = سنِ تازه‌ترینِ این دو سیگنال
    (گرد به ۰٫۱ روز، یا null). سیگنالِ بی‌PII؛ نبودِ سایدکار fail-soft به رفتارِ قدیمی برمی‌گردد."""
    leg = "accounting"
    adir = ACCT_DIR
    beat_age, beat_live = _acct_beat_signal()
    try:
        exists = adir.exists()
    except OSError:
        exists = False
    if not exists:
        if beat_live:
            return {"leg": leg, "live": True, "signal": "acct-beat",
                    "age_days": round(beat_age, 1),
                    "note": ("پوشهٔ Accounting (xlsx) پیدا نشد، ولی ضربانِ حسابداری "
                             "(PocketSmith/ledger_core، wiring.acct_beat) "
                             f"≤{ACCT_BEAT_MAX_AGE_DAYS:g} روز پیش نوشته شده — pipeline جریان دارد.")}
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
        xlsx_live = fresh(newest, ACCT_MAX_AGE_DAYS)
        live = xlsx_live or beat_live
        ages = [x for x in (a, beat_age) if x is not None]
        out_age = round(min(ages), 1) if ages else None
        signal = f"workbooks={n_wb}"
        note = ("منبعِ مالی موجود — فقط تعداد/mtimeِ workbook دیده شد؛ "
                "صفر مقدار/نام/عدد خوانده شد (خط‌قرمزِ PII، فقط‌خواندنی). "
                + (f"دادهٔ تازه (≤{ACCT_MAX_AGE_DAYS:g} روز) — جریان دارد."
                   if xlsx_live else
                   f"workbookها >{ACCT_MAX_AGE_DAYS:g} روز دست‌نخورده‌اند."))
        if beat_live:
            signal = f"workbooks={n_wb};acct-beat"
            note += (" ضربانِ حسابداری (PocketSmith/ledger_core) هم تازه است — "
                     "pipeline جریان دارد.")
        elif not xlsx_live:
            note += " live=False (داده جریان ندارد)."
        return {"leg": leg, "live": live, "signal": signal, "age_days": out_age, "note": note}
    if beat_live:
        return {"leg": leg, "live": True, "signal": "empty;acct-beat",
                "age_days": round(beat_age, 1),
                "note": ("پوشهٔ Accounting هست ولی بدونِ workbook؛ ضربانِ حسابداری "
                         "(PocketSmith/ledger_core) تازه است — pipeline جریان دارد.")}
    return {"leg": leg, "live": False, "signal": "empty", "age_days": None,
            "note": "پوشهٔ Accounting هست ولی بدونِ workbook — skeleton."}


if __name__ == "__main__":
    print(json.dumps(accounting_status(), ensure_ascii=False, indent=2))
