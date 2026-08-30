"""test_lead_quote_area_key — متراژِ استخراج‌شده به quote می‌رسد (قاتلِ #۱۰).

۲۰۲۶-۰۸-۰۱ — قاتلِ زنجیره‌ایِ شمارهٔ ۱۰: lead_email_intake کلیدِ `floor_area_m2`
می‌نویسد ولی lead_quote.lead_to_intake کلیدِ `size_m2` را می‌خواند. عدم‌تطابق
نامِ کلید ⇒ همیشه ۰ ⇒ قیمت A$0.00 ⇒ گاردِ قیمتِ خودِ سیستم ایمیل را بی‌صدا
رد می‌کرد. لیدِ واقعی هرگز قیمت نمی‌گرفت.

این تست کلیدِ canonical (floor_area_m2) و range و legacy (size_m2) را نگه
می‌دارد. جهش: خواندنِ floor_area_m2 را بشکن → تستِ اصلی قرمز می‌شود.
"""
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE))
import harness  # noqa: E402
harness.setup("lead-quote-area-key")

_LEGS = harness.SELF_OPS / "legs"
if str(_LEGS) not in sys.path:
    sys.path.insert(0, str(_LEGS))

from lead_quote import lead_to_intake  # noqa: E402


def t_canonical_floor_area_m2_reaches_quote():
    """کلیدِ canonical اکنون floor_area_m2 است — باید به size_m2 برسد."""
    qi = lead_to_intake({"description": "3br repaint", "floor_area_m2": 120})
    assert qi.size_m2 == 120.0, f"floor_area_m2=120 گم شد: size_m2={qi.size_m2}"


def t_range_averages_to_midpoint():
    """بازهٔ کاری → میانگین."""
    qi = lead_to_intake({"description": "repaint", "floor_area_range_m2": [100, 140]})
    assert qi.size_m2 == 120.0, f"range midpoint غلط: {qi.size_m2}"


def t_legacy_size_m2_still_supported():
    """دادهٔ legacy با size_m2 هنوز کار می‌کند (backward-compatible)."""
    qi = lead_to_intake({"description": "repaint", "size_m2": 90})
    assert qi.size_m2 == 90.0, f"legacy size_m2 گم شد: {qi.size_m2}"


def t_no_area_is_zero_not_crash():
    """نبودِ کلید = صفر صادقانه، نه crash."""
    qi = lead_to_intake({"description": "repaint"})
    assert qi.size_m2 == 0.0, f"کلیدِ غایب باید ۰ باشد: {qi.size_m2}"


def t_canonical_takes_precedence_over_legacy():
    """اگر هر دو هست، canonical برنده."""
    qi = lead_to_intake({"description": "x", "floor_area_m2": 200, "size_m2": 50})
    assert qi.size_m2 == 200.0, f"canonical نباید توسط legacy لِه شود: {qi.size_m2}"


if __name__ == "__main__":
    harness.run([
        ("canonical_floor_area_m2_reaches_quote", t_canonical_floor_area_m2_reaches_quote),
        ("range_averages_to_midpoint", t_range_averages_to_midpoint),
        ("legacy_size_m2_still_supported", t_legacy_size_m2_still_supported),
        ("no_area_is_zero_not_crash", t_no_area_is_zero_not_crash),
        ("canonical_takes_precedence_over_legacy", t_canonical_takes_precedence_over_legacy),
    ])
