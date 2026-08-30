"""
hrv.py — محاسبه‌ی RMSSD از داده‌ی خامِ فواصلِ ضربان (RR / IBI).

RMSSD = ریشه‌ی میانگینِ مربعاتِ اختلافِ فواصلِ پیاپیِ ضربان (بر حسب ms).
ورودی: لیستِ فواصلِ RR بر حسب میلی‌ثانیه (همان چیزی که اکثر اپ‌ها/دستگاه‌های
HRV با نام IBI یا RR صادر می‌کنند). خروجی هم بر حسب ms است.
"""

from __future__ import annotations

import math

# تبدیل ارقام فارسی/عربی به انگلیسی
_DIGITS = str.maketrans("۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩", "01234567890123456789")

# بازه‌ی منطقیِ یک فاصله‌ی RR انسانی (ms) — بیرونِ این بازه artifact است
RR_MIN_MS = 300.0   # ~۲۰۰ ضربه در دقیقه
RR_MAX_MS = 2000.0  # ~۳۰ ضربه در دقیقه


def parse_numbers(text: str) -> list[float]:
    """
    یک رشته‌ی آزاد را به لیست عدد تبدیل می‌کند.
    جداکننده: فاصله، کاما (انگلیسی/فارسی)، خط جدید، تب.
    اعداد فارسی و واحدِ ms پشتیبانی می‌شوند.
    """
    t = text.translate(_DIGITS)
    for ch in (",", "،", "؛", ";", "\n", "\t", "\r"):
        t = t.replace(ch, " ")
    t = t.replace("٫", ".")
    out: list[float] = []
    for tok in t.split():
        tok = tok.replace("ms", "").strip()
        if not tok:
            continue
        try:
            out.append(float(tok))
        except ValueError:
            continue
    return out


def compute_rmssd(rr_ms: list[float]):
    """
    RMSSD را از لیستِ فواصلِ RR (ms) حساب می‌کند.

    خروجی: dict با کلیدهای
      ok        : bool
      rmssd     : float | None  (ms)
      n_used    : int           (تعداد RRِ معتبرِ استفاده‌شده)
      n_dropped : int           (تعداد RRِ حذف‌شده به‌عنوان artifact)
      reason    : str | None    (اگر ok=False، علتش)
    قاعده‌ها:
      - فواصلِ بیرونِ بازه‌ی منطقی حذف می‌شوند (artifact rejection).
      - برای محاسبه حداقل ۲ فاصله‌ی معتبر لازم است (یک اختلاف).
    """
    clean = [x for x in rr_ms if RR_MIN_MS <= x <= RR_MAX_MS]
    dropped = len(rr_ms) - len(clean)

    if len(clean) < 2:
        return {
            "ok": False, "rmssd": None, "n_used": len(clean),
            "n_dropped": dropped,
            "reason": "حداقل ۲ فاصله‌ی RR معتبر لازم است.",
        }

    diffs = [clean[i + 1] - clean[i] for i in range(len(clean) - 1)]
    rmssd = math.sqrt(sum(d * d for d in diffs) / len(diffs))
    return {
        "ok": True, "rmssd": rmssd, "n_used": len(clean),
        "n_dropped": dropped, "reason": None,
    }
