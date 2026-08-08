#!/usr/bin/env python3
"""autonomy_matrix.py — ماتریسِ ردهٔ خودمختاری (رأی مالک، چت 2026-07-16 19:30).

رأی مالک (عین جمله): «می‌خوام گیتِ تأییدِ انسانی فقط برای مواردِ مهم در تلگرامِ
تعاملیِ واقعی باشه، بقیش آزاد بشه — و بقیشم بگو تصمیم بگیره انجام بده، سوال نپرسه.»

ترجمهٔ مهندسی — دو رده، یک منبعِ حقیقت (همین فایل):
  • **important** → همیشه گیتِ تعاملیِ تلگرام (کارتِ verdict با دکمه، OCTOPUS_TG_EXEC).
    فهرستِ سخت، آزادنشدنی با هیچ flag ای: پول/خرج/انتقال · secret/کلید · حذف/پاک‌سازی ·
    ارسال/انتشار به بیرون (ایمیل/فاکتور/پست) · merge به master / تغییرِ کد · ژنوم/ledger/
    schema/قانونِ اساسی · kill/halt/restart ِ عضوِ زنده · spawn/تکثیر · σ · human-append ·
    PII/هویتِ پارتنر/Project-F.
  • **free** → سیستم خودش تصمیم می‌گیرد و (اگر مسیرِ عملِ امن دارد) انجام می‌دهد؛
    هر خودتصمیم در ledger + لاگ ثبت می‌شود (شفافیتِ بدونِ سوال). پشتِ فلگِ
    OCTOPUS_AUTONOMY_FREE — خاموش = رفتارِ قبلی (همه‌چیز به مالک).

این ماژول فقط «رده» و «فلگ» می‌دهد — هیچ عملی اجرا نمی‌کند؛ مصرف‌کننده: auto_approve.
stdlib-only · fail-safe به سمتِ important (شک = گیتِ انسانی).
"""
from __future__ import annotations

import os
import re

FLAG = "OCTOPUS_AUTONOMY_FREE"

# فهرستِ مهم — سوپرمجموعهٔ _HIGH_RISK ِ auto_approve + کلاس‌هایی که آنجا غایب بودند
# (حذف/ارسال/انتشار/PII). شک = مهم. \b روی حروفِ فارسی هم کار می‌کند (unicode \w).
_IMPORTANT_RE = re.compile(
    r"(\bmoney\b|پول|دلار|\bdollar\b|خرج|\bspend\b|\bpay\b|پرداخت|انتقالِ? وجه|\btransfer\b|"
    r"\bbudget\b|بودجه|\bwallet\b|کیفِ? پول|"
    r"\bsecret\b|کلید|راز|\btoken\b|\bapi.?key\b|\bpem\b|\bseed\b|سید|"
    r"\bdelete\b|حذف|\bpurge\b|\berase\b|پاک‌?سازیِ? داده|\bremove\b|"
    r"\bsend\b|ارسال|\bpublish\b|انتشار|\bemail\b|ایمیل|فاکتور|\binvoice\b|\boutbound\b|"
    r"\bcode\b|کدِ|\bmerge\b|\bapply_merge\b|\bmaster\b|"
    r"ژنوم|\bgenome\b|\bledger\b|\bschema\b|قانونِ? اساسی|\bconstitution\b|"
    r"\bkill\b|\bhalt\b|\brestart\b|ری‌?استارت|\bstop\b|توقفِ? ارگان|"
    r"\bspawn\b|تکثیر|\breplicat|\bsigma\b|σ|\bhuman.?append\b|امضا|"
    r"\bpii\b|پارتنر|\bpartner\b|\bproject.?f\b|هویت)", re.I)


def free_enabled() -> bool:
    """آیا OCTOPUS_AUTONOMY_FREE روشن است؟ (پیش‌فرض خاموش = رفتارِ محافظه‌کارِ قبلی).

    ۲۰۲۶-۰۸-۰۸ (up-863c603099): حالا OWNER-PROFILE.json را هم می‌خواند. اگر
    answers.autonomy حاویِ «خودش» یا «انجام بده» یا «آزاد» باشد، یعنی مالک
    صریحاً خواسته که کارهای کوچک خودکار شوند. flag اولویت دارد (صریح‌تر)،
    OWNER-PROFILE fallback است."""
    if str(os.environ.get(FLAG, "")).strip().lower() in {"1", "true", "yes", "on"}:
        return True
    # fallback: OWNER-PROFILE answers.autonomy
    try:
        import json as _json
        from pathlib import Path as _P
        prof = _P(str(__import__("opslib").STATE_DIR)) / "OWNER-PROFILE.json"
        if prof.exists():
            d = _json.loads(prof.read_text("utf-8"))
            auto = str(d.get("answers", {}).get("autonomy", "") or "").lower()
            # مالک گفت «خودش انجام بده» / «آزاد» / «سوال نپرس» → free
            if any(w in auto for w in ("خودش", "انجام بده", "آزاد", "سوال نپرس")):
                return True
    except Exception:  # noqa: BLE001
        pass
    return False


def owner_autonomy_level() -> str:
    """سطحِ خودمختاریِ مالک از OWNER-PROFILE → 'free' | 'gated' | 'unknown'.

    ۲۰۲۶-۰۸-۰۸: پلِ بینِ OWNER-PROFILE.answers.autonomy و رفتارِ runtime.
    این تابع توسط self_audit probe خوانده می‌شود تا تأیید کند autonomy preference
    واقعاً مصرف می‌شود (نه فقط ثبت می‌شود)."""
    if free_enabled():
        return "free"
    return "gated"


def is_important(p: dict) -> tuple[bool, str]:
    """آیا این پیشنهاد در ردهٔ «مهم» (گیتِ انسانیِ تعاملی) است؟ → (bool, دلیل).
    fail-safe: ورودیِ ناسالم/غیرقابل‌خواندن = مهم."""
    try:
        if str(p.get("change_level", "")) == "code":
            return True, "change_level=code"
        blob = f"{p.get('title', '')} {p.get('action', '')} {p.get('suggested_action', '')}"
        m = _IMPORTANT_RE.search(blob)
        if m:
            return True, f"کلیدواژهٔ مهم: {m.group(0)}"
        return False, ""
    except Exception:  # noqa: BLE001 — شک = گیتِ انسانی
        return True, "ورودیِ ناخوانا — fail-safe به important"


if __name__ == "__main__":
    import json
    _demo = [
        {"title": "کادنسِ نمونه‌برداری را نرم کن", "action": "HEART_SAMPLE_INTERVAL_S"},
        {"title": "پولِ بیشتری به لید بده", "action": "budget"},
        {"title": "این فایل را حذف کن", "action": "delete old log"},
        {"title": "ایمیل به مشتری بفرست", "action": "send email"},
    ]
    print(json.dumps({"flag_on": free_enabled(),
                      "demo": [{"t": d["title"], "important": is_important(d)} for d in _demo]},
                     ensure_ascii=False, indent=2))
