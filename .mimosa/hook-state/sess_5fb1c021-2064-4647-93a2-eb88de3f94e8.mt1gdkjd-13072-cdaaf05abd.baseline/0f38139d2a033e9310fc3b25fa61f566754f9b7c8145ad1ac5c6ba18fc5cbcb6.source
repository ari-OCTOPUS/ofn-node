"""governance.py — گیت‌های حاکمیتیِ Mining (fail-closed).

ارثی از D-10 (اجرای مالی HARD_STOP) · D-11 (صفر wallet) · D-20 (صفر SSH) + قید برق.
هیچ side-effect؛ فقط تصمیمِ «مجاز/غیرمجاز» و وضعیتِ گیت.
"""
from __future__ import annotations

# اقدام‌هایی که هیچ ایجنتی مجاز نیست (fail-closed) — D-10/D-11/D-20 و spawn/apply
FORBIDDEN_ACTIONS = frozenset({
    "ssh", "deploy", "wallet", "wallet_access", "miner_control",
    "trade", "buy", "sell", "withdraw", "spawn", "code.apply",
})

ELECTRICITY_CEILING_KWH = 0.05  # قید ساختاری: بالاتر و نه‌خورشیدی → HALT


class ActionForbidden(PermissionError):
    """اقدامِ ممنوع طبقِ حاکمیت (fail-closed)."""


def assert_action_allowed(action: str) -> None:
    """اگر اقدام ممنوع باشد → ActionForbidden. (propose-only؛ اجرا فقط با verdictِ مالک.)"""
    a = (action or "").strip().lower()
    if a in FORBIDDEN_ACTIONS:
        raise ActionForbidden(f"action '{a}' ممنوع است — فقط verdictِ مالک.")


def is_action_allowed(action: str) -> bool:
    try:
        assert_action_allowed(action)
        return True
    except ActionForbidden:
        return False


def electricity_gate(price_kwh, solar: bool):
    """('OK'|'HALT', reason). HALT اگر خورشیدی نیست و (قیمت نامعلوم یا ≥ سقف)."""
    if solar:
        return "OK", "خورشیدی"
    if price_kwh is None:
        return "HALT", "هزینهٔ برق نامعلوم (fail-closed)"
    try:
        if float(price_kwh) >= ELECTRICITY_CEILING_KWH:
            return "HALT", f"برق {price_kwh}/kWh ≥ سقفِ {ELECTRICITY_CEILING_KWH}"
    except (TypeError, ValueError):
        return "HALT", "هزینهٔ برقِ نامعتبر (fail-closed)"
    return "OK", f"برق {price_kwh}/kWh < سقف"


def wallet_access_allowed() -> bool:
    """D-11: هیچ ایجنت هرگز به wallet دسترسی ندارد."""
    return False
