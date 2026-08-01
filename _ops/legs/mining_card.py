"""mining_card.py — کارتِ عددیِ ماینینگ + خلاصهٔ دایجست.

D-013: عددی از همین حالا — نه «کارتِ راه‌اندازی».
هر عددی که اندازه‌گیری نشده، صریحاً «اندازه‌گیری‌نشده» است، نه ۰.
ناوگان = ۱۶۲ (ثابتِ مالک). پایهٔ هش = ۱۶ نود.

این ماژول read-only است: هیچ فایلی نمی‌نویسد، هیچ شبکه‌ای نمی‌زند.
"""
from __future__ import annotations

import html

# ── ثابت‌های ماژول ───────────────────────────────────────────────────────────
FLEET_TOTAL: int = 162          # ۱۶ Orange Pi + ۱۴۰ ESP32 + ۲ FPGA — تأییدِ مالک
MINERS_BASE: int = 16           # پایهٔ هش (Orange Pi 5 Pro)
UNMEASURED: str = "\u0627\u0646\u062f\u0627\u0632\u0647\u200c\u06af\u06cc\u0631\u06cc\u200c\u0646\u0634\u062f\u0647"  # اندازه‌گیری‌نشده

# جدولِ ارقامِ فارسی
_FA_DIGITS = list("۰۱۲۳۴۵۶۷۸۹")


# ── کمکی ──────────────────────────────────────────────────────────────────────
def _fa(n: int) -> str:
    """عدد صحیح را به ارقامِ فارسی برمی‌گرداند: 162 → «۱۶۲»."""
    s = str(n)
    return "".join(_FA_DIGITS[int(ch)] for ch in s)


# ── کارت ──────────────────────────────────────────────────────────────────────
def card_text(*, live: bool = False, signal: str = "skeleton",
              fleet_total: int = FLEET_TOTAL,
              miners_base: int = MINERS_BASE) -> str:
    """متنِ کارتِ عددیِ ماینینگ — HTML امن برای تلگرام، حداکثر ۸ خط."""
    # خطِ سر: آیکون + وضعیت
    icon = html.escape("⛏ Mining")
    if live:
        status = html.escape("🟢 live")
    else:
        status = html.escape("⚪ skeleton")

    lines: list[str] = []
    lines.append(f"<b>{icon}</b>  {status}")

    # خطِ ناوگان
    fleet_str = html.escape(f"ناوگان: {_fa(fleet_total)}  ·  پایهٔ هش: {_fa(miners_base)} نود")
    lines.append(fleet_str)

    # وقتی زنده نیست: همه‌چیز اندازه‌گیری‌نشده
    if not live:
        lines.append(html.escape(f"نرخ هش: {UNMEASURED}"))
        lines.append(html.escape(f"آپتایم: {UNMEASURED}"))
        lines.append(html.escape(f"دما: {UNMEASURED}"))
        lines.append(html.escape(f"سود: {UNMEASURED}"))
    else:
        # آینده: مقادیر واقعی جایگزین می‌شوند
        lines.append(html.escape(f"نرخ هش: {UNMEASURED}"))
        lines.append(html.escape(f"آپتایم: {UNMEASURED}"))
        lines.append(html.escape(f"دما: {UNMEASURED}"))
        lines.append(html.escape(f"سود: {UNMEASURED}"))

    return "\n".join(lines)


# ── دایجست ────────────────────────────────────────────────────────────────────
def digest_detail(*, live: bool = False, signal: str = "skeleton") -> str:
    """یک خطِ کوتاه (≤۱۰۰ نویسه) برای render.py."""
    fleet = _fa(FLEET_TOTAL)
    if live:
        return html.escape(f"{fleet} نود · زنده · {UNMEASURED}")
    else:
        return html.escape(f"{fleet} نود · همه خاموش · {UNMEASURED}")
