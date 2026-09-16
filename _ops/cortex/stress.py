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


def _r(f: str) -> dict | None:
    """U1 (2026-09-07): فایلِ غایب/ناخوانا → None (ناشناخته)، نه {} (صفرِ آرام).
    خوانشِ موفقِ JSON خالی همچنان {} برمی‌گردد."""
    p = STATE / f
    try:
        if not p.exists():
            return None
        return json.loads(p.read_text("utf-8"))
    except (OSError, ValueError):
        return None


def _clamp(x: float) -> float:
    return max(0.0, min(1.0, x))


# ── استرسِ هر زیرسیستم از بدکارکردنِ واقعیِ خودش (۰..۱) ─────────────────────────────
def _money_stress() -> tuple[float | None, str]:
    raw = _r("telemetry-latest.json")
    if raw is None:                          # U1: غایب/خراب = ناشناخته، نه صفرِ آرام
        return None, "telemetry غایب/ناخوانا"
    m = (raw.get("month") or {}).get("aud") or 0
    s = _clamp(float(m) / MONEY_CAP)        # نزدیکِ سقف = استرس؛ عبور = ترس
    return s, f"{float(m):.0f}/{MONEY_CAP:.0f} دلار"


def _heart_stress() -> tuple[float | None, str]:
    raw = _r("replication-latest.json")
    if raw is None:                          # U1: غایب/خراب = ناشناخته
        return None, "replication غایب/ناخوانا"
    sig = (raw.get("sigma") or {}).get("sigma_effective") or 0
    # σ→۱ = محورِ سرطان = بالاترین ترس (spawn بی‌مهار)
    s = _clamp(float(sig) / 1.0)
    return s, f"σ={float(sig):.2f}"


def _legs_stress() -> tuple[float | None, str]:
    p = STATE / "selfheal-events.jsonl"
    if not p.exists():                       # U1: غایب = ناشناخته، نه «۰ خودترمیم»
        return None, "گزارشِ خودترمیم غایب/ناخوانا"
    n = 0
    try:
        cut = time.time() - 86400
        for ln in p.read_text("utf-8").splitlines()[-60:]:
            try:
                if float(json.loads(ln).get("ts", 0)) >= cut:
                    n += 1
            except (ValueError, TypeError):
                continue
    except OSError:
        return None, "گزارشِ خودترمیم غایب/ناخوانا"
    s = _clamp(n / 8.0)        # ۸ خودترمیم/روز = ناپایداریِ بالا
    return s, f"{n} خودترمیم/روز"


def _doctor_stress() -> tuple[float | None, str]:
    raw = _r("doctor/rfcs.json")
    if raw is None:                          # U1: غایب/خراب = ناشناخته
        return None, "rfcs.json غایب/ناخوانا"
    rf = raw.get("rfcs") or []
    pending = sum(1 for r in rf if r.get("status") in ("submitted", "drafted"))
    s = _clamp(pending / 6.0)
    return s, f"{pending} پیشنهادِ معطل"


def _alerts_stress() -> tuple[float | None, str]:
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
        if not al.exists():                  # U1: غایب = ناشناخته، نه «۰ هشدار»
            return None, "فایلِ هشدار غایب/ناخوانا"
        text = al.read_text("utf-8")
    except OSError:
        return None, "فایلِ هشدار غایب/ناخوانا"
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
    """استرس/ترسِ همهٔ زیرسیستم‌ها + سطحِ استرسِ کلِ ارگانیسم.

    U1 (2026-09-07, stress.v2): حسگرِ غایب/خراب دیگر «صفرِ آرام» تولید نمی‌کند —
    زیرسیستمِ ناشناخته stress=null و quality="unknown" می‌گیرد، در «unknown» فهرست
    می‌شود و data_quality ارگانیسم «degraded» می‌شود. ترس فقط از مقادیرِ
    شناخته‌شده محاسبه می‌شود (تورمِ هشدار نه)، ولی آرام‌نماییِ دادهٔ ناقص هم نه."""
    subs: dict = {}
    unknown: list = []
    for sid, (name, fn) in _SUBSYSTEMS.items():
        try:
            s, detail = fn()
        except Exception as e:  # noqa: BLE001 — خطای حسگر = ناشناخته، نه آرام
            s, detail = None, f"خطای حسگر: {type(e).__name__}"
        if s is None:
            unknown.append(sid)
            subs[sid] = {"name": name, "stress": None, "fear": False,
                         "quality": "unknown", "detail": detail}
        else:
            subs[sid] = {"name": name, "stress": round(s, 2),
                         "fear": s >= FEAR_THRESHOLD, "quality": "ok",
                         "detail": detail}
    in_fear = [sid for sid, v in subs.items() if v["fear"]]
    # استرسِ ارگانیسم = بیشینهٔ زیرسیستم‌های *شناخته‌شده*؛ همه ناشناخته ⇒ null (نه صفر)
    known = [v["stress"] for v in subs.values() if v["stress"] is not None]
    org = max(known) if known else None
    level = ("🔴 ترس" if org is not None and org >= FEAR_THRESHOLD else
             "🟡 استرس" if org is not None and org >= 0.4 else "🟢 آرام")
    return {"ts": opslib.now_iso(), "schema": "stress.v2",
            "organism_stress": round(org, 2) if org is not None else None,
            "in_fear": in_fear, "level": level,
            "data_quality": "degraded" if unknown else "ok",
            "unknown": unknown,
            "subsystems": subs}


def organism_in_fear() -> tuple[bool, str]:
    """آیا ارگانیسم در حالتِ ترس است؟ (خوراکِ گیتِ محافظه‌کاریِ auto_approve/…)."""
    # U1 (2026-09-07): حسگرِ ناشناخته در جزئیات حمل می‌شود — «آرامِ» گزارش‌شده
    # با دادهٔ سالم یکی نمی‌شود؛ گیتِ مصرف‌کننده (auto_approve) ناقص بودن را می‌بیند.
    a = assess()
    unk = f"؛ ⚠️ {len(a['unknown'])} حسگرِ ناشناخته" if a["unknown"] else ""
    if a["in_fear"]:
        names = "، ".join(a["subsystems"][s]["name"] for s in a["in_fear"])
        return True, f"ترس در: {names} (استرسِ ارگانیسم {a['organism_stress']}){unk}"
    calm = "آرام" if a["data_quality"] == "ok" else "آرام (دادهٔ ناقص)"
    return False, f"{calm} (استرس {a['organism_stress']}){unk}"


def persist() -> dict:
    """ارزیابی + نوشتن به state/cortex/stress-latest.json + رویداد اگر واردِ ترس شد."""
    a = assess()
    try:
        p = STATE / "cortex" / "stress-latest.json"
        p.parent.mkdir(parents=True, exist_ok=True)
        prev = _r("cortex/stress-latest.json") or {}
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
