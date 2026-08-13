"""bayes.py — belief update (ADR-039 C4، Plane-4).

دو مسیرِ صادقانه برای به‌روزرسانیِ باور — هر دو خروجی‌شان belief_delta_log_odds است
که GateDecision می‌پذیرد:

  ۱. Bayesian (likelihood معلوم): log-odds update با clip از policy.belief_update.
     P(H|E) = P(E|H)P(H) / [P(E|H)P(H) + P(E|¬H)(1-P(H))]  ⇒  Δlog-odds = log(BF)
  ۲. Score-band (evidence مبهم/زبانی): posterior **تا review تغییر نمی‌کند**.
     invariantِ بازبینیِ Hypothesis-Ledger: «عددِ زبانی = احتمالِ کالیبره‌شده نیست»،
     پس evidence‌ای که likelihood معلوم ندارد، باور را هم نمی‌تواند جابجا کند.

هیچ I/O، هیچ network، هیچ side-effect. خروجی همیشه در کرانِ [-clip, +clip] است و
GateDecision belief_delta_log_odds ∈ [-20, 20] را قبلاً در schema محدود کرده.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class BeliefDelta:
    """خروجیِ یک belief-update.

    method: "bayesian" (likelihood معلوم) | "score_band" (evidence مبهم، delta=0).
    invariant #8 (prior != posterior): همیشه delta ثبت می‌شود، حتی اگر صفر باشد."""
    log_odds_delta: float
    method: str
    note: str = ""

    def clipped_to(self, lo: float, hi: float) -> "BeliefDelta":
        v = max(lo, min(hi, self.log_odds_delta))
        if v == self.log_odds_delta:
            return self
        return BeliefDelta(v, self.method, self.note + " [clipped]")


def _prior_to_log_odds(prior: float) -> float:
    """prior ∈ (0,1) → log-odds ∈ ℝ. جزمیِ ۰/۱ ممنون است (schemas قبلاً enforces)."""
    if not (0.0 < prior < 1.0):
        raise ValueError(f"prior must be in (0,1); got {prior}")
    return math.log(prior / (1.0 - prior))


def update_bayesian(
    *,
    prior: float,
    p_e_given_h: float,
    p_e_given_not_h: float,
    clip_log_odds: float = 6.0,
) -> BeliefDelta:
    """به‌روزرسانیِ log-odds با Bayes factor.

    Δlog-odds = log( P(E|H) / P(E|¬H) ). خروجی در [-clip, +clip]. نکتهٔ مهم:
    این فقط زمانی صدا زده شود که likelihood واقعاً معلوم است (آزمونِ sandbox با
    metricِ کمی). برای evidence زبانی/مبهم از update_score_band استفاده کن.
    """
    if not (0.0 < p_e_given_h <= 1.0):
        raise ValueError(f"p_e_given_h must be in (0,1]; got {p_e_given_h}")
    if not (0.0 < p_e_given_not_h <= 1.0):
        raise ValueError(f"p_e_given_not_h must be in (0,1]; got {p_e_given_not_h}")
    prior_lo = _prior_to_log_odds(prior)
    log_bf = math.log(p_e_given_h) - math.log(p_e_given_not_h)
    raw = prior_lo + log_bf
    clipped = max(prior_lo - clip_log_odds, min(prior_lo + clip_log_odds, raw))
    delta = clipped - prior_lo
    return BeliefDelta(delta, "bayesian")


def update_score_band(
    *,
    support_direction: str,
    strength: str,
    clip_log_odds: float = 6.0,
) -> BeliefDelta:
    """evidence مبهم/زبانی → posterior تا review تغییر نمی‌کند (delta=0).

    بازبینیِ Hypothesis-Ledger: یک confidence-looking number که از تخمینِ زبانیِ
    مدل آمده، احتمالِ کالیبره‌شده نیست؛ پس نمی‌تواند باور را جابجا کند. evidence
    ثبت می‌شود (score band) ولی belief_delta صفر است — invariant #8/#9 حفظ می‌شود.
    """
    direction = str(support_direction or "").strip().lower()
    if direction not in ("supports", "contradicts", "ambiguous"):
        raise ValueError(
            "support_direction must be supports|contradicts|ambiguous; "
            f"got {support_direction!r}"
        )
    # delta = 0 عمدی؛ فقط direction/strength برای ممیزی ثبت می‌شوند.
    return BeliefDelta(
        0.0, "score_band",
        note=f"{direction}/{strength} — posterior unchanged pending review",
    ).clipped_to(-clip_log_odds, clip_log_odds)


def posterior_from_delta(prior: float, delta: BeliefDelta) -> float:
    """Δ → posterior ∈ (0,1) (برای گزارش/ممیزی؛ GateDecision از delta استفاده می‌کند)."""
    prior_lo = _prior_to_log_odds(prior)
    post_lo = prior_lo + delta.log_odds_delta
    # sigmoid
    return 1.0 / (1.0 + math.exp(-post_lo))


def aggregate_independent(
    deltas: list,
    *,
    clip_log_odds: float = 6.0,
    lambda_disagreement: float = 0.5,
) -> BeliefDelta:
    """تجمعِ چند-shardِ مستقل (C4 multi-agent). جمعِ log-odds با جریمهٔ disagreement.

    اگر shardها جهتِ متضاد دارند (مجموعهٔ علامت‌ها مخلوط)، lambda_disagreement
    شدتِ مطلق را کم می‌کند تا اجماعِ کاذب نسازد (invariant #6 generated!=sourced:
    چند رأیِ زبانی هم‌جهت ≠ شواهدِ مستقل)."""
    if not deltas:
        return BeliefDelta(0.0, "bayesian", "no-evidence (delta=0)")
    total = sum(d.log_odds_delta for d in deltas)
    # جریمهٔ disagreement: اگر نشانه‌های متضاد هست، جمع را به صفر نزدیک کن.
    signs = [1 if d.log_odds_delta > 0 else (-1 if d.log_odds_delta < 0 else 0)
             for d in deltas]
    n_pos = sum(1 for s in signs if s > 0)
    n_neg = sum(1 for s in signs if s < 0)
    if n_pos > 0 and n_neg > 0:
        disagreement = min(n_pos, n_neg) / max(n_pos, n_neg)
        total = total * (1.0 - lambda_disagreement * disagreement)
    return BeliefDelta(total, "bayesian", f"aggregate n={len(deltas)}").clipped_to(
        -clip_log_odds, clip_log_odds)
