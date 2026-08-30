#!/usr/bin/env python3
"""needs_digest.py — «به چی نیاز دارم؟» برای مالکِ ADHD.

فهرستِ کوتاه (≤۵ آیتم، هر کدام یک خط) از چیزهایی که سیستم واقعاً از مالک می‌خواهد:
داده، تأیید، یا یک اقدامِ یک‌باره. فقط‌خواندنی، $0، stdlib — هیچ effector.
مصرف‌کننده‌ها: صفحهٔ «📌 الان» کابین + نوتیفِ هوشمندِ needs_nudge (wiring).
"""
from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE))
import opslib  # noqa: E402


def _read_json(p: Path) -> dict:
    try:
        return json.loads(p.read_text("utf-8")) if p.exists() else {}
    except (OSError, ValueError):
        return {}


def _owner_parked(domain: str) -> bool:
    """آیا مالک این حوزه را صریحاً **پارک** کرده؟

    منبع: `VERDICT_QUEUE.md` در ریشهٔ vault — صفِ تصمیم‌های خودِ مالک. تا
    ۲۰۲۶-۰۷-۲۷ هیچ خطِ کدی آن فایل را باز نمی‌کرد، پس ارگانیسم چیزی را مطالبه
    می‌کرد که مالک با کلماتِ خودش متوقف کرده بود (`VQ-ACCT-PARK`: «حساب‌کتاب‌ها را
    قاطی نکن چون همهٔ داده‌ها را نداده‌ام»).

    fail-OPEN عمدی: اگر فایل نبود یا خوانده نشد، `False` برمی‌گردد — یعنی رفتارِ
    قبلی. سکوتِ اشتباه بدتر از نویزِ اشتباه است؛ ارگانیسم نباید به‌خاطرِ یک خطای
    خواندن، نیازی را از چشمِ مالک پنهان کند."""
    try:
        p = opslib.ORG_ROOT / "VERDICT_QUEUE.md"
        if not p.exists():
            return False
        key = f"VQ-{str(domain).upper()}-PARK"
        for line in p.read_text("utf-8", errors="replace").splitlines():
            if line.startswith("|") and key in line and "PARK" in line.upper():
                return True
    except OSError:
        return False
    return False


def compute(pending_count: int | None = None) -> dict:
    """نیازهای فعلی. خروجی: {items:[str], hash:str, n:int}. هر آیتم ≤۷۰ کاراکتر."""
    items: list[str] = []
    state = opslib.STATE_DIR
    # ۱) کارت‌های تأییدِ معلق (از کانال تزریق می‌شود — منبعِ in-memory)
    if pending_count:
        items.append(f"📮 {pending_count} کارتِ تأیید منتظرِ توست — /queue")
    # ۲) سوال‌های باز روی میزت (آخرین سربرگِ تاریخ‌دارِ AGENT_QUESTIONS)
    try:
        aq = opslib.AGENT_QUESTIONS
        if aq.exists():
            tail = aq.read_text("utf-8")[-4000:]
            heads = re.findall(r"## (2026-\d\d-\d\d)[^\n]*", tail)
            # ۲۰۲۶-۰۷-۲۷ — شرطِ قبلی `heads[-1] >= today()` **وارونه** بود: سؤال
            # فقط در همان روزی که پرسیده شد دیده می‌شد و فردایش برای همیشه نامرئی.
            # یعنی هرچه سؤال قدیمی‌تر و معطل‌تر، کمتر دیده می‌شد — دقیقاً برعکسِ
            # چیزی که باید. اندازه‌گیری: ۳۰ سربرگ، قدیمی‌ترین ۲۰۲۶-۰۷-۰۴، و صفر
            # نمایش. حالا کهنگی خودش سیگنال است.
            if heads:
                oldest, newest = min(heads), max(heads)
                try:
                    import datetime as _dt
                    _age = (_dt.date.fromisoformat(opslib.today())
                            - _dt.date.fromisoformat(oldest)).days
                except (TypeError, ValueError):
                    _age = 0
                if _age >= 2:
                    items.append(f"❓ {len(heads)} سوالِ بی‌جواب در AGENT_QUESTIONS — "
                                 f"قدیمی‌ترین {oldest} ({_age} روز)")
                elif newest >= opslib.today():
                    items.append(f"❓ سوال‌های تازه در AGENT_QUESTIONS ({newest})")
    except OSError:
        pass
    # ۳) دادهٔ پولی: بدونِ CSV بانکی velocity پولی صفر می‌ماند
    #
    # ۲۰۲۶-۰۷-۲۷ — ولی **فقط اگر مالک پارکش نکرده باشد**. `VQ-ACCT-PARK` در
    # VERDICT_QUEUE.md با کلماتِ خودش می‌گوید «حساب‌کتاب‌ها را قاطی نکن چون همهٔ
    # داده‌ها را نداده‌ام». تا امروز هیچ کدی آن فایل را نمی‌خواند، پس این خط هر روز
    # صدرِ لیستِ «📌 الان» بود — یعنی اختاپوس چیزی را مطالبه می‌کرد که مالک صریحاً
    # متوقفش کرده بود. تفاوتِ «نمی‌دانم» با «تو گفتی نپرس» همین است.
    try:
        if not _owner_parked("ACCT"):
            rec_dir = opslib.OPS / "reconcile"
            if not any(rec_dir.glob("*.csv")):
                items.append("💵 CSV واریزی‌ها نیست → قلب پول را نمی‌بیند (بذار در _ops/reconcile)")
    except OSError:
        pass
    # ۳.۵) حسابداری (اسکنِ 2026-07-16 #14): صفِ مرور/ثبت — از سایدکارِ acct_beat
    # (فقط‌خواندنی؛ اگر ضربان خاموش/سایدکار غایب → سکوتِ صادق، نه عددِ کهنه)
    acct = _read_json(state / "ORGANISM-STATE.accounting")
    if acct:
        pr = int(acct.get("pending_review", 0) or 0)
        pb = int(acct.get("pending_books", 0) or 0)
        if pr:
            items.append(f"🧮 {pr} تراکنش منتظرِ دسته‌بندیِ توست — /review")
        if pb:
            items.append(f"📚 {pb} ثبتِ پیشنهادی منتظرِ تأییدِ توست — /books")
        if acct.get("drift_alarm"):
            items.append("⚠️ دقتِ قواعدِ حسابدار افت کرده (drift) — /review را مرور کن")
    # ۴) قلب: منتظرِ seedِ باند یا در حالِ جمعِ نمونه (Gate-0)
    pulse = state / "pulse"
    shadow = _read_json(pulse / "heart-shadow-latest.json")
    if shadow:
        if not (pulse / "heart-setpoint-latest.json").exists():
            items.append("🫀 قلب منتظرِ اولین velocity برای seedِ باند (HH-P8)")
        sig = _read_json(pulse / "heart-signals-latest.json")
        d = (sig.get("delta_self") or {})
        if d.get("authoritative") is False and d.get("sample_size") is not None:
            k = d.get("sample_size", 0)
            need = d.get("min_samples", 48)
            if k < need:
                items.append(f"⏳ Gate-0: نمونهٔ ساعتی {k}/{need} — فقط صبر")
    # ۵) chrono persist نشده (R15)
    if not (state / "chrono.db").exists():
        items.append("⏱ chrono.db ساخته نشده (R15) — یک restart بعد از merge کافی است")
    # ۶) هشدارهای امروزِ گاورنر
    try:
        alerts = opslib.ALERTS_MD
        if alerts.exists():
            today = opslib.today()
            tail = alerts.read_text("utf-8")[-6000:]
            n_today = tail.count(f"## {today}")
            if n_today:
                items.append(f"🚨 {n_today} هشدارِ امروز در governor-alerts")
    except OSError:
        pass
    items = items[:5]
    digest_hash = hashlib.sha256("|".join(items).encode("utf-8")).hexdigest()[:16]
    # ۲۰۲۶-۰۷-۲۸ — `stable_hash`: هویتِ **نگرانی‌ها**، نه متنِ لحظه‌ایشان.
    #
    # اندازه‌گیریِ رونوشتِ واقعی: کارتِ «نیازت دارم» چهار بار با **همان سه آیتم**
    # آمد و تنها چیزی که عوض می‌شد شمارندهٔ هشدار بود: ۱۳ → ۱۴ → ۱۶ → ۱۸ → ۲۵.
    # چون `hash` روی متنِ آیتم‌هاست و متن شامل همان عدد است، هر تیک
    # `changed=True` می‌شد و همان سه نگرانی دوباره فرستاده می‌شد. این
    # اطلاع‌رسانی نیست، غر زدن است — و بدتر: سیگنالِ واقعی را بی‌ارزش می‌کند.
    #
    # راه‌حل: برای **تصمیمِ فرستادن** رشتهٔ ارقام‌زدوده را hash کن. عدد در
    # نمایش دست‌نخورده می‌ماند (مالک عددِ امروز را می‌بیند)، ولی «۲۵ هشدار» و
    # «۳۳ هشدار» یک نگرانیِ واحد شمرده می‌شوند. اگر نگرانیِ تازه‌ای اضافه یا
    # حذف شود، رشته واقعاً فرق می‌کند و کارت می‌آید.
    #
    # ⚠️ ارقام‌زداییِ **سراسری** غلط بود و تستِ موجود گرفتش: `t_d_nudge_sends_
    # once_then_throttles` می‌سنجد که رشدِ صفِ تأیید (۱ → ۳) خبر بدهد. آن هم
    # یک عدد است، ولی سیگنالِ واقعی — نه رانشِ شمارنده. تفاوتشان معنایی است:
    #   · «۳ → ۲۰ تراکنشِ منتظرِ تو»  → بک‌لاگِ خودت بزرگ شد. باید بدانی.
    #   · «۱۳ → ۲۵ هشدارِ امروز»      → شمارندهٔ یک فایلِ فقط‌افزودنی. نویز.
    # پس فقط همان یک خط بی‌اثر می‌شود، نه هر عددی.
    #
    # `hash` قدیمی دست‌نخورده برمی‌گردد تا هیچ خواننده‌ای نشکند.
    _NOISY = ("هشدارِ امروز", "governor-alerts")

    def _key(it: str) -> str:
        return re.sub(r"\d+", "#", it) if any(k in it for k in _NOISY) else it

    _norm = "|".join(_key(it) for it in items)
    stable_hash = hashlib.sha256(_norm.encode("utf-8")).hexdigest()[:16]
    return {"items": items, "hash": digest_hash, "stable_hash": stable_hash,
            "n": len(items), "ts": opslib.now_iso()}


if __name__ == "__main__":
    print(json.dumps(compute(), ensure_ascii=False, indent=2))
