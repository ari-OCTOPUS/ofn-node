#!/usr/bin/env python3
"""reflex.py — NI-2: ReflexArc (رفلکسِ محافظ). throttle داخلی، نه effect.

پاسخِ خودکار به خطر: σ>1→throttle · budget>80%→slow · freeze→pause.
هیچ‌کدام settle/publish/pay نمی‌کنند.
"""
from __future__ import annotations
from dataclasses import dataclass


@dataclass
class ReflexAction:
    """یک رفلکسِ فعال. throttle داخلی — هیچ اثرِ بیرونی."""
    name: str
    triggered: bool
    action: str       # throttle/slow/pause/alarm
    severity: str     # low/medium/high/critical
    detail: str = ""
    is_effect: bool = False   # همیشه False


class ReflexArc:
    """ارزیابی snapshot → رفلکس‌های محافظ. throttle فقط."""

    def evaluate(self, snap: dict) -> list[ReflexAction]:
        s = snap or {}
        rhythm = s.get("rhythm", {})
        spectral = s.get("spectral", {})
        budget = s.get("budget", {})
        sensory = s.get("sensory", {})
        pain = s.get("pain_level", 0.0)
        actions = []

        sigma = spectral.get("sigma", 0)
        if sigma > 1.0:
            actions.append(ReflexAction("sigma-throttle", True,
                "throttle", "critical", f"σ={sigma}>1 → doctor critical-only"))

        spent_pct = budget.get("pct", 0)
        if spent_pct > 0.8:
            actions.append(ReflexAction("budget-slow", True,
                "slow", "high", f"budget {spent_pct*100:.0f}% → acquisition slow"))

        afferent = sensory.get("afferent_ratio", 1.0)
        if afferent < 0.1:
            actions.append(ReflexAction("disconnect-alarm", True,
                "alarm", "high", "afferent<0.1 → dreaming"))

        mode = rhythm.get("mode_color", "GREEN")
        if mode == "RED":
            actions.append(ReflexAction("red-pause", True,
                "pause", "high", "RED → non-essential pause"))

        if pain > 0.7:
            actions.append(ReflexAction("pain-protect", True,
                "pause", "critical", f"pain={pain:.2f} → protective redirect"))

        if not actions:
            actions.append(ReflexAction("all-clear", False, "none", "low", "no reflex needed"))

        return actions
