#!/usr/bin/env python3
"""cognition_effect.py — HH-artery: پلِ صادقِ «شناختِ LLM → effectِ قابل‌شمارشِ قلب».

مسئله (رأی مالک 2026-07-19 «جریانِ واقعیِ پول/شناخت وارد قلب نمی‌شود؛ استعاره→کد»):
قلب فقط confirmed(پول) و effects(effector-gate) را می‌شمارد؛ خروجیِ مغز (Ollama/API)
به هیچ‌کدام سیم نبود، پس ضربان از beats(متروْنوم) پر می‌شد و ارزشِ واقعی=۰ پنهان می‌ماند.

این ماژول تنها گذرگاهِ ثبتِ «effectِ شناختی» است: آرتیفکتِ تولیدِ مغز فقط وقتی ثبت می‌شود
که **بیرونی تأیید شده باشد** (validator=owner/…)، هرگز خودسنجی (self/llm). این نامتغیرِ
external-validation-only همان ضدِّ «توهمِ ارزش» است — خونِ قلابیِ تازه نمی‌سازیم.

خطوطِ قرمز: stdlib-only · $0 · فقط استریمِ اختصاصیِ خودش (pulse/cognition-effects.jsonl)
را می‌نویسد — هرگز ledger پول/ژنوم را لمس نمی‌کند · kill-switch اول · flag خاموش = no-op مطلق.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE.parent / "budget"))
import opslib  # noqa: E402

STREAM_PATH = opslib.STATE_DIR / "pulse" / "cognition-effects.jsonl"

# validatorهای بیرونیِ مجاز — خودسنجی ساختاراً رد می‌شود (نامتغیرِ ضدِّ توهمِ ارزش).
_EXTERNAL_VALIDATORS = frozenset({"owner", "reconcile", "effector-gate", "human"})
_SELF_VALIDATORS = frozenset({"", "self", "llm", "model", "brain", "cortex", "agent"})
# ردهٔ وزنیِ آرتیفکت (فقط برچسب؛ وزنِ عددی در producers.velocity_meter اعمال می‌شود).
_WEIGHT_CLASSES = frozenset({"draft", "review", "decision", "money"})


def enabled() -> bool:
    """flagِ سیم‌کشی. خاموش (پیش‌فرض) = no-op مطلق، بایت‌به‌بایت رفتارِ امروز."""
    return os.environ.get("OCTOPUS_WIRE_COGNITION_EFFECT") == "1"


def record(leg: str, artifact_id: str, validator: str = "owner",
           weight_class: str = "review", note: str = "") -> dict | None:
    """یک effectِ شناختیِ بیرونی-تأییدشده را در استریمِ قلب ثبت کن.

    خروجی: رکوردِ ثبت‌شده، یا None (kill-switch / flag خاموش / خودسنجیِ ردشده / خطا).
    این تابع هرگز خرج/انتشار نمی‌کند و هرگز ledger پول را لمس نمی‌کند."""
    if opslib.STOP_ORGANISM.exists() or opslib.halted():
        return None
    if not enabled():
        return None
    v = (validator or "").strip().lower()
    if v in _SELF_VALIDATORS or v not in _EXTERNAL_VALIDATORS:
        # نامتغیرِ کلیدی: بدونِ تأییدِ بیرونی هیچ effectی شمرده نمی‌شود (ضدِّ خونِ قلابی).
        try:
            opslib.alert([f"cognition_effect: validatorِ نامعتبر «{validator}» رد شد "
                          f"(leg={leg}, artifact={artifact_id}) — external-validation-only"])
        except Exception:  # noqa: BLE001
            pass
        return None
    rec = {
        "ts": opslib.now_iso(),
        "leg": str(leg)[:64],
        "artifact_id": str(artifact_id)[:96],
        "validator": v,
        "weight_class": weight_class if weight_class in _WEIGHT_CLASSES else "review",
        "note": str(note)[:200],
        "provenance": "external-validated cognition effect (heart artery)",
    }
    try:
        opslib.append_jsonl(STREAM_PATH, rec)
    except Exception as e:  # noqa: BLE001 — مشاهده fail-soft است
        try:
            opslib.alert([f"cognition_effect append failed: {type(e).__name__}: {e}"])
        except Exception:  # noqa: BLE001
            pass
        return None
    return rec


if __name__ == "__main__":
    import json
    # عمداً flag را setdefault نمی‌کنیم: اجرای مستقیمِ این فایل روی درختِ زنده نباید
    # رکوردِ ساختگیِ validator=owner در استریمِ زنده بنویسد. برای دموِ محلی، پیش از اجرا
    # خودت OCTOPUS_WIRE_COGNITION_EFFECT=1 بگذار (و ترجیحاً STATE_DIR را به tmp ببر).
    print(json.dumps({
        "enabled": enabled(),
        "self_rejected(llm)": record("demo", "a1", validator="llm"),
        "owner_ok": record("owner-approval", "job-123", validator="owner", weight_class="review"),
    }, ensure_ascii=False, indent=2))
