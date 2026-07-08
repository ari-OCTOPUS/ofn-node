#!/usr/bin/env python3
"""nociceptor.py — NI-5: Nociceptor (دردسنج).

pain = f(budget_trajectory, error_rate, freeze_count, partner_stress, afferent, σ).
pain>0.7 → protective redirect. محافظ، نه هدف. λ_persist<0.
"""
from __future__ import annotations
from dataclasses import dataclass


@dataclass
class PainSignal:
    """خروجیِ nociceptor."""
    pain_level: float        # 0=سالم، 1=بحرانی
    contributors: dict       # {factor: contribution}
    protective_mode: bool    # pain>0.7
    detail: str = ""


class Nociceptor:
    """دردسنج. pain محافظ است، هرگز reward/objective. λ_persist<0."""

    LAMBDA_PERSIST = -1.0

    def measure(self, budget_pct: float = 0.0,
                error_rate: float = 0.0,
                freeze_active: bool = False,
                partner_stress: float = 0.0,
                afferent_ratio: float = 1.0,
                sigma: float = 0.0) -> PainSignal:
        """محاسبهٔ pain. همهٔ ورودی‌ها 0..1 (budget_pct هم 0..1)."""
        contributors = {}
        pain = 0.0

        # budget exhaustion
        bp = max(0, budget_pct - 0.8) * 3
        contributors["budget"] = min(1.0, bp)
        pain += bp * 0.3

        # error rate
        contributors["errors"] = min(1.0, error_rate)
        pain += error_rate * 0.25

        # freeze
        if freeze_active:
            contributors["freeze"] = 1.0
            pain += 0.4

        # partner stress
        contributors["partner_stress"] = partner_stress
        pain += partner_stress * 0.15

        # afferent deficit
        deficit = max(0, 0.2 - afferent_ratio) * 3
        contributors["afferent_deficit"] = min(1.0, deficit)
        pain += deficit * 0.1

        # sigma proximity to cancer
        if sigma > 0.8:
            sig_pain = (sigma - 0.8) * 5
            contributors["sigma"] = min(1.0, sig_pain)
            pain += sig_pain * 0.2

        pain = min(1.0, pain)
        protective = pain > 0.7

        detail = "protective redirect" if protective else ("warning" if pain > 0.4 else "healthy")
        return PainSignal(pain_level=round(pain, 3), contributors=contributors,
                          protective_mode=protective, detail=detail)
