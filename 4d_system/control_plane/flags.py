"""
control_plane/flags.py — flagهای حاکمیتی، همه default-off به‌جز observe-only.

قاعده‌ی سخت (از دکترینِ مالک): هر چیزی که action واقعی را عوض کند باید
flag-gated و default-off باشد. در v1 اصلاً مسیرِ کدی برای live governance
وجود ندارد؛ این flagها از الان تعریف می‌شوند تا contract روشن باشد.
"""
from __future__ import annotations

import os

# پیش‌فرض‌ها — فقط observe-only روشن است.
FLAG_DEFAULTS: dict[str, bool] = {
    "CONTROL_PLANE_OBSERVE_ONLY": True,    # خواندن/نمایش وضعیت (بی‌خطر)
    "CONTROL_PLANE_SHADOW_POLICY": False,  # v2: ارزیابی policy فقط روی کاغذ
    "CONTROL_PLANE_APPROVALS_LIVE": False, # v3: approval واقعی برای high-risk
    "CONTROL_PLANE_LIVE_GOVERNANCE": False,# v3+: هر نوع блок/enforcement زنده
    "CONTROL_PLANE_KILL_SWITCH_LIVE": False,  # v4: pause/stop از UI
    "CONTROL_PLANE_SELF_HEAL": False,      # v5: watchdog ترمیمِ خود (۲۴/۷)
}

_TRUTHY = ("1", "true", "yes", "on")
_FALSY = ("0", "false", "no", "off")


def flag(name: str) -> bool:
    """مقدارِ یک flag — env override، وگرنه default. flag ناشناس = False."""
    default = FLAG_DEFAULTS.get(name, False)
    raw = os.getenv(name, "").strip().lower()
    if raw in _TRUTHY:
        return True
    if raw in _FALSY:
        return False
    return default


def all_flags() -> dict[str, bool]:
    """وضعیتِ همه‌ی flagهای شناخته‌شده (برای UI و گزارش)."""
    return {name: flag(name) for name in FLAG_DEFAULTS}


def governance_mode() -> str:
    """خلاصه‌ی حالتِ حاکمیت برای نمایش در یک نگاه."""
    f = all_flags()
    if f["CONTROL_PLANE_KILL_SWITCH_LIVE"] or f["CONTROL_PLANE_LIVE_GOVERNANCE"]:
        return "LIVE (v4+)"
    if f["CONTROL_PLANE_APPROVALS_LIVE"]:
        return "approvals-live (v3)"
    if f["CONTROL_PLANE_SHADOW_POLICY"]:
        return "shadow (v2)"
    if f["CONTROL_PLANE_OBSERVE_ONLY"]:
        return "observe-only (v1)"
    return "disabled"
