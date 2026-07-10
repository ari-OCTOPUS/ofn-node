#!/usr/bin/env python3
"""part_loops.py — لوپِ یادگیری+خود-تغییر برای «هر بخش» (جلسه ۴۶).

رأی مالک: «اتوماتیک‌تر کن؛ برای هر بخش لوپ‌های یادگیرنده و تغییردهنده طرح کن.»
به‌جای یک لوپِ مرکزیِ تنها، هر بخشِ اختاپوس لوپِ خودش را دارد با سه گام:
  observe (probe سلامتِ خودش) → learn (مقایسه با آستانه/تاریخچه) → propose (پیشنهادِ بهبود).

ارکستریتور (`run_all`) همهٔ بخش‌ها را روی ضربان می‌چرخاند، رویداد emit می‌کند، و
پیشنهادها را در `state/cortex/part-loops-latest.json` می‌نویسد → `improve.gather_signals`
آن را به `/upgrades` و خانهٔ آره/نه می‌برد. **propse-only**: knobِ $0 قابلِ‌auto، بقیه به مالک.
هیچ بازنویسیِ خودکارِ کد (مرزِ L4/L5 دست‌نخورده). $0 · stdlib · fail-soft · read-only probe.

هر پیشنهاد: {part, title, action, change_level(tune|reconfig|code), auto_ok}.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_OPS = _HERE.parent
if str(_OPS / "budget") not in sys.path:
    sys.path.insert(0, str(_OPS / "budget"))
import opslib  # noqa: E402

STATE = opslib.STATE_DIR
OUT = STATE / "cortex" / "part-loops-latest.json"


def _r(p: Path) -> dict:
    try:
        return json.loads(p.read_text("utf-8")) if p.exists() else {}
    except (OSError, ValueError):
        return {}


def _prop(part, title, action, level="reconfig", auto=False) -> dict:
    return {"part": part, "title": title, "action": action,
            "change_level": level, "auto_ok": bool(auto)}


# ── هر بخش: (status, [proposals]) ────────────────────────────────────────────────
def _loop_heart():
    h = _r(STATE / "pulse" / "heart-shadow-latest.json")
    period = h.get("period_s")
    gate0 = h.get("gate0_live_producer")
    wire = (h.get("production_wire") or {}).get("open")
    status = "🟢" if period else "🟡"
    props = []
    if not gate0:
        props.append(_prop("قلب", "قلب هنوز دادهٔ کافی برای هدایتِ زنده ندارد",
                           "بگذار ~۱۲ ساعت نمونه جمع شود؛ خودکار باز می‌شود.", "tune"))
    if period and not wire:
        props.append(_prop("قلب", "قلب در سایه می‌تپد (هنوز واقعی نمی‌راند)",
                           "بعد از Gate-0 خودش زنده می‌شود؛ کاری لازم نیست.", "tune"))
    return {"id": "heart", "name": "❤️ قلب", "status": status,
            "detail": f"ضربان {round(period) if period else '—'}s"}, props


def _loop_cortex():
    c = _r(STATE / "cortex" / "cortex-state.json")
    coh = c.get("coherence")
    status = "🟢" if (coh or 0) >= 0.7 else ("🟡" if coh is not None else "⚪")
    props = []
    if coh is not None and coh < 0.6:
        props.append(_prop("مغز", f"هم‌آهنگیِ اعضا پایین است ({round(coh*100)}٪)",
                           "چند عضو کهنه‌اند؛ بررسیِ تازگیِ داده‌ها.", "reconfig"))
    return {"id": "cortex", "name": "🧠 مغز", "status": status,
            "detail": f"هم‌آهنگی {round(coh*100) if coh is not None else '—'}٪"}, props


def _loop_doctor():
    rf = _r(STATE / "doctor" / "rfcs.json")
    rfcs = rf.get("rfcs") or []
    pending = sum(1 for r in rfcs if r.get("status") in ("submitted", "drafted"))
    status = "🟡" if pending else "🟢"
    props = []
    if pending >= 3:
        props.append(_prop("دکتر", f"{pending} پیشنهادِ بهبود منتظرِ رأیِ توست",
                           "در خانه با آره/نه تصمیم بگیر.", "reconfig"))
    return {"id": "doctor", "name": "🩺 دکتر", "status": status,
            "detail": f"{pending} منتظر"}, props


def _loop_money():
    t = _r(STATE / "telemetry-latest.json")
    month = (t.get("month") or {}).get("aud")
    status = "🟢"
    props = []
    if isinstance(month, (int, float)):
        if month >= 24:      # ۸۰٪ سقفِ ۳۰
            status = "🔴"
            props.append(_prop("پول", f"خرجِ ماه به {month:.0f} از ۳۰ دلار رسید",
                               "نزدیکِ سقف — تا اولِ ماه پولیِ نو محدود می‌شود.", "reconfig"))
        elif month >= 15:
            status = "🟡"
    return {"id": "money", "name": "💰 پول", "status": status,
            "detail": f"{month if month is not None else 0}$/۳۰"}, props


def _loop_learning():
    try:
        sys.path.insert(0, str(_HERE))
        import discoveries
        recent = len(discoveries.recent(20, within_h=48))
    except Exception:  # noqa: BLE001
        recent = 0
    status = "🟢" if recent else "🟡"
    props = []
    if recent == 0:
        props.append(_prop("یادگیری", "اخیراً چیزِ تازه‌ای یاد نگرفته",
                           "کادنسِ تحقیقِ وب را تندتر کن (knob، $0).", "tune", auto=True))
    return {"id": "learning", "name": "📚 یادگیری", "status": status,
            "detail": f"{recent} کشفِ ۴۸h"}, props


def _loop_legs():
    p = STATE / "selfheal-events.jsonl"
    heals = 0
    try:
        if p.exists():
            import time as _t
            cut = _t.time() - 86400
            for ln in p.read_text("utf-8").splitlines()[-50:]:
                try:
                    if float(json.loads(ln).get("ts", 0)) >= cut:
                        heals += 1
                except (ValueError, TypeError):
                    continue
    except OSError:
        pass
    status = "🟡" if heals >= 5 else "🟢"
    props = []
    if heals >= 5:
        props.append(_prop("اعضا", f"امروز {heals} بار خودترمیمی شد — یه عضو ناپایدار است",
                           "بررسیِ ریشه‌ایِ آن عضو (به مالک گزارش).", "reconfig"))
    return {"id": "legs", "name": "🦿 اعضا", "status": status,
            "detail": f"{heals} خودترمیم/روز"}, props


def _loop_self():
    sm = _r(STATE / "cortex" / "self-model.json")
    aware = sm.get("self_awareness_pct")
    status = "🟢" if (aware or 0) >= 90 else "🟡"
    props = []
    undoc = sm.get("undocumented") or []
    if undoc:
        props.append(_prop("خودآگاهی", f"{len(undoc)} ماژول بدونِ توضیح",
                           "یک docstringِ یک‌خطی به هرکدام (سندی، بی‌خطر).", "tune"))
    return {"id": "self", "name": "🪞 خودمدلی", "status": status,
            "detail": f"{aware if aware is not None else '—'}٪ سند"}, props


LOOPS = [_loop_heart, _loop_cortex, _loop_doctor, _loop_money,
         _loop_learning, _loop_legs, _loop_self]


def run_all(beat: int = 0) -> dict:
    """لوپِ همهٔ بخش‌ها را بچرخان → وضعیت + پیشنهادها؛ رویداد emit + persist."""
    parts, proposals = [], []
    for fn in LOOPS:
        try:
            st, props = fn()
        except Exception as e:  # noqa: BLE001 — یک بخشِ خطادار کلِ لوپ را نکشد
            st, props = {"id": getattr(fn, "__name__", "?"), "name": "?",
                         "status": "⚪", "detail": f"err:{type(e).__name__}"}, []
        parts.append(st)
        proposals.extend(props)
    digest = {"ts": opslib.now_iso(), "schema": "part-loops.v1", "beat": beat,
              "parts": parts, "n_proposals": len(proposals), "proposals": proposals}
    try:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        with opslib.LockedJson(OUT) as lj:
            lj.write(digest)
    except Exception as e:  # noqa: BLE001
        opslib.alert([f"part_loops persist failed: {e}"])
    # رویدادِ ساختاریافته برای داشبورد
    try:
        sys.path.insert(0, str(_OPS))
        import events
        bad = [p for p in parts if p["status"] in ("🔴", "🟡")]
        events.emit("task.completed", "part-loops",
                    summary=f"لوپِ {len(parts)} بخش چرخید — {len(proposals)} پیشنهاد" +
                    (f"، {len(bad)} بخش نیازِ توجه" if bad else ""),
                    next_action="خانه: /upgrades" if proposals else "")
    except Exception:  # noqa: BLE001
        pass
    return digest


def summary() -> dict:
    """خلاصهٔ سبکِ آخرین دور (خوراکِ داشبورد/خانه)."""
    d = _r(OUT)
    return {"parts": [{"name": p["name"], "status": p["status"], "detail": p.get("detail")}
                      for p in (d.get("parts") or [])],
            "n_proposals": d.get("n_proposals", 0)}


if __name__ == "__main__":
    print(json.dumps(run_all(), ensure_ascii=False, indent=2))
