#!/usr/bin/env python3
"""neural_driver.py — Neural↔Brain↔Studio wiring.

اسنپ‌شات Neural، ThinkingBrain را feed می‌کند: pain→risk، circadian→schedule،
afferent→confidence، sigma→throttle. هرگز effect.
"""
from __future__ import annotations
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE))


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
                 spectral=None, budget=None) -> dict:
        """دورِ کامل: collect snapshot → reflex → brain inputs."""
        # nociceptor
        pain = self.nociceptor.measure(
            budget_pct=budget.get("pct", 0) if budget else 0,
            freeze_active=rhythm.get("mode_color") == "RED" if rhythm else False,
            afferent_ratio=sensory.get("afferent_ratio", 1.0) if sensory else 1.0,
            sigma=spectral.get("sigma", 0) if spectral else 0,
        )
        snap = self.hub.collect(
            beat=beat, rhythm=rhythm or {}, sensory=sensory or {},
            spectral=spectral or {}, budget=budget or {},
            pain_level=pain.pain_level)
        reflexes = self.reflex.evaluate(snap.to_dict())
        brain_inputs = self.snapshot_to_brain_inputs(snap.to_dict())
        return {
            "snapshot": snap.to_dict(),
            "pain": {"level": pain.pain_level, "protective": pain.protective_mode},
            "reflexes": [{"name": r.name, "triggered": r.triggered,
                          "action": r.action} for r in reflexes],
            "brain_inputs": brain_inputs,
        }
