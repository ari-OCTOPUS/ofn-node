#!/usr/bin/env python3
"""money.py — موتورِ پولِ دقیق (integer cents، نه float) — 2026-07-16.

روشِ ۱ از تحقیقِ ۲۰۲۷ (استاندارد، دهه‌ها در payments): پول هرگز IEEE-754 float نیست
(0.1+0.2!=0.3). این‌جا هر مبلغ = عددِ صحیحِ سنت. parse با Decimal (امن)، ذخیره/جمع/تقسیم
با int. تقسیمِ splitِ largest-remainder → سهم‌ها *دقیقاً* جمع می‌شوند به کل (بدونِ نشتِ سنت).

مصرف: to_cents("۱٬۲۳۴.۵۶") → 123456 · fmt(123456) → "1234.56" · split_cents(101, {a:50,b:50}) → {a:51,b:50}
$0 · stdlib (Decimal) · بدونِ وابستگی.
"""
from __future__ import annotations

import re
from decimal import Decimal, ROUND_HALF_UP, InvalidOperation

_CLEAN = re.compile(r"[^\d.\-]")


def to_cents(x) -> int:
    """هر ورودی (رشته/عدد) → عددِ صحیحِ سنت. پرانتز = منفی (قرارداد حسابداری). خطا → 0.
    $, کاما، فاصله، و ارقامِ فارسی پاک می‌شوند."""
    if isinstance(x, bool):
        return 0                                 # bool پول نیست (audit 2026-07-16 #15)
    if isinstance(x, int):
        return x * 100 if abs(x) < 10**7 else x  # هشدار: int خام مبهم است؛ ترجیح رشته
    if x is None:
        return 0
    s = str(x).strip()
    if not s:
        return 0
    neg = False
    if s.startswith("(") and s.endswith(")"):     # (123.45) = -123.45
        neg = True
        s = s[1:-1]
    # ارقامِ فارسی/عربی → لاتین
    s = s.translate(str.maketrans("۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩", "01234567890123456789"))
    s = _CLEAN.sub("", s)
    if s in ("", "-", ".", "-."):
        return 0
    try:
        d = Decimal(s)
    except InvalidOperation:
        return 0
    cents = int((d * 100).quantize(Decimal("1"), rounding=ROUND_HALF_UP))
    return -cents if neg else cents


def fmt(cents: int, sym: str = "") -> str:
    """سنت → رشتهٔ دو-رقمی (برای نمایش فقط در لبِ خروجی). 123456 → '1234.56'."""
    try:
        c = int(cents)
    except (TypeError, ValueError):
        c = 0
    sign = "-" if c < 0 else ""
    c = abs(c)
    return f"{sign}{sym}{c // 100}.{c % 100:02d}"


def split_cents(total: int, weights: dict) -> dict:
    """تقسیمِ largest-remainder: total سنت را طبقِ weights تقسیم کن طوری که مجموعِ سهم‌ها
    *دقیقاً* = total (نشتِ سنت غیرممکن). weights مثل {'armin':60,'abbas':40} یا هر نسبت.
    مجموعِ سهم‌های خروجی == total تضمین‌شده (assertion-safe)."""
    total = int(total)
    keys = [k for k, v in weights.items() if _num(v) > 0]
    wsum = sum(_num(weights[k]) for k in keys)
    if not keys or wsum <= 0:
        return {}
    # سهمِ کف (floor) + توزیعِ باقی‌مانده به بزرگ‌ترین کسرها
    raw = {k: (total * _num(weights[k])) / wsum for k in keys}
    floors = {k: int(raw[k]) if total >= 0 else -int(-raw[k]) for k in keys}
    allocated = sum(floors.values())
    remainder = total - allocated                  # چند سنت مانده
    # مرتب بر اساسِ بزرگیِ کسرِ اعشاری (نزولی برای remainder مثبت)
    fracs = sorted(keys, key=lambda k: (raw[k] - floors[k]),
                   reverse=(remainder >= 0))
    step = 1 if remainder >= 0 else -1
    out = dict(floors)
    for i in range(abs(remainder)):
        out[fracs[i % len(fracs)]] += step
    assert sum(out.values()) == total, f"split leak: {sum(out.values())} != {total}"
    return out


def gst_component(gross_cents: int) -> int:
    """جزءِ GSTِ یک مبلغِ ناخالصِ شاملِ GST (استرالیا): **دقیقاً ۱/۱۱ با گردِ half-up**.
    صرفاً حساب است، نه تصمیمِ مالیاتی — این‌که قلمی اصلاً taxable هست یا نه، تصمیمِ
    مالک/BAS agentِ ثبت‌شده است (RD-002). ورودیِ خراب/منفی‌ساز → 0 روی خراب، قدرمطلق‌محور.
    مثال: 11000 (110.00$) → 1000 · 10000 → 909 · 1050 → 95."""
    try:
        g = int(gross_cents)
    except (TypeError, ValueError):
        return 0
    sign = -1 if g < 0 else 1
    gst = int((Decimal(abs(g)) / 11).quantize(Decimal("1"), rounding=ROUND_HALF_UP))
    return sign * gst


def net_of_gst(gross_cents: int) -> int:
    """خالصِ بدونِ GST: gross − gst_component. تضمین: net + gst == gross (بدونِ نشتِ سنت)."""
    try:
        g = int(gross_cents)
    except (TypeError, ValueError):
        return 0
    return g - gst_component(g)


def _num(v) -> float:
    try:
        return float(v)
    except (TypeError, ValueError):
        return 0.0


if __name__ == "__main__":
    # دودِ سریع
    assert to_cents("1,234.56") == 123456
    assert to_cents("$250.00") == 25000
    assert to_cents("(420.00)") == -42000
    assert to_cents("۲۵۰") == 25000
    assert fmt(123456) == "1234.56"
    assert fmt(-42000) == "-420.00"
    # splitِ فرد: ۱۰۱ سنت، ۵۰/۵۰ → 51+50=101 (بدونِ نشت)
    s = split_cents(101, {"armin": 50, "abbas": 50})
    assert sum(s.values()) == 101 and s == {"armin": 51, "abbas": 50}, s
    # ۱۰۰۰۰ سنت ۶۰/۴۰
    s2 = split_cents(10000, {"armin": 60, "abbas": 40})
    assert sum(s2.values()) == 10000 and s2["armin"] == 6000, s2
    # GST ۱/۱۱ قطعی (حساب، نه تصمیمِ مالیاتی): net+gst==gross همیشه
    assert gst_component(11000) == 1000 and net_of_gst(11000) == 10000
    assert gst_component(10000) == 909 and net_of_gst(10000) + gst_component(10000) == 10000
    assert gst_component(1050) == 95
    assert gst_component(-11000) == -1000                     # علامت حفظ می‌شود
    assert gst_component("bad") == 0
    assert to_cents(True) == 0 and to_cents(False) == 0       # bool پول نیست (audit #15)
    for g in (1, 3, 7, 99, 12345, 999999):                     # ناوردا: بدونِ نشتِ سنت
        assert net_of_gst(g) + gst_component(g) == g, g
    print("PASS money smoke")
