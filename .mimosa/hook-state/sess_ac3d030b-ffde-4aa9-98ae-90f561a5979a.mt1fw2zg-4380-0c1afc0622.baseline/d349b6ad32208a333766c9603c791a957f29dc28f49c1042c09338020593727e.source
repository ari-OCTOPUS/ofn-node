"""death_watch.py — معیارِ مرگِ D2: بقا، نه payback.

رهاکردنِ یک کوین فقط با نشانه‌های مرگِ بقا مجاز است؛ payback/نقدشوندگی هرگز معیارِ قطع نیست.
"""
from __future__ import annotations

DEV_DEAD_WEEKS = 8


def should_abandon(coin: dict) -> tuple[bool, str]:
    """(bool, reason) طبقِ D2. payback عمداً نادیده گرفته می‌شود."""
    if not isinstance(coin, dict):
        return False, "ورودیِ نامعتبر — تصمیم نگرفت (fail-safe)"
    if coin.get("dev_dead_weeks", 0) >= DEV_DEAD_WEEKS:
        return True, f"dev خاموش ≥ {DEV_DEAD_WEEKS} هفته"
    if coin.get("chain_stalled"):
        return True, "زنجیره متوقف"
    if coin.get("community_dead"):
        return True, "جامعه خالی"
    return False, "زنده (طبق D2)"
