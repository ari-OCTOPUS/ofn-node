#!/usr/bin/env python3
"""innervation.py — نقشهٔ عصب‌کشی: قلب → ستونِ فقرات → همهٔ اندام‌ها (جلسه ۴۶).

رأی مالک: «ستونِ فقرات کامل به قلب وصل باشه، قلب به تمومِ اندام‌ها وصل باشه، و با
ضربانش کنترلِ کلی داشته باشه و کم‌نقطهٔ مرده.»

مدل: ضربانِ ستونِ فقرات (chrono pacemaker) هر اندام را beat می‌زند؛ قلب ریتمِ آن را
تعیین می‌کند. این ماژول تازگیِ stateِ هر اندام را می‌سنجد → «عصب‌دار (زنده)» یا
«نقطهٔ مرده (beat نمی‌خورد)». + `heart_period_now()` = ریتمِ کنترلِ کلی که همه می‌خوانند.

$0 · stdlib · read-only · fail-soft.
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

_HERE = Path(__file__).resolve().parent
if str(_HERE.parent / "budget") not in sys.path:
    sys.path.insert(0, str(_HERE.parent / "budget"))
import opslib  # noqa: E402

STATE = opslib.STATE_DIR

# (id, نام, مسیرِ stateِ اندام نسبت به STATE_DIR, SLAِ دقیقه = چند دقیقه یک‌بار باید تازه شود)
#  SLA بر اساسِ کادنسِ واقعیِ هر اندام (کندترها SLAِ بزرگ‌تر).
ORGANS = [
    ("spine",    "🦴 ستونِ فقرات (pacemaker)", "ORGANISM-STATE.json",        5),
    ("heart",    "❤️ قلب",                     "pulse/heart-shadow-latest.json", 30),
    ("cortex",   "🧠 مغزِ مرکزی",              "cortex/cortex-state.json",    30),
    ("work",     "⚙️ پمپِ کار",                "pulse/work-state.json",       360),
    ("stress",   "🫀 استرس",                   "cortex/stress-latest.json",   30),
    ("parts",    "🔁 لوپِ بخش‌ها",             "cortex/part-loops-latest.json", 120),
    ("business", "💼 مغزِ دومِ کسب‌وکار",       "cortex/business-brain-latest.json", 120),
    ("learning", "📚 یادگیری/تحقیق",           "pulse/research-latest.json",  1440),
    ("selfmodel","🪞 خودمدلی",                 "cortex/self-model.json",      120),
    ("telemetry","💰 تلمتریِ مالی",            "telemetry-latest.json",       360),
]


def _age_min(rel: str) -> float | None:
    p = STATE / rel
    try:
        if not p.exists():
            return None
        return (time.time() - p.stat().st_mtime) / 60.0
    except OSError:
        return None


def heart_period_now() -> float | None:
    """ریتمِ کنترلِ کلی: periodِ فعلیِ قلب (ثانیه) که همهٔ اندام‌ها می‌توانند بخوانند."""
    try:
        d = json.loads((STATE / "pulse" / "heart-shadow-latest.json").read_text("utf-8"))
        return float(d.get("period_s")) if d.get("period_s") is not None else None
    except (OSError, ValueError, TypeError):
        return None


def check() -> dict:
    """نقشهٔ عصب‌کشی: هر اندام عصب‌دار (تازه) است یا نقطهٔ مرده؟"""
    organs, dead = [], []
    # P6 (truth-map 2026-07-17): SLAی spine پویا از cadenceِ واقعیِ قلب. SLAی ثابتِ ۵
    # برای tickِ ۵دقیقه‌ای کالیبره شده بود؛ با قلبِ باز (period 900s) سنِ measured همیشه
    # ~۱۵min بود و spine هر tick با ~۶ ثانیه اختلاف «نقطهٔ مرده» می‌شد (آرتیفکتِ U1).
    _hp = heart_period_now()
    for oid, name, rel, sla in ORGANS:
        if oid == "spine" and _hp:
            try:
                sla = max(sla, int(round(float(_hp) / 60.0)) + 2)
            except (TypeError, ValueError):
                pass
        age = _age_min(rel)
        if age is None:
            status, ok = "⚪ هنوز نزاده", False       # فایل نیست → هنوز beat نخورده
        elif age <= sla:
            status, ok = "🟢 عصب‌دار", True
        elif age <= sla * 3:
            status, ok = "🟡 کند", True
        else:
            status, ok = "🔴 نقطهٔ مرده", False
        organs.append({"id": oid, "name": name, "status": status,
                       "age_min": None if age is None else round(age, 1),
                       "sla_min": sla, "connected": ok})
        if not ok and age is not None:               # فقط زادهٔ مرده = نقطهٔ مردهٔ واقعی
            dead.append(name)
    born = [o for o in organs if o["age_min"] is not None]
    connected = [o for o in born if o["connected"]]
    coverage = round(100.0 * len(connected) / max(1, len(born)), 0)
    return {"ts": opslib.now_iso(), "schema": "innervation.v1",
            "heart_period_s": heart_period_now(),
            "coverage_pct": coverage, "n_organs": len(organs),
            "n_born": len(born), "dead_spots": dead, "organs": organs}


def persist() -> dict:
    a = check()
    try:
        p = STATE / "cortex" / "innervation-latest.json"
        p.parent.mkdir(parents=True, exist_ok=True)
        prev = {}
        try:
            prev = json.loads(p.read_text("utf-8")) if p.exists() else {}
        except (OSError, ValueError):
            prev = {}
        with opslib.LockedJson(p) as lj:
            lj.write(a)
        # نقطهٔ مردهٔ نو → رویداد (اندامی که beat نمی‌خورد = مشکلِ عصب‌کشی)
        new_dead = set(a["dead_spots"]) - set(prev.get("dead_spots", []))
        if new_dead:
            sys.path.insert(0, str(_HERE.parent))
            import events
            events.emit("task.blocked", "innervation",
                        summary=f"🔴 نقطهٔ مرده: {'، '.join(new_dead)} beat نمی‌خورد",
                        status="failed", next_action="خانه: بررسیِ عصب‌کشی")
    except Exception as e:  # noqa: BLE001
        opslib.alert([f"innervation persist failed: {e}"])
    return a


def summary() -> dict:
    try:
        d = json.loads((STATE / "cortex" / "innervation-latest.json").read_text("utf-8"))
    except (OSError, ValueError):
        d = check()
    return {"coverage_pct": d.get("coverage_pct"), "heart_period_s": d.get("heart_period_s"),
            "dead_spots": d.get("dead_spots", []),
            "organs": [{"name": o["name"], "status": o["status"]} for o in d.get("organs", [])]}


if __name__ == "__main__":
    print(json.dumps(check(), ensure_ascii=False, indent=2))
