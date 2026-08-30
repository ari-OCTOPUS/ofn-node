#!/usr/bin/env python3
"""actions.py — رجیستریِ متمرکزِ callbackهای عملگرا (فاز F — skeleton).

نقش: یک منبعِ حقیقتِ خالص برای نگاشتِ «نامِ اکشنِ منطقی» → «callback_data + متاداده».
تا render و intent و center به‌جایِ hardcode پخش‌شدن، از همین جدول بخوانند.

قراردادِ خروجی هر مدخل:

    {
      "callback":   "mn:st"  یا "lg:{leg}:p"  (قالب با {leg} و {id} جایگذاری می‌شود),
      "risk":       "read|low|medium|high|emergency",
      "direct":     True/False,           # آیا read-only و امنِ مستقیم؟
      "double_confirm": True/False,       # آیا نیاز به pw/pwc دارد؟
      "description": "...",               # human-readable (فارسی)
      "verbs":      ("mn","lg","pw",...), # برای dispatch در center
    }

چرا skeleton: این فاز در دستور «اگر زمان کم بود، حداقل skeleton و تست کوچک» خواسته
شده. پیاده‌سازیِ کامل یعنی render_menu و intent router از همین ACTIONS بخوانند —
که یک refactor بزرگ است و ریسکِ شکستنِ تست‌های سبز را دارد. فعلاً جدولِ معتبر +
lookup helper + تست داریم؛ مصرف در مراحلِ بعدی.

$0 · stdlib-only · import-time خالص. مصرف‌کنندهٔ آینده: render.py / center.py.
"""
from __future__ import annotations

from typing import Any

# ─── رجیستریِ اکشن‌ها ─────────────────────────────────────────────────────────────
# کلیدها = «نامِ منطقیِ dotدار» که در گزارش‌ها و intentها پایدارند.
# callback می‌تواند شاملِ {leg} یا {id} برای جایگذاریِ پارامتریک باشد.
ACTIONS: dict[str, dict[str, Any]] = {
    # ── خواندنی (read) — مستقیم، بدونِ تأیید
    "status.refresh":     {"callback": "mn:st",    "risk": "read",      "direct": True,
                           "double_confirm": False, "verbs": ("mn",),
                           "description": "تازه‌سازیِ وضعیت"},
    "menu.show":          {"callback": "mn:menu",  "risk": "read",      "direct": True,
                           "double_confirm": False, "verbs": ("mn",),
                           "description": "نمایشِ منوی اصلی"},
    "legs.show":          {"callback": "mn:lg",    "risk": "read",      "direct": True,
                           "double_confirm": False, "verbs": ("mn",),
                           "description": "نمایشِ پای ارگانیسم"},
    "budget.show":        {"callback": "mn:bg",    "risk": "read",      "direct": True,
                           "double_confirm": False, "verbs": ("mn",),
                           "description": "نمایشِ پیشنهادِ بودجه (propose-only)"},
    "revenue.show":       {"callback": "mn:rv",    "risk": "read",      "direct": True,
                           "double_confirm": False, "verbs": ("mn",),
                           "description": "نمایشِ درآمدِ aggregate"},
    "map.show":           {"callback": "mn:map",   "risk": "read",      "direct": True,
                           "double_confirm": False, "verbs": ("mn",),
                           "description": "صفحهٔ نقشه‌برداری metadata"},
    "approvals.show":     {"callback": "mn:ap",    "risk": "read",      "direct": True,
                           "double_confirm": False, "verbs": ("mn",),
                           "description": "صفحهٔ صف تأیید"},
    "missions.show":      {"callback": "mn:ms",    "risk": "read",      "direct": True,
                           "double_confirm": False, "verbs": ("mn",),
                           "description": "صفحهٔ مأموریت‌ها (Mission Genome)"},

    # ─ـ کم‌ریسک (low) — مکث/ادامهٔ پا (برگشت‌پذیر، ولی state عوض می‌شود)
    "leg.pause":          {"callback": "lg:{leg}:p", "risk": "low",     "direct": False,
                           "double_confirm": False, "verbs": ("lg",),
                           "description": "مکثِ یک پای مشخص"},
    "leg.resume":         {"callback": "lg:{leg}:r", "risk": "low",     "direct": False,
                           "double_confirm": False, "verbs": ("lg",),
                           "description": "ادامهٔ یک پای مکث‌شده"},

    # ─ـ خواندنی با side-effect محدود (read) — scan فقط metadata
    "map.start":          {"callback": "map:start", "risk": "read",     "direct": False,
                           "double_confirm": False, "verbs": ("map",),
                           "description": "شروعِ اسکنِ metadata (فقط خواندنی)"},

    # ── صف تأیید (read برای نمایش، ولی تغییر state)
    "approval.approve":   {"callback": "ap:ok:{id}",  "risk": "low",    "direct": False,
                           "double_confirm": False, "verbs": ("ap",),
                           "description": "تأییدِ یک job از صف"},
    "approval.reject":    {"callback": "ap:no:{id}",  "risk": "low",    "direct": False,
                           "double_confirm": False, "verbs": ("ap",),
                           "description": "ردِ یک job از صف"},
    "approval.detail":    {"callback": "ap:detail:{id}", "risk": "read", "direct": False,
                           "double_confirm": False, "verbs": ("ap",),
                           "description": "جزئیاتِ یک job (content-free)"},

    # ── Mission Genome — state-only، اجرای واقعیِ patch جداست
    "mission.open":       {"callback": "ms:open:{id}", "risk": "read",   "direct": False,
                           "double_confirm": False, "verbs": ("ms",),
                           "description": "بازکردن کارت مأموریت"},
    "mission.test":       {"callback": "ms:test:{id}", "risk": "low",    "direct": False,
                           "double_confirm": False, "verbs": ("ms",),
                           "description": "ثبت درخواست تست/fitness برای مأموریت"},
    "mission.review":     {"callback": "ms:review:{id}", "risk": "low",  "direct": False,
                           "double_confirm": False, "verbs": ("ms",),
                           "description": "ثبت درخواست Doctor/Epistemics review"},
    "mission.approve":    {"callback": "ms:approve:{id}", "risk": "low", "direct": False,
                           "double_confirm": False, "verbs": ("ms",),
                           "description": "تأیید state مأموریت؛ apply واقعی نیست"},
    "mission.reject":     {"callback": "ms:reject:{id}", "risk": "low",  "direct": False,
                           "double_confirm": False, "verbs": ("ms",),
                           "description": "رد state مأموریت"},

    # ─ـ پرخطر (high) — پشتِ power-gate + دوکلیک
    "budget.apply":       {"callback": "pw:ba",     "risk": "high",     "direct": False,
                           "double_confirm": True,  "verbs": ("pw", "pwc"),
                           "description": "اعمالِ سقف‌های epoch به budgets.yaml"},
    "system.restart":     {"callback": "pw:rs",     "risk": "high",     "direct": False,
                           "double_confirm": True,  "verbs": ("pw", "pwc"),
                           "description": "ری‌استارتِ روتینِ ارگانیسم"},

    # ── اضطراری (emergency) — آزاد ولی دوکلیک (قراردادِ power.py)
    "system.panic":       {"callback": "pw:pn",     "risk": "emergency","direct": False,
                           "double_confirm": True,  "verbs": ("pw", "pwc"),
                           "description": "پنیک — HALT-ALL همه‌چیز"},
    "system.stop":        {"callback": "pw:st",     "risk": "emergency","direct": False,
                           "double_confirm": True,  "verbs": ("pw", "pwc"),
                           "description": "توقفِ کاملِ ارگانیسم"},
    "system.resume":      {"callback": "pw:re",     "risk": "emergency","direct": False,
                           "double_confirm": True,  "verbs": ("pw", "pwc"),
                           "description": "برداشتنِ پنیک (HALT-ALL)"},
}


def get(name: str) -> "dict | None":
    """یک مدخل را برگردان. fail-soft → None اگر نبود."""
    return ACTIONS.get(str(name or ""))


def callback_for(name: str, **params) -> "str | None":
    """callback_data ساخته‌شده برای یک اکشن با جایگذاریِ پارامترها.

    params می‌تواند شاملِ leg و id باشد. پارامترهای نامعتبر → رها می‌شوند
    (format-safe با безопас‌سازی). fail-soft → None."""
    entry = get(name)
    if not entry:
        return None
    tmpl = str(entry.get("callback") or "")
    if not tmpl:
        return None
    try:
        # فقط پارامترهای موردِ قالب را جایگذار کن؛ بقیه نادیده.
        return tmpl.format(**{k: str(v) for k, v in params.items() if f"{{{k}}}" in tmpl})
    except (KeyError, IndexError, ValueError):
        return tmpl    # قالب نشد → همان خام (مصرف‌کننده تصمیم می‌گیرد)


def actions_by_risk(risk: str) -> list[str]:
    """همهٔ نام‌های اکشن با یک ریسکِ مشخص. برای گزارش‌دهی و audit."""
    risk = str(risk or "")
    return [name for name, e in ACTIONS.items() if e.get("risk") == risk]


def is_double_confirm(name: str) -> bool:
    """آیا این اکشن نیاز به pw/pwc دارد؟ برای gating در center."""
    e = get(name)
    return bool(e and e.get("double_confirm"))


def is_safe_direct(name: str) -> bool:
    """آیا این اکشن read-only و امنِ مستقیم است؟ برای intent router."""
    e = get(name)
    return bool(e and e.get("direct") and e.get("risk") == "read")


if __name__ == "__main__":
    import json
    print(f"{len(ACTIONS)} actions registered.")
    for risk in ("read", "low", "high", "emergency"):
        print(f"  {risk}: {len(actions_by_risk(risk))}")
    print("\nSamples:")
    print("  leg.pause with leg=lead →", callback_for("leg.pause", leg="lead"))
    print("  approval.approve with id=job-1 →", callback_for("approval.approve", id="job-1"))
    print("  map.start →", callback_for("map.start"))
    print("  is_double_confirm('budget.apply'):", is_double_confirm("budget.apply"))
