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
            if heads and heads[-1] >= opslib.today():
                items.append(f"❓ سوال‌های تازه در AGENT_QUESTIONS ({heads[-1]})")
    except OSError:
        pass
    # ۳) دادهٔ پولی: بدونِ CSV بانکی velocity پولی صفر می‌ماند
    try:
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
    return {"items": items, "hash": digest_hash, "n": len(items),
            "ts": opslib.now_iso()}


if __name__ == "__main__":
    print(json.dumps(compute(), ensure_ascii=False, indent=2))
