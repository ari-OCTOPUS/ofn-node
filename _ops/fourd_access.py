#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""fourd_access.py — W1: دسترسیِ read-only مغزِ دوم (4d_system) به دادهٔ OCTOPUS.

فاز ۷ دستورالعمل ۲۰۲۶-۰۸-۱۶ + سندِ DUAL-BRAIN-CONSTITUTION §۴-§۵:
  W1 اتصال data layer (read-only) ← FOURD_DATA_ACCESS=1 (فقط همین مرحله؛
  W2 پروپوزال/W3 ارزیابی/W4 وتو/W5 ارز — هر کدام رأیِ جداگانهٔ مالک می‌خواهد).

چرا اجازه‌نامه (allowlist) و نه انکارنامه (denylist)
────────────────────────────────────────────────────
این در، ورودیِ یک سیستمِ خودتغییرِ بیرونی به state زندهٔ ارگانیسم است. denylist
یعنی هر فایلِ جدیدِ آینده به‌طور پیش‌فرض خواندنی است. allowlist یعنی هر چیز
جدید تا رأیِ صریح نیامده **ناخواندنی** است (fail-closed). اجازه‌نامه فقط فایل‌های
state غیرمحرمانهٔ شمرده‌شده است — هرگز flags/cmd (حاملِ secret)، هرگز .env،
هرگز دادهٔ دستهٔ ویژه. الگوی نامِ راز از flag_drift.is_secret_name (منبعِ یگانه).

تضمینِ ساختاریِ فقط-خواندن: این ماژول هیچ تابعِ نوشتن ندارد و تست با AST همین
را قفل می‌کند (open فقط در حالتِ خواندن؛ write_text/os.remove/shutil ممنوع).
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
for _p in (str(_HERE), str(_HERE / "budget")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import opslib  # noqa: E402

FLAG = "FOURD_DATA_ACCESS"
SCHEMA = "fourd-access.v1"
_TRUTHY = ("1", "true", "yes", "on")

# اجازه‌نامهٔ نهایی — فقط این فایل‌های state غیرمحرمانه از پشتِ درِ W1 خوانده
# می‌شوند. افزودنِ ردیف = رأیِ مالک + تست.
ALLOWED_VIEWS = {
    "organism_state": "ORGANISM-STATE.json",
    "cortex_state": "cortex/cortex-state.json",
    "cardiac_budget": "cardiac-budget.json",
    "heartstate": "pulse/heartstate-latest.json",
    "arbiter": "pulse/arbiter-latest.json",
    "life_currency": "pulse/life-currency-latest.json",
}


def enabled() -> bool:
    if FLAG in os.environ:
        return str(os.environ[FLAG]).strip().lower() in _TRUTHY
    try:
        import owner_verdicts as _ov   # noqa: WPS433
        return str(_ov.get(FLAG) or "0").strip().lower() in _TRUTHY
    except Exception:  # noqa: BLE001
        return False


def read_view(view: str) -> dict:
    """یک نمای مجاز را بخوان. نامِ ناشناخته = خطای not-in-allowlist (نه fallback
    به مسیر خام — درِ بسته). فقط با فلگ؛ بدونِ فلگ هیچ فایلی باز نمی‌شود."""
    if not enabled():
        return {"enabled": False, "reason": "flag-off", "view": str(view)[:48]}
    rel = ALLOWED_VIEWS.get(str(view or "").strip())
    if rel is None:
        return {"enabled": True, "error": "not-in-allowlist",
                "view": str(view)[:48]}
    # دفاع دوم: الگوی نامِ راز روی مؤلفه‌های مسیر (هرگز نباید رخ دهد — اجازه‌نامه
    # را دستِ انسان نوشته، ولی آینه‌ی قاعده در کد می‌ماند)
    try:
        import flag_drift as _fd   # noqa: WPS433
        if any(_fd.is_secret_name(part) for part in Path(rel).parts):
            return {"enabled": True, "error": "secret-pattern-denied",
                    "view": str(view)[:48]}
    except Exception:   # noqa: BLE001 — نبودِ ماژولِ گارد نباید در را باز بگذارد
        return {"enabled": True, "error": "guard-unavailable-denied",
                "view": str(view)[:48]}
    try:
        p = Path(opslib.STATE_DIR) / rel
        data = json.loads(p.read_text("utf-8"))
        return {"enabled": True, "view": str(view), "data": data}
    except (OSError, ValueError):
        return {"enabled": True, "view": str(view), "error": "unreadable",
                "note": "فایل غایب/خراب — بدونِ دروغ"}

def snapshot() -> dict:
    """همهٔ نمای‌های مجاز در یک dict — غذأ دادهٔ مغزِ 4d (فقط‌خواندن).
    بدونِ فلگ: فقط اعلامِ خاموشی، صفر I/O."""
    out = {"schema": SCHEMA, "ts": opslib.now_iso(),
           "enabled": enabled(), "read_only": True, "w1_only": True,
           "views": {}}
    if not enabled():
        out["reason"] = "flag-off (W1 — رأیِ مالک لازم)"
        return out
    for name in ALLOWED_VIEWS:
        r = read_view(name)
        out["views"][name] = (r.get("data") if "data" in r
                              else {"error": r.get("error", "unknown")})
    return out


if __name__ == "__main__":   # pragma: no cover
    print(json.dumps({k: (len(v) if k == "views" else v)
                      for k, v in snapshot().items()},
                     ensure_ascii=False, indent=1))
