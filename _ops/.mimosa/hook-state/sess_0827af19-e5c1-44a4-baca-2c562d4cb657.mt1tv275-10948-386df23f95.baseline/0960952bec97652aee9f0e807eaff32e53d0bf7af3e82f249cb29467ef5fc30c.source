#!/usr/bin/env python3
"""fuel_meter.py — HH-fuel: مترِ «سوختِ زندگی»ِ قلب = مصرفِ واقعیِ API/Ollama.

رأی مالک 2026-07-19 (جداسازیِ دو پول): «پولِ قلب» = مقداری که اختاپوس از APIهایش
(Ollama محلی + پولی) مصرف می‌کند تا زنده بماند — جدا از «پولِ واقعیِ حساب» که کارِ
پای حسابداری است. این ماژول تنها گذرگاهِ ثبتِ هر call واقعیِ LLM در استریمِ سوختِ قلب است
(همان «trace-log واحد»ی که improve.py می‌خواست).

خطوط قرمز: stdlib-only · فقط state/pulse/fuel-stream.jsonl را می‌نویسد · kill-switch اول ·
flag خاموش = no-op مطلق (بایت‌به‌بایت) · هرگز prompt/محتوا ثبت نمی‌شود (فقط متادیتای مصرف).
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE.parent / "budget"))
import opslib  # noqa: E402

STREAM_PATH = opslib.STATE_DIR / "pulse" / "fuel-stream.jsonl"


def enabled() -> bool:
    """flagِ سیم‌کشی. خاموش (پیش‌فرض) = no-op مطلق."""
    return os.environ.get("OCTOPUS_WIRE_HEART_FUEL") == "1"


def record(tier: str, model: str = "", cost_usd: float = 0.0,
           ms: int = 0, ok: bool = True) -> dict | None:
    """یک call واقعیِ LLM (سوختِ مصرف‌شده) را ثبت کن. خروجی: رکورد یا None.
    هرگز محتوا/prompt ثبت نمی‌شود — فقط tier/model/هزینه/latency."""
    if opslib.STOP_ORGANISM.exists() or opslib.halted():
        return None
    if not enabled():
        return None
    try:
        rec = {"ts": opslib.now_iso(), "tier": str(tier)[:16],
               "model": str(model)[:48],
               "cost_musd": opslib.micro(float(cost_usd or 0.0)),
               "ms": int(ms or 0), "ok": bool(ok)}
        opslib.append_jsonl(STREAM_PATH, rec)
        return rec
    except Exception:  # noqa: BLE001 — مترِ سوخت هرگز مسیرِ مغز را نکشد
        return None


if __name__ == "__main__":
    import json
    # عمداً flag را setdefault نمی‌کنیم: اجرای مستقیمِ این فایل روی درختِ زنده نباید
    # سوختِ ساختگی در استریمِ زنده بنویسد. برای دمو، خودت OCTOPUS_WIRE_HEART_FUEL=1 بگذار.
    print(json.dumps({
        "enabled": enabled(),
        "local": record("local", "qwen2.5:latest", cost_usd=0.0, ms=800, ok=True),
        "paid": record("primary", "fugu", cost_usd=0.012, ms=2200, ok=True),
    }, ensure_ascii=False, indent=2))
