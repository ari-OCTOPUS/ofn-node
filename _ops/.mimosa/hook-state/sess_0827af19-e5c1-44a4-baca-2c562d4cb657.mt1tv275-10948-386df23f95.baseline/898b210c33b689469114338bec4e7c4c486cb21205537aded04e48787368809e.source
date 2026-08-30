#!/usr/bin/env python3
"""Pure authority policy for heart-derived cadence.

A fresh file is not automatically authoritative. Closed production wire remains shadow. Shadow
cadence may be used only when explicitly allowed and is always labelled advisory.
"""
from __future__ import annotations


def decide(heart: dict, *, default_period_s: float = 120.0,
           multiplier: float = 2.0, allow_shadow: bool = False,
           min_s: float = 60.0, max_s: float = 600.0) -> dict:
    auth = str(heart.get("authority") or "MISSING")
    data = heart.get("data") or {}
    try:
        hp = float(data.get("period_s"))
        valid = hp > 0
    except (TypeError, ValueError):
        hp, valid = 0.0, False
    if auth == "AUTHORITATIVE" and heart.get("production_open") and valid:
        p = max(min_s, min(max_s, multiplier * hp))
        return {"period_s": p, "authority": "AUTHORITATIVE",
                "source": f"heart-production×{multiplier:g}", "blocked": False}
    if auth == "ADVISORY_SHADOW" and allow_shadow and valid:
        p = max(min_s, min(max_s, multiplier * hp))
        return {"period_s": p, "authority": "ADVISORY_SHADOW",
                "source": f"heart-shadow×{multiplier:g}", "blocked": False,
                "warning": "shadow cadence is not production authority"}
    return {"period_s": float(default_period_s), "authority": "DEFAULT",
            "source": "safe-default", "blocked": False,
            "warning": f"heart unavailable/not-authoritative:{auth}"}
