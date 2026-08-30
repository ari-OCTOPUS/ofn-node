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

# نقطهٔ نیم‌اشباعِ استرسِ هشدار — **از دادهٔ واقعی، نه از حدس**.
# اشتقاق (۲۰۲۶-۰۷-۲۸): ۸۶۵ هشدارِ تاریخ‌دار در `governor-alerts.md` طیِ ۱۸ روز،
# با پنجرهٔ لغزانِ ۲۴ساعته هر ۶ ساعت → ۶۹ نمونه:
#     میانه ۰ · صدکِ ۷۵ = ۵۴ · صدکِ ۹۰ = ۱۱۸ · بیشینه ۴۰۱
#     ۳۴ پنجره غیرصفر (۴۹٪)، میانهٔ آن‌ها = ۵۹  ← همین عدد
# در `n/(n+k)` این یعنی «روزِ فعالِ معمولی = ۰.۵»، و منحنی هرگز صاف نمی‌شود.
# اگر روزی توزیع عوض شد، این عدد را از همان اسکریپت دوباره دربیاور — نه از حس.
_ALERT_HALF_POINT = 59
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
    """استرسِ هشدار از هشدارهای **اخیر**، نه از کلِ تاریخِ فایل.

    ⚠️ ۲۰۲۶-۰۷-۲۸ — نسخهٔ قبلی خطوطِ **کلِ** یک فایلِ append-only را می‌شمرد و
    روی `clamp(n/400)*0.5` اشباع می‌کرد. فایل امروز ۲۵۶۳ خط دارد، پس این عدد از
    مدت‌ها پیش روی سقفِ ۰.۵ **قفل** شده بود و دیگر هرگز پایین نمی‌آمد.

    یک شمارندهٔ یک‌طرفه نمی‌تواند سلامتِ **فعلی** را نشان دهد: فقط می‌گوید
    «تا حالا چقدر اتفاق افتاده»، نه «الان چه خبر است». و اثرش زنجیره‌ای بود —
    `organism_stress` روی ۰.۵ پین می‌شد، `organism.py` آن را به‌عنوان
    `error_rate` می‌داد، و `wiring.py` با آستانهٔ `>0.2` سیگنالِ `errors_high` را
    **در هر تیک** شلیک می‌کرد (اندازه‌گیری: ۷۰۳ از ۷۰۳). یعنی تنها ورودیِ فعالِ
    یادگیری یک ثابت بود، و ثابت اطلاعات ندارد.

    حالا فقط هشدارهای ۲۴ ساعتِ اخیر شمرده می‌شوند. تاریخچه دست‌نخورده می‌ماند —
    فقط دیگر به‌عنوان وضعیتِ لحظه‌ای خوانده نمی‌شود."""
    import datetime as _dt
    import os as _os
    import re as _re
    al = opslib.OPS / "governor" / "governor-alerts.md"
    try:
        text = al.read_text("utf-8") if al.exists() else ""
    except OSError:
        text = ""
    total = len(text.splitlines()) if text else 0
    cutoff = _dt.datetime.now() - _dt.timedelta(hours=24)
    recent = 0
    for m in _re.finditer(r"^##\s*(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})",
                          text, _re.M):
        try:
            if _dt.datetime.strptime(m.group(1), "%Y-%m-%dT%H:%M:%S") >= cutoff:
                recent += 1
        except ValueError:
            continue
    # بدونِ هیچ سرصفحهٔ تاریخ‌دار، رفتارِ قبلی (fail-soft) — ولی با سقفِ همان.
    if recent == 0 and total and not _re.search(r"^##\s*\d{4}-", text, _re.M):
        return _clamp(total / 400.0) * 0.5, f"{total} خطِ هشدار (بی‌تاریخ)"
    # ── کالیبراسیون از دادهٔ واقعی (۲۰۲۶-۰۷-۲۸، پشتِ فلگ) ────────────────────
    # فیکسِ صبح پنجره را ۲۴ساعته کرد ولی **سقف** را نگه داشت: `clamp(n/20)*0.5`
    # از n=۲۰ به بعد صاف می‌شود. توزیعِ واقعیِ ۱۸ روز (۶۹ پنجرهٔ ۲۴ساعته از
    # `governor-alerts.md`) می‌گوید چرا این بد است:
    #
    #     میانه ۰ · صدکِ ۷۵ = ۵۴ · صدکِ ۹۰ = ۱۱۸ · بیشینه ۴۰۱
    #     ۴۹٪ پنجره‌ها غیرصفرند؛ میانهٔ روزهای فعال = ۵۹
    #
    # یعنی نقطهٔ اشباع (۲۰) **زیرِ صدکِ ۷۵** است: هر روزِ فعالی همان ۰.۵ را
    # می‌دهد، چه ۲۰ هشدار باشد چه ۴۰۱. عدد دودویی می‌شود و **شدت** گم می‌شود.
    #
    # ⚠️ ولی یک تصحیحِ صادقانه: اندازه‌گیری نشان داد سیگنالِ دودویی `errors_high`
    # روی همین ۱۸ روز **۴۷٪** شلیک می‌کرده — یعنی آنتروپیِ ۰.۹۹۹ بیت، تقریباً
    # بیشینهٔ ممکن. پس ادعای «این سیگنال اطلاعات ندارد» از پنجرهٔ اخیر می‌آمد،
    # نه از کلِ تاریخ. سودِ واقعیِ این تغییر دو چیزِ دیگر است:
    #   ۱) `organism_stress` **پیوسته** می‌شود، نه پین‌شده روی ۰.۵.
    #   ۲) زیرسیستمِ هشدار برای اولین بار می‌تواند به `FEAR_THRESHOLD=0.75`
    #      برسد. با سقفِ ۰.۵ این **ساختاراً ناممکن** بود — یعنی یک سیگنالِ
    #      ایمنی که هرگز به آژیرِ خودش نمی‌رسید.
    #
    # `n/(n+k)` با k = میانهٔ روزهای فعال (۵۹): هرگز اشباع نمی‌شود، و k از داده
    # آمده نه از حدس. روی همان ۶۹ پنجره، ترس **۴ بار (۵٪)** شلیک می‌کرد —
    # استثنایی، نه پرسروصدا.
    if str(_os.environ.get("OCTOPUS_STRESS_CALIBRATED", "")).strip().lower() in (
            "1", "true", "yes", "on"):
        k = _ALERT_HALF_POINT
        graded = recent / (recent + k) if (recent + k) > 0 else 0.0
        return round(graded, 4), f"{recent} هشدارِ ۲۴ساعتِ اخیر (کالیبره، k={k})"
    return _clamp(recent / 20.0) * 0.5, f"{recent} هشدارِ ۲۴ساعتِ اخیر"


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
