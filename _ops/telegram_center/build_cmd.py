#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""build_cmd — هدایتِ کدنویسیِ خودِ اختاپوس از DM ِ لنگر.

رأیِ مالک ۲۰۲۶-۰۷-۳۰: «تلگرام واقعاً کدنویسیِ داخلیِ اختاپوس را هدایت کند؛
اختاپوس خودآگاهی دارد و باید خودش را بسازد، با اولاما، ۲۴ ساعته.»

تا امروز حلقهٔ کد **همه‌ی قطعاتش را داشت** ولی از تلگرام قابلِ هدایت نبود:
`code_brain.enqueue_task` وجود داشت و هیچ فرمانی صدایش نمی‌زد (`/code` به
`collab_coding` می‌رفت که چیزِ دیگری است)، و صف/پچ‌ها هیچ نمایی نداشتند.

این ماژول **فقط متن و صف** است:
  · هیچ‌چیز نمی‌فرستد (مرکز می‌فرستد)
  · هیچ پچی اعمال نمی‌کند (زنجیرهٔ موجود: shadow-test → کارتِ مالک → رأی →
    `consume_approvals`؛ هیچ گیتی این‌جا دور نمی‌خورد)
  · هیچ فلگی نمی‌سازد و هیچ‌کدام را روشن نمی‌کند

نردبانِ صداقت: اگر `OCTOPUS_CODE_BRAIN` خاموش باشد یا اولاما بالا نباشد،
همین را **می‌گوید** — «ثبت شد ولی مغز خاموش است» بهتر از صفِ ساکت است.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_OPS = _HERE.parent
for _p in (str(_OPS), str(_OPS / "cortex"), str(_OPS / "budget")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

_FA = str.maketrans("0123456789", "۰۱۲۳۴۵۶۷۸۹")


def _fa(n) -> str:
    return str(n).translate(_FA)


def _brain():
    import code_brain
    return code_brain


def _autonomy():
    import code_autonomy
    return code_autonomy


# ── وضعیتِ صادقانهٔ حلقه ────────────────────────────────────────────────────
def loop_status() -> dict:
    """هر پله را جدا گزارش کن — «روشن است» بی‌تفکیک، همان دروغی است که
    قرارداد ممنوع کرده."""
    st = {"brain_flag": False, "has_key": False, "ollama": False,
          "apply_wired": False, "active": False, "patch_card": False,
          "tasks": 0, "patches": 0}
    try:
        cb = _brain()
        st["brain_flag"] = bool(cb.enabled())
        st["has_key"] = bool(cb._has_key())
        st["tasks"] = len(cb.pending_tasks())
    except Exception:  # noqa: BLE001
        pass
    try:
        sys.path.insert(0, str(_OPS / "cortex"))
        import local_llm
        st["ollama"] = bool(local_llm.available())
    except Exception:  # noqa: BLE001
        pass
    try:
        ca = _autonomy()
        st["active"] = bool(ca.active())
        st["apply_wired"] = str(os.environ.get(
            "OCTOPUS_WIRE_CODE_APPLY", "")).strip().lower() in ("1", "true", "yes", "on")
        pend = ca.opslib.STATE_DIR / "cortex" / "pending-patches"
        st["patches"] = len(list(pend.glob("*.json"))) if pend.exists() else 0
    except Exception:  # noqa: BLE001
        pass
    st["patch_card"] = str(os.environ.get(
        "OCTOPUS_WIRE_PATCH_CARD", "")).strip().lower() in ("1", "true", "yes", "on")
    return st


def status_text() -> str:
    s = loop_status()
    def m(v):
        return "🟢" if v else "🔴"
    lines = [
        "🛠 <b>ساختِ خود — وضعیتِ حلقه</b>", "",
        f"{m(s['brain_flag'])} مغزِ کد (فلگ)",
        f"{m(s['has_key'] or s['ollama'])} تولیدکننده: "
        + ("پولی+محلی" if s["has_key"] and s["ollama"]
           else "پولی" if s["has_key"] else "اولاما ($0)" if s["ollama"]
           else "هیچ‌کدام — هیچ کدی تولید نمی‌شود"),
        f"{m(s['active'])} خودمختاریِ کد فعال (ACTIVATION + بی‌STOP)",
        f"{m(s['apply_wired'])} درایورِ اعمال وصل",
        f"{m(s['patch_card'])} کارتِ پچ به مالک (PATCH_CARD)",
        "",
        f"📥 صفِ کار: {_fa(s['tasks'])} · 🧩 پچِ منتظرِ رأی: {_fa(s['patches'])}",
    ]
    if not s["patch_card"]:
        lines.append("")
        lines.append("⚠️ PATCH_CARD خاموش است: پچ ساخته و سایه-تست می‌شود "
                     "ولی کارتش به تو نمی‌رسد — قفلِ چهارم، عمدی.")
    return "\n".join(lines)


# ── ثبتِ کارِ ساخت ──────────────────────────────────────────────────────────
def enqueue(text: str) -> dict:
    """متنِ مالک → یک taskِ ساخت. خروجی: {ok, id?, note}."""
    body = str(text or "").strip()
    if len(body) < 8:
        return {"ok": False, "note": "خیلی کوتاه است — بگو چه فایلی و چه تغییری."}
    try:
        tid = _brain().enqueue_task(body[:2000], source="telegram-owner")
    except Exception as e:  # noqa: BLE001
        return {"ok": False, "note": f"ثبت نشد: {type(e).__name__}"}
    s = loop_status()
    if not s["brain_flag"]:
        note = "ثبت شد — ولی مغزِ کد خاموش است، پس تا روشن‌شدنش کدی نوشته نمی‌شود."
    elif not (s["has_key"] or s["ollama"]):
        note = "ثبت شد — ولی نه کلیدِ پولی هست نه اولاما بالا؛ صف می‌مانَد."
    elif not s["patch_card"]:
        note = ("ثبت شد. پچ ساخته و سایه-تست می‌شود، ولی PATCH_CARD خاموش است "
                "پس کارتش به تو نمی‌رسد (قفلِ چهارم).")
    else:
        note = "ثبت شد. وقتی سایه سبز شد، کارتِ رأی برایت می‌آید."
    return {"ok": True, "id": tid, "note": note}


def queue_text(cap: int = 8) -> str:
    try:
        rows = _brain().pending_tasks()
    except Exception:  # noqa: BLE001
        return "📥 صف در دسترس نیست."
    if not rows:
        return "📥 صفِ ساخت خالی است. با «بساز: …» کار اضافه کن."
    out = [f"📥 <b>صفِ ساخت</b> — {_fa(len(rows))} کار"]
    for r in rows[:cap]:
        out.append(f"· <code>{r.get('id')}</code> — {str(r.get('task'))[:70]}")
    return "\n".join(out)


def patches_text(cap: int = 5) -> str:
    """پچ‌های منتظرِ رأی — فقط مسیر و نیت، هرگز محتوای کد (نویز + ریسکِ echo)."""
    try:
        import json
        ca = _autonomy()
        pend = ca.opslib.STATE_DIR / "cortex" / "pending-patches"
        files = sorted(pend.glob("*.json")) if pend.exists() else []
    except Exception:  # noqa: BLE001
        return "🧩 فهرستِ پچ در دسترس نیست."
    if not files:
        return "🧩 پچی منتظرِ رأی نیست."
    out = [f"🧩 <b>پچِ منتظرِ رأی</b> — {_fa(len(files))}"]
    for f in files[:cap]:
        try:
            d = json.loads(f.read_text("utf-8"))
        except Exception:  # noqa: BLE001
            continue
        out.append(f"· <code>{d.get('id')}</code> → {str(d.get('target'))[:50]}\n"
                   f"   {str(d.get('intent') or '')[:70]}")
    out.append("")
    out.append("رأی از همان کارتی که فرستاده شد — این‌جا فقط نماست.")
    return "\n".join(out)


# ── تشخیصِ «بساز» در متنِ آزاد ──────────────────────────────────────────────
_BUILD = ("بساز:", "بساز ", "کد بزن", "خودت را بساز", "اصلاح کن:", "/build")


def is_build_request(text: str) -> bool:
    t = str(text or "").strip()
    return any(t.startswith(p) or t.lower().startswith(p) for p in _BUILD)


def strip_prefix(text: str) -> str:
    t = str(text or "").strip()
    for p in _BUILD:
        if t.startswith(p) or t.lower().startswith(p):
            return t[len(p):].strip(" :،") or t
    return t
