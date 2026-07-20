#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""fence_adapter.py — درِ مشترکِ غربالِ context-fence برای callerهای LLMِ خارج از model_router.

model_router.ask خودش fenced است (آیتم۲، test_context_fence_wiring). این آداپتر همان غربال
را — با همان فلگ و همان انضباطِ observe-only — به مسیرهای مستقیمِ provider می‌رساند
(debate_loop / heart.doctor_setpoint / governor.allocate_llm / fallbackِ chord.llm_adapter)
بدونِ ذره‌ای تغییر در provider semantics:

  - فلگ خاموش (پیش‌فرض، OCTOPUS_WIRE_CONTEXT_FENCE) → None و صفر کار — رفتارِ قدیم
    بایت‌به‌بایت.
  - فلگ روشن → فاز ۱ observe-only: هر بخشِ برچسب‌خورده screen می‌شود؛ یافته → یک alertِ
    redaction-safe (فقط caller-id ایستا + برچسبِ provenance + کدهای یافته — **هرگز متنِ
    خامِ prompt/PII/secret**)؛ هرگز بلاک نمی‌کند، هرگز prompt را تغییر نمی‌دهد.
  - provenance جدا می‌ماند (PROVENANCE_LABELS): owner (دستورِ مالک/سیستم — معتمد؛ معمولاً
    pass داده نمی‌شود) / external (دادهٔ بیرونی) / memory (بازیابی‌شده/state) /
    self_knowledge (**همیشه ADVISORY** — در نتیجه advisory=True مهر می‌خورد) /
    synthesis (خروجیِ LLM قبلی).
  - هر خطا (import/screen/alert) → None و مسیرِ LLM دست‌نخورده (§۴ fail-soft).

stdlib فقط؛ صفر شبکه؛ صفر mutation؛ صفر state.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent          # _ops/cortex

PROVENANCE_LABELS = ("owner", "external", "memory", "self_knowledge", "synthesis")
_SCRUB = re.compile(r"[^\w:.\-/@]")


def _scrub(v, n: int = 48) -> str:
    return _SCRUB.sub("_", str(v or "unknown"))[:n]


def screen_llm_input(caller: str, parts, alert_fn=None) -> dict | None:
    """غربالِ observe-onlyِ ورودیِ LLM در یک call-siteِ مستقیمِ provider.

    caller: شناسهٔ ایستای call-site (مثلاً "debate.muse-r1") — scrub می‌شود.
    parts:  iterable از (provenance_label, text) — یا یک str تنها (برچسبِ external).
    alert_fn: تزریق‌پذیر برای تست؛ پیش‌فرض opslib.alert (lazy).

    خروجی: فلگ خاموش یا هر خطا → None؛ روشن → {"caller","clean","flagged","parts"} —
    فقط برای مشاهده؛ صداکننده هرگز نباید بر اساسِ آن بلاک/تغییر بدهد (فاز ۱)."""
    try:
        if str(_HERE) not in sys.path:
            sys.path.insert(0, str(_HERE))
        import context_fence as _fence           # noqa: WPS433 — همسایهٔ همین ماژول
        if not _fence.enabled():
            return None
        if isinstance(parts, (str, bytes)):
            parts = [("external", parts)]
        results, flagged = [], []
        for item in (parts or []):
            if isinstance(item, (tuple, list)) and len(item) == 2:
                label, text = item
            else:
                label, text = "external", item
            label = _scrub(label, 24)
            sc = _fence.screen(str(text or ""))
            rec = {"provenance": label, "screen": sc}
            if label == "self_knowledge":
                rec["advisory"] = True           # self-knowledge هرگز authoritative نمی‌شود
            results.append(rec)
            if not sc.get("clean", True):
                flagged.append((label, sc.get("findings") or []))
        if flagged:
            _emit_alert(caller, flagged, alert_fn)
        return {"caller": _scrub(caller), "clean": not flagged,
                "flagged": len(flagged), "parts": results}
    except Exception:  # noqa: BLE001 — غربال هرگز مسیرِ LLM را نمی‌کشد
        return None


def _emit_alert(caller, flagged, alert_fn) -> None:
    """alertِ redaction-safe: فقط caller + برچسبِ provenance + کدهای یافته — هرگز متنِ خام."""
    try:
        if alert_fn is None:
            _bud = str(_HERE.parent / "budget")
            if _bud not in sys.path:
                sys.path.insert(0, _bud)
            import opslib                        # noqa: WPS433
            alert_fn = opslib.alert
        det = "؛ ".join(f"{lbl}: {sorted(set(codes))}" for lbl, codes in flagged)
        alert_fn([f"context_fence[{_scrub(caller)}]: ورودیِ مشکوک به prompt-injection — {det}"])
    except Exception:  # noqa: BLE001 — alertِ شکسته نباید call را بکشد
        pass
