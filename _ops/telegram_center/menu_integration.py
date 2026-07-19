#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
menu_integration — the ONE delegate center.py calls for the 6-option owner panel.

Purpose: hold ALL wiring logic here (tested, stdlib) so center.py's change is tiny and additive:
a new `/panel` command + a new `m:` callback verb, both flag-gated by OCTOPUS_WIRE_MENU_V2.
Returns center.py's native shape: (text:str, keyboard) where keyboard = list of rows of
{text, callback_data}. Everything read-only; the panel never executes risky actions itself —
② مأموریت and ⑥ توقف only guide the owner to the existing gated paths.

Consumes: owner_menu (nav), owner_views (①③④ data), owner_debug (⑤ scan). All stdlib.
"""
from __future__ import annotations

import os
import sys
from typing import Any, List, Tuple

_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

import owner_menu as om
import owner_views as ov
import owner_debug as od

FLAG = "OCTOPUS_WIRE_MENU_V2"

# legs the owner can actually command (matches power.PAUSABLE_LEGS). center.py already routes
# lg:<key>:p / lg:<key>:r → power.pause_leg/resume_leg, so these buttons are REAL control.
_PAUSABLE = ("lead", "ziman", "mining", "crypto", "accounting")

Keyboard = List[List[dict]]


def enabled() -> bool:
    return os.environ.get(FLAG, "0") == "1"


def _back_row() -> List[dict]:
    return [{"text": "🐙 منو", "callback_data": "m:home"}]


def render_menu() -> Tuple[str, Keyboard]:
    """The ⑥-option home panel."""
    text = "🐙 اختاپوس — پنل\nیکی را انتخاب کن:"
    return text, om.build_main_menu(cols=2)


def dispatch(data: str) -> Tuple[str, Keyboard]:
    """Route an m:* callback to its view. Never raises; unknown/home -> home panel."""
    if data == "m:home":
        return render_menu()
    key = om.route(data)  # m:status -> "status", etc.
    try:
        if key == "status":
            return ov.render_dashboard(ov.dashboard()), [_back_row()]
        if key == "mytasks":
            return ov.render_backlog(ov.pending_decisions(), ov.proposals()), [_back_row()]
        if key == "legs":
            rows = ov.legs_status()
            kb: Keyboard = []
            for r in rows:
                lk = r.get("key")
                if lk in _PAUSABLE:   # real control: center routes lg:* → power.pause_leg/resume_leg
                    kb.append([{"text": f"⏸ {r['label']}", "callback_data": f"lg:{lk}:p"},
                               {"text": f"▶️ {r['label']}", "callback_data": f"lg:{lk}:r"}])
            # کنترلِ کلِّ اختاپوس: صفحهٔ فلگ‌ها (master switchها — HARVEST/دکتر/…) که center از قبل دارد
            kb.append([{"text": "🎚️ کنترلِ فلگ‌ها (کلِّ اختاپوس)", "callback_data": "mn:fl"}])
            kb.append([{"text": "🧭 صفِ تصمیم‌ها", "callback_data": "mn:ap"}])
            kb.append(_back_row())
            return ov.render_legs(rows) + "\n\n👆 هر پا را مکث/ادامه بده؛ یا کلِّ اختاپوس را از فلگ‌ها کنترل کن:", kb
        if key == "report":
            return od.render_debug(od.scan()), [_back_row()]
        if key == "mission":
            return ("② مأموریت جدید\nبه زبانِ ساده بنویس چی می‌خوای. اگر کارِ مهمی باشد "
                    "(پول/کد/حذف/ارسال/…) برایت کارتِ تأیید می‌آید و تا ✅ نزنی اجرا نمی‌شود؛ "
                    "بقیه مستقیم انجام می‌شود. هیچ قابلیتی حذف نشده — فقط گیتِ توست.",
                    [_back_row()])
        if key == "stop":
            return ("⑥ توقف اضطراری\nبرای خواباندنِ اجرای خودکار: دستورِ /panic را بفرست "
                    "(داده حذف نمی‌شود، فقط اجرا می‌ایستد).", [_back_row()])
    except Exception:
        return "🐙 پنل موقتاً در دسترس نیست.", [_back_row()]
    return render_menu()  # m:home or anything unknown -> home


if __name__ == "__main__":
    t, kb = render_menu()
    print(t)
    print("buttons:", [b["callback_data"] for row in kb for b in row])
    for cb in ("m:status", "m:legs", "m:report", "m:mission", "m:stop", "m:home", "m:bogus"):
        txt, _ = dispatch(cb)
        print(f"\n[{cb}]\n{txt[:120]}")
