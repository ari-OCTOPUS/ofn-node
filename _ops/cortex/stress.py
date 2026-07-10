#!/usr/bin/env python3
"""stress.py — هومئوستاتِ استرس/ترس (کورتیزولِ ارگانیسم) (جلسه ۴۶).

رأی مالک: «به جریانِ مالی و ضربانِ قلب و اینا استرس بده و ترسِ زیاد اگه بد کار کردن،
که جامعه تحت کنترل و نظم باشه — عینِ تنشِ انسانی.»

مدلِ زیستی: هر زیرسیستم یک سطحِ استرس (۰..۱) دارد که از **بدکارکردنِ خودش** بالا می‌رود
و با بهبود فروکش می‌کند (هومئوستاز). عبور از آستانه = حالتِ **ترس**: خودمختاری تنگ‌تر و
رفتار محافظه‌کارتر (fail-closed) می‌شود، و به مالک هشدار می‌رود. این «جامعهٔ ایجنت‌ها» را
منظم نگه می‌دارد: بدکارکن‌ها خودکار مهار می‌شوند.

**ترس = محافظه‌کاری، نه تخریب:** بالاترین اثر = توقفِ خود-تغییری + مهارِ کار + escalate.
هیچ اقدامِ مخرب. $0 · stdlib · read-only signals · fail-soft.
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
FEAR_THRESHOLD = 0.75      # استرس بالای این = ترس (تنگ‌شدنِ خودمختاری)
MONEY_CAP = 30.0


def _r(f: str) -> dict:
    p = STATE / f
    try:
        return json.loads(p.read_text("utf-8")) if p.exists() else {}
    except (OSError, ValueError):
        return {}


def _clamp(x: float) -> float:
    return max(0.0, min(1.0, x))


# ── استرسِ هر زیرسیستم از بدکارکردنِ واقعیِ خودش (۰..۱) ─────────────────────────────
def _money_stress() -> tuple[float, str]:
    m = (_r("telemetry-latest.json").get("month") or {}).get("aud") or 0
    s = _clamp(float(m) / MONEY_CAP)        # نزدیکِ سقف = استرس؛ عبور = ترس
    return s, f"{float(m):.0f}/{MONEY_CAP:.0f} دلار"


def _heart_stress() -> tuple[float, str]:
    sig = (_r("replication-latest.json").get("sigma") or {}).get("sigma_effective") or 0
    # σ→۱ = محورِ سرطان = بالاترین ترس (spawn بی‌مهار)
    s = _clamp(float(sig) / 1.0)
    return s, f"σ={float(sig):.2f}"


def _legs_stress() -> tuple[float, str]:
    p = STATE / "selfheal-events.jsonl"
    n = 0
    try:
        if p.exists():
            cut = time.time() - 86400
            for ln in p.read_text("utf-8").splitlines()[-60:]:
                try:
                    if float(json.loads(ln).get("ts", 0)) >= cut:
                        n += 1
                except (ValueError, TypeError):
                    continue
    except OSError:
        pass
    s = _clamp(n / 8.0)        # ۸ خودترمیم/روز = ناپایداریِ بالا
    return s, f"{n} خودترمیم/روز"


def _doctor_stress() -> tuple[float, str]:
    rf = _r("doctor/rfcs.json").get("rfcs") or []
    pending = sum(1 for r in rf if r.get("status") in ("submitted", "drafted"))
    s = _clamp(pending / 6.0)
    return s, f"{pending} پیشنهادِ معطل"


def _alerts_stress() -> tuple[float, str]:
    al = opslib.OPS / "governor" / "governor-alerts.md"
    try:
        n = len(al.read_text("utf-8").splitlines()) if al.exists() else 0
    except OSError:
        n = 0
    # نسبتِ رشد نامعلوم است؛ حجمِ بالا = استرسِ ملایمِ نظارتی (سقفِ ۰.۵)
    return _clamp(n / 400.0) * 0.5, f"{n} خطِ هشدار"


_SUBSYSTEMS = {
    "money": ("💰 جریانِ مالی", _money_stress),
    "heart": ("❤️ ضربانِ قلب", _heart_stress),
    "legs": ("🦿 اعضا", _legs_stress),
    "doctor": ("🩺 دکتر", _doctor_stress),
    "alerts": ("🚨 هشدارها", _alerts_stress),
}


def assess() -> dict:
    """استرس/ترسِ همهٔ زیرسیستم‌ها + سطحِ استرسِ کلِ ارگانیسم."""
    subs = {}
    for sid, (name, fn) in _SUBSYSTEMS.items():
        try:
            s, detail = fn()
        except Exception:  # noqa: BLE001
            s, detail = 0.0, "—"
        subs[sid] = {"name": name, "stress": round(s, 2),
                     "fear": s >= FEAR_THRESHOLD, "detail": detail}
    in_fear = [sid for sid, v in subs.items() if v["fear"]]
    # استرسِ ارگانیسم = بیشینهٔ زیرسیستم‌ها (یک عضوِ بحرانی کلِ جامعه را تحتِ فشار می‌برد)
    org = max((v["stress"] for v in subs.values()), default=0.0)
    return {"ts": opslib.now_iso(), "schema": "stress.v1",
            "organism_stress": round(org, 2), "in_fear": in_fear,
            "level": ("🔴 ترس" if org >= FEAR_THRESHOLD else
                      "🟡 استرس" if org >= 0.4 else "🟢 آرام"),
            "subsystems": subs}


def organism_in_fear() -> tuple[bool, str]:
    """آیا ارگانیسم در حالتِ ترس است؟ (خوراکِ گیتِ محافظه‌کاریِ auto_approve/…)."""
    a = assess()
    if a["in_fear"]:
        names = "، ".join(a["subsystems"][s]["name"] for s in a["in_fear"])
        return True, f"ترس در: {names} (استرسِ ارگانیسم {a['organism_stress']})"
    return False, f"آرام (استرس {a['organism_stress']})"


def persist() -> dict:
    """ارزیابی + نوشتن به state/cortex/stress-latest.json + رویداد اگر واردِ ترس شد."""
    a = assess()
    try:
        p = STATE / "cortex" / "stress-latest.json"
        p.parent.mkdir(parents=True, exist_ok=True)
        prev = _r("cortex/stress-latest.json")
        with opslib.LockedJson(p) as lj:
            lj.write(a)
        # رویداد فقط هنگامِ ورودِ نو به ترس (نه هر چرخه — ضدِ اسپم)
        new_fear = set(a["in_fear"]) - set(prev.get("in_fear", []))
        if new_fear:
            sys.path.insert(0, str(_HERE.parent))
            import events
            names = "، ".join(a["subsystems"][s]["name"] for s in new_fear)
            events.emit("task.blocked", "stress-homeostat",
                        summary=f"🔴 ترس: {names} بد کار می‌کنند — خودمختاری تنگ شد",
                        status="failed", next_action="خانه: بررسی",
                        approval_state="required")
    except Exception as e:  # noqa: BLE001
        opslib.alert([f"stress persist failed: {e}"])
    return a


if __name__ == "__main__":
    print(json.dumps(assess(), ensure_ascii=False, indent=2))
