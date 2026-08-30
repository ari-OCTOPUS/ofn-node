"""
core/scores.py — Four operational scores from the SOG generalization.

These scores translate the theoretical SOG concepts into measurable
quantities for any agent system (not just the linear-Gaussian model):

    SMS  (Self-Model Score)        = L_blind - L_informed
    SLS  (Shadow Leakage Score)    = L_null  - L_blind
    PCAI (Private-Channel Adv Idx) = (L_b - L_i) / (L_0 - L_i + ε)
    MSC  (Mode-Stability Control)  = 1 - V_anchored / V_baseline

In the SOG model, these specialize to:
    SMS = Δ_self = ½log(S_b/S)
    SLS = E_shadow = ½log(σ_z²/S_b)
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Optional

import numpy as np


@dataclass
class OperationalScores:
    """The four engineering scores from the SOG synthesis."""
    sms: float          # Self-Model Score: L_b - L_i (higher = private state matters more)
    sls: float          # Shadow Leakage Score: L_0 - L_b (higher = more inferrable)
    pcai: float         # Private-Channel Advantage Index (0..1)
    msc: Optional[float] = None  # Mode-Stability (needs variance data)

    def summary(self) -> dict:
        return {
            "SMS (self-model gain)": round(self.sms, 6),
            "SLS (shadow leakage)":  round(self.sls, 6),
            "PCAI (private advantage)": round(self.pcai, 4),
            "MSC (mode stability)":  round(self.msc, 4) if self.msc is not None else None,
        }

    def interpret(self) -> str:
        """Human-readable interpretation of the scores."""
        parts = []
        if self.sms > 0.05:
            parts.append("دسترسی به private state ارزش بالایی دارد (SMS>0.05)")
        elif self.sms < 0.01:
            parts.append("private state کمکی نمی‌کند (SMS≈0) — reflection بی‌فایده است")

        if self.sls > 0.05:
            parts.append("حالت پنهان به‌راحتی قابل‌استنتاج است (SLS>0.05) — خوب برای monitoring، بد برای privacy")
        elif self.sls < 0.005:
            parts.append("shadow ضعیف است — monitoring سخت، privacy بالا")

        if self.pcai > 0.7:
            parts.append(f"اکثرِ اطلاعاتِ مفید خصوصی است (PCAI={self.pcai:.2f})")
        elif self.pcai < 0.3:
            parts.append(f"اکثرِ اطلاعات قابل‌مشاهده است (PCAI={self.pcai:.2f})")

        if self.msc is not None:
            if self.msc > 0.3:
                parts.append(f"anchors به‌طور قابل‌توجهی واریانس را کاهش داد ({self.msc:.0%})")
            elif self.msc < 0.05:
                parts.append("anchors تأثیر قابل‌توجهی نداشتند")

        return "؛ ".join(parts) if parts else "امتیازها خنثی هستند"


def compute_scores_from_losses(L_null: float, L_blind: float, L_informed: float,
                                eps: float = 1e-10) -> OperationalScores:
    """
    Compute SMS, SLS, PCAI from three loss values.

    Args:
        L_null:     loss of the null/baseline observer (sees only marginal stats)
        L_blind:    loss of the blind observer (sees public trace Y)
        L_informed: loss of the informed observer (sees Y + private state D, M)

    Returns:
        OperationalScores with SMS, SLS, PCAI
    """
    sms = L_blind - L_informed
    sls = L_null - L_blind

    total_gain = L_null - L_informed + eps
    pcai = sms / total_gain if total_gain > 0 else 0.0
    pcai = max(0.0, min(1.0, pcai))  # clamp to [0, 1]

    return OperationalScores(sms=sms, sls=sls, pcai=pcai)


def compute_scores_from_model(rho=0.5, lam=0.5, se=0.1, sz=0.05, sd=0.1
                              ) -> OperationalScores:
    """
    Compute the four scores directly from the SOG model parameters.

    In the model:
        L_null  ← σ_z² (marginal variance)
        L_blind ← S_b (blind innovation variance)
        L_informed ← S (informed innovation variance)

    These are differential entropies, so the log-loss difference is:
        L_a - L_b = ½·log(var_a / var_b)
    """
    from .model import solve_from_stds

    sol = solve_from_stds(rho=rho, lam=lam, se=se, sz=sz, sd=sd)

    # Convert variances to "loss" (entropy rate)
    # L = ½·log(2πe·var), so L_a - L_b = ½·log(var_a/var_b)
    # گاردِ لبه: پارامترهای منحط (مثلاً se=0, lam=0) واریانس صفر می‌سازند و
    # math.log(0) با ValueError بی‌پیام می‌ترکید؛ کف می‌گذاریم تا تابع total بماند.
    _MIN_VAR = 1e-12
    L_null = 0.5 * math.log(2 * math.pi * math.e * max(sol.sigma_z2, _MIN_VAR))
    L_blind = 0.5 * math.log(2 * math.pi * math.e * max(sol.Sb, _MIN_VAR))
    L_informed = 0.5 * math.log(2 * math.pi * math.e * max(sol.S, _MIN_VAR))

    return compute_scores_from_losses(L_null, L_blind, L_informed)


def compute_msc(baseline_outputs: list, anchored_outputs: list) -> float:
    """
    Compute Mode-Stability Controllability score.

    MSC = 1 - V_anchored / V_baseline

    Args:
        baseline_outputs: list of outputs WITHOUT anchors (high variance expected)
        anchored_outputs:  list of outputs WITH anchors (low variance expected)

    Returns:
        MSC score (can be negative if anchors INCREASE variance)
    """
    v0 = float(np.var(baseline_outputs)) if len(baseline_outputs) > 1 else 0.0
    va = float(np.var(anchored_outputs)) if len(anchored_outputs) > 1 else 0.0

    if v0 < 1e-15:
        return 0.0
    return 1.0 - (va / v0)


# ════════════════════════════════════════════════════════════════════════
#  Decision helpers — from the "Decision Memo" section
# ════════════════════════════════════════════════════════════════════════

def should_use_reflection(scores: OperationalScores, cost_threshold: float = 0.02) -> bool:
    """
    Delta-Self Reflection Gate: should we allow another reflection pass?

    Reflection is worth it only if SMS exceeds the cost threshold.
    """
    return scores.sms > cost_threshold


def should_route_by_shadow(scores: OperationalScores, threshold: float = 0.3) -> bool:
    """
    Shadow-Guided Orchestrator: can we route from public summaries only?

    Yes if SLS is high enough that the shadow carries useful signal.
    """
    # Normalize SLS against the total information
    return scores.sls > threshold * (scores.sms + scores.sls)


def should_use_mas(scores: OperationalScores, coordination_cost: float = 0.01) -> bool:
    """
    The production rule from the synthesis:

    Use MAS only if: Δquality > coordination_cost + verification_cost + latency_cost

    Simplified: use MAS if total gain (SMS + SLS) exceeds coordination cost.
    """
    total_gain = scores.sms + scores.sls
    return total_gain > coordination_cost


if __name__ == "__main__":
    print("=== Operational Scores (canonical point) ===\n")

    scores = compute_scores_from_model()
    print(f"SMS (Δ_self):  {scores.sms:.6f}")
    print(f"SLS (E_shadow): {scores.sls:.6f}")
    print(f"PCAI:          {scores.pcai:.4f}")
    print(f"\nInterpretation: {scores.interpret()}")

    print(f"\nDecision helpers:")
    print(f"  Should reflect?    {should_use_reflection(scores)}")
    print(f"  Route by shadow?  {should_route_by_shadow(scores)}")
    print(f"  Use MAS?          {should_use_mas(scores)}")

    # MSC test
    rng = np.random.default_rng(42)
    baseline = rng.normal(0, 1, 100).tolist()
    anchored = rng.normal(0, 0.3, 100).tolist()
    msc = compute_msc(baseline, anchored)
    print(f"\nMSC test: {msc:.4f} (expect ~0.91 for 70% variance reduction)")
