#!/usr/bin/env python3
"""neural_driver.py — Neural↔Brain↔Studio wiring.

اسنپ‌شات Neural، ThinkingBrain را feed می‌کند: pain→risk، circadian→schedule،
afferent→confidence، sigma→throttle. هرگز effect.
"""
from __future__ import annotations
import os
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE))

# ── WS-2 (۲۰۲۶-۰۸-۰۱): فلگِ رؤیت‌پذیریِ تفکیکِ درد ──────────────────────────────
# چرا env مستقیم و نه `wiring.flag`: `wiring` خودش `neural_driver` را import می‌کند
# (wiring.py:1409) — importِ معکوس حلقه می‌سازد. معناشناسی **دقیقاً** همان
# `wiring.flag` است (`os.environ.get(name, "0") == "1"`).
# ⚠️ این نام عمداً در `wiring.PAPER_FULL_FLAGS` نیست، پس `apply_profile` آن را
# روشن نمی‌کند: غیاب = خاموش. (برای این نام، برخلافِ خانوادهٔ OCTOPUS_WIRE_*.)
PAIN_BREAKDOWN_FLAG = "OCTOPUS_PAIN_BREAKDOWN"


def breakdown_enabled() -> bool:
    """فلگِ تفکیکِ درد. پیش‌فرض خاموش → خروجی بایت‌به‌بایتِ امروز."""
    return os.environ.get(PAIN_BREAKDOWN_FLAG, "0") == "1"


class NeuralDriver:
    """از NeuralSnapshot، ورودی‌های ThinkingBrain را تنظیم کن.
    این bridge است — نه effect."""

    def __init__(self):
        from signal_hub import SignalHub
        from reflex import ReflexArc
        from nociceptor import Nociceptor
        self.hub = SignalHub()
        self.reflex = ReflexArc()
        self.nociceptor = Nociceptor()

    def snapshot_to_brain_inputs(self, snap: dict) -> dict:
        """تبدیل snapshot → ورودی‌های ThinkingBrain.
        خروجی: {partner_stress, confidence_adjustment, schedule_hint, throttle}.
        همه advisory."""
        pain = snap.get("pain_level", 0.0)
        rhythm = snap.get("rhythm", {})
        spectral = snap.get("spectral", {})
        sensory = snap.get("sensory", {})
        budget = snap.get("budget", {})

        # pain → partner_stress proxy (اگر pain بالا، stress بالا)
        partner_stress = min(1.0, pain * 0.8)

        # circadian readiness → confidence
        readiness = rhythm.get("readiness", 0.7)
        confidence_adj = readiness * 0.3

        # sigma → throttle
        sigma = spectral.get("sigma", 0)
        throttle = sigma > 0.9

        # afferent → learning confidence
        afferent = sensory.get("afferent_ratio", 1.0)
        data_confidence = min(1.0, afferent * 0.5)

        # budget → risk
        budget_pct = budget.get("pct", 0)

        return {
            "partner_stress": round(partner_stress, 2),
            "confidence_adjustment": round(confidence_adj, 2),
            "schedule_hint": rhythm.get("mode_focus", "STEADY"),
            "throttle_brain": throttle,
            "data_confidence": round(data_confidence, 2),
            "budget_pct": budget_pct,
            "advisory_only": True,
        }

    def evaluate(self, beat: int = 0, rhythm=None, sensory=None,
                 spectral=None, budget=None, bcm=None, hebbian=None) -> dict:
        """دورِ کامل: collect snapshot → reflex → brain inputs.

        FIX #310 (2026-07-28): پارامترهای اختیاری bcm/hebbian — برای اولین‌بار،
        وزن‌های آموخته‌شده را در خروجی fold می‌کنیم (`learned_pressure`).
        تا امروز کلِ لایهٔ عصبی advisory-only بود و `protective_override` فقط از
        thresholdهای ثابت (nociceptor/reflex) می‌خواند. باbcm/hebbian، shadow path
        می‌تواند ثبت کند که یادگیری *می‌گفت* چه — گامِ اولِ بستنِ حلقه.
        bcm=None یا hebbian=None → learned_pressure=0 (صفر تغییرِ رفتار، backward compat).
        اعمالِ واقعی پشت flag جداگانه (OCTOPUS_NEURAL_LEARNED_APPLY، default-off).
        """
        # nociceptor — P3 (truth-map 2026-07-17): error_rate و partner_stress دیگر drop
        # نمی‌شوند؛ قبلاً ۲ از ۶ ورودیِ درد هرگز به measure نمی‌رسید و pain ساختاراً کور بود.
        _sens = sensory or {}

        def _unit(v, default):
            """clamp امنِ 0..1 — NaN/inf/غیرعدد → default (NaN هر مقایسه را fail می‌کند)."""
            try:
                f = float(v)
            except (TypeError, ValueError):
                return default
            return f if 0.0 <= f <= 1.0 else (1.0 if f > 1.0 and f != float("inf") else default)

        # WS-2: با فلگ خاموش، `breakdown=False` و مسیر بایت‌به‌بایتِ قبل است.
        _breakdown = breakdown_enabled()
        pain = self.nociceptor.measure(
            budget_pct=budget.get("pct", 0) if budget else 0,
            error_rate=_unit(_sens.get("error_rate", 0.0), 0.0),
            freeze_active=rhythm.get("mode_color") == "RED" if rhythm else False,
            partner_stress=_unit(_sens.get("partner_stress", 0.0), 0.0),
            afferent_ratio=_unit(_sens.get("afferent_ratio", 1.0), 1.0),
            sigma=spectral.get("sigma", 0) if spectral else 0,
            breakdown=_breakdown,
        )
        snap = self.hub.collect(
            beat=beat, rhythm=rhythm or {}, sensory=sensory or {},
            spectral=spectral or {}, budget=budget or {},
            pain_level=pain.pain_level)
        reflexes = self.reflex.evaluate(snap.to_dict())
        brain_inputs = self.snapshot_to_brain_inputs(snap.to_dict())

        # FIX #310 (2026-07-28): برای اولین‌بار، وزن‌های آموخته‌شده را fold کن.
        # learned_pressure = نرمال‌شدهٔ میانگینِ وزنِ ۳ کلیدِ برترِ BCM.
        # اگر bcm مفقود/خالی → 0.0 (backward compat: هیچ تغییری در رفتار).
        # این مقدار shadow log می‌شه (OCTOPUS_NEURAL_EFFECT_SHADOW) و اعمالش پشت
        # flag جداگانه‌ست (OCTOPUS_NEURAL_LEARNED_APPLY، default-off).
        learned_pressure = 0.0
        learned_top_signal = ""
        learned_n_keys = 0
        if bcm is not None:
            try:
                _keys = bcm.keys() if hasattr(bcm, "keys") else []
                learned_n_keys = len(_keys)
                if _keys:
                    _weighted = [(k, bcm.weight(k) or 0.0) for k in _keys]
                    _top = sorted(_weighted, key=lambda kv: kv[1], reverse=True)[:3]
                    _sum_top = sum(w for _, w in _top)
                    # نرمال‌سازی: w_cap=4.0 (پیش‌فرض BCM)، ۳ کلید → max=12.0
                    learned_pressure = min(1.0, _sum_top / 12.0)
                    learned_top_signal = _top[0][0] if _top else ""
            except Exception:  # noqa: BLE001 — یادگیری هرگز evaluate را نمی‌کشد
                pass
        brain_inputs["learned_pressure"] = round(learned_pressure, 3)
        brain_inputs["learned_top_signal"] = learned_top_signal
        brain_inputs["learned_n_keys"] = learned_n_keys

        # WS-2 (۲۰۲۶-۰۸-۰۱): تا امروز این dict فقط اسکالرِ fuse‌شده را بیرون می‌داد و
        # `contributors` را دور می‌ریخت — به همین دلیل `effect-shadow.jsonl` هیچ‌وقت
        # نمی‌گفت درد **از کدام ورودی** آمده، و کشفِ «۵ از ۶ صفرند» فقط با بازسازیِ
        # آفلاینِ ۸۵۱۱ ردیف ممکن شد. با فلگ روشن، تفکیک هم بیرون می‌آید.
        # کلیدهای level/protective دست‌نخورده‌اند → `wiring.protective_override`
        # (که فقط `pain.level` را می‌خواند، wiring.py:1659) بی‌اثر می‌ماند.
        _pain_out = {"level": pain.pain_level, "protective": pain.protective_mode}
        if _breakdown and pain.contributions is not None:
            _pain_out["contributions"] = pain.contributions
            _pain_out["zero_terms"] = list(pain.zero_terms)

        return {
            "snapshot": snap.to_dict(),
            "pain": _pain_out,
            "reflexes": [{"name": r.name, "triggered": r.triggered,
                          "action": r.action} for r in reflexes],
            "brain_inputs": brain_inputs,
        }
