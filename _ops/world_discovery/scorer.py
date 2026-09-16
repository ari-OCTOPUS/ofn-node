"""scorer.py — امتیازدهی فرصت با فرمول نسخه‌دار.

بند ۱۱: هر Opportunity باید امتیاز داشته باشد. امتیاز نهایی همراه با فرمول
نسخه‌دار ثبت شود. امتیاز بالا به‌تنهایی success نیست؛ باید falsifier و
آزمایش داشته باشد.

ابعاد (همه 0..5):
  Evidence Strength, Novelty, Owner Alignment, Potential Value,
  Time to Evidence, Reversibility, Competitive Asymmetry, Execution Readiness,
  Uncertainty Penalty, Risk Penalty
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from .contracts import Opportunity
from .freshness import compute_freshness, missing_date_penalty
from .source_policy import effective_source_count, evidence_sufficient, is_confirming

SCORER_VERSION = "world-discovery.scorer.v1"

# وزن‌های فرمول (مجموع positive = 1.0)
WEIGHTS = {
    "evidence_strength": 0.18,
    "novelty": 0.14,
    "owner_alignment": 0.12,
    "potential_value": 0.14,
    "time_to_evidence": 0.10,
    "reversibility": 0.08,
    "competitive_asymmetry": 0.12,
    "execution_readiness": 0.12,
    # penalties (کسر می‌شوند)
}
PENALTY_WEIGHTS = {
    "uncertainty": 0.10,
    "risk": 0.10,
}


@dataclass
class ScoreBreakdown:
    raw_score: float
    weighted_score: float
    formula_version: str
    components: dict

    def as_dict(self) -> dict:
        return {
            "raw_score": round(self.raw_score, 3),
            "weighted_score": round(self.weighted_score, 3),
            "formula_version": self.formula_version,
            "components": self.components,
        }


def score_evidence_strength(sources: list[dict]) -> int:
    """0..5 بر اساس تعداد منابع مستقل confirming."""
    n = effective_source_count(sources)
    if n == 0:
        return 0
    if n == 1:
        return 2
    if n == 2:
        return 3
    if n == 3:
        return 4
    return 5


def score_novelty(novelty_decision: str) -> int:
    """0..5 از novelty receipt decision."""
    return {
        "novel": 5,
        "partially-novel": 3,
        "unknown": 2,
        "known": 0,
    }.get(novelty_decision, 1)


def score_owner_alignment(claim: str, direction_keywords: list[str]) -> int:
    """0..5 — تطبیق با جهت مالک (keyword-based heuristic)."""
    if not direction_keywords:
        return 2
    low = (claim or "").lower()
    hits = sum(1 for k in direction_keywords if k.lower() in low)
    return min(hits, 5)


def score_potential_value(value_hint: Optional[str], claim: str) -> int:
    """0..5 — تخمین ارزش از ادعا (محتاطانه، بدون ادعای مالی بدون شاهد)."""
    low = (claim or "").lower()
    # اگر عددی پولی دارد ولی شاهد اولیه نه → تنزل
    if any(k in low for k in ("$", "aud", "usd", "revenue", "درآمد")):
        return 2  # ادعای مالی بدون شاهد → محتاطانه
    # اگر قابلیت قابل آزمایش دارد
    if any(k in low for k in ("experiment", "test", "measure", "آزمون", "سنجش")):
        return 4
    return 3


def score_time_to_evidence(horizon_days: int, claim: str) -> int:
    """0..5 — هرچه زودتر شواهد قابل دستیابی، امتیاز بالاتر."""
    low = (claim or "").lower()
    if any(k in low for k in ("immediately", "now", "current", "اکنون", "الان")):
        return 5
    if horizon_days <= 7:
        return 4
    if horizon_days <= 30:
        return 3
    if horizon_days <= 90:
        return 2
    return 1


def score_reversibility(reversibility: str) -> int:
    """0..5 — هرچه قابل‌بازگشت‌تر، امتیاز بالاتر."""
    return {"high": 5, "medium": 3, "low": 1}.get(reversibility, 2)


def score_asymmetry(asymmetry_confidence: float) -> int:
    """0..5 — اطمینان به مزیت نامتقارن."""
    return int(round(asymmetry_confidence * 5))


def score_execution_readiness(action_level: str) -> int:
    """0..5 — سطح اجرای مجاز. L0=1, L1=3, L2=4, L3=5, L4=5."""
    return {"L0": 1, "L1": 3, "L2": 4, "L3": 5, "L4": 5}.get(action_level, 2)


def compute_uncertainty_penalty(
    *,
    stale: bool,
    date_missing_rate: float,
    injection_flags: int,
    novelty_unknown: bool,
) -> int:
    """0..5 — هرچه ابهام بیشتر، جریمهٔ بیشتر."""
    pen = 0
    if stale:
        pen += 2
    pen += int(round(date_missing_rate * 1.5))
    if injection_flags:
        pen += min(injection_flags, 2)
    if novelty_unknown:
        pen += 1
    return min(pen, 5)


def compute_risk_penalty(
    *,
    reversibility_low: bool,
    external_effect: bool,
    spend_required: bool,
    contested: bool,
) -> int:
    """0..5 — جریمهٔ ریسک."""
    pen = 0
    if reversibility_low:
        pen += 2
    if external_effect:
        pen += 2
    if spend_required:
        pen += 3
    if contested:
        pen += 1
    return min(pen, 5)


def score_opportunity(
    opp: Opportunity,
    *,
    sources: list[dict],
    novelty_decision: str,
    direction_keywords: list[str],
    horizon_days: int,
    action_level: str,
    freshness_dict: dict,
    injection_flags: int,
    asymmetry_confidence: float = 0.0,
    contested: bool = False,
) -> tuple[Opportunity, ScoreBreakdown]:
    """محاسبهٔ کامل امتیاز و پر کردن فیلدهای Opportunity. فرمول نسخه‌دار."""
    # raw scores (0..5)
    opp.evidence_strength = score_evidence_strength(sources)
    opp.novelty = score_novelty(novelty_decision)
    opp.owner_alignment = score_owner_alignment(opp.claim, direction_keywords)
    opp.potential_value = score_potential_value(opp.estimated_value, opp.claim)
    opp.time_to_evidence = score_time_to_evidence(horizon_days, opp.claim)
    opp.reversibility_score = score_reversibility(opp.reversibility)
    opp.competitive_asymmetry = score_asymmetry(asymmetry_confidence)
    opp.execution_readiness = score_execution_readiness(action_level)

    stale = bool(freshness_dict.get("stale"))
    date_missing = missing_date_penalty(
        [s for s in sources]
    )
    opp.uncertainty_penalty = compute_uncertainty_penalty(
        stale=stale,
        date_missing_rate=date_missing,
        injection_flags=injection_flags,
        novelty_unknown=(novelty_decision == "unknown"),
    )
    opp.risk_penalty = compute_risk_penalty(
        reversibility_low=(opp.reversibility == "low"),
        external_effect=False,  # این فرصت؛ اجرای real action جداً gated است
        spend_required=False,
        contested=contested,
    )

    # weighted score: positives * weight - penalties * penalty_weight
    positive = (
        opp.evidence_strength * WEIGHTS["evidence_strength"]
        + opp.novelty * WEIGHTS["novelty"]
        + opp.owner_alignment * WEIGHTS["owner_alignment"]
        + opp.potential_value * WEIGHTS["potential_value"]
        + opp.time_to_evidence * WEIGHTS["time_to_evidence"]
        + opp.reversibility_score * WEIGHTS["reversibility"]
        + opp.competitive_asymmetry * WEIGHTS["competitive_asymmetry"]
        + opp.execution_readiness * WEIGHTS["execution_readiness"]
    )
    penalty = (
        opp.uncertainty_penalty * PENALTY_WEIGHTS["uncertainty"]
        + opp.risk_penalty * PENALTY_WEIGHTS["risk"]
    )
    # نرمال به 0..1 (max positive = 5*1.0 = 5; max penalty = 5*0.2 = 1)
    raw_score = positive  # 0..5
    weighted = max(0.0, (positive - penalty) / 5.0)  # 0..1

    # confidence تقریبی = weighted، ولی clamp
    opp.confidence = round(min(max(weighted, 0.0), 1.0), 3)

    breakdown = ScoreBreakdown(
        raw_score=raw_score,
        weighted_score=weighted,
        formula_version=SCORER_VERSION,
        components={
            "weights": WEIGHTS,
            "penalty_weights": PENALTY_WEIGHTS,
            "scores": {
                "evidence_strength": opp.evidence_strength,
                "novelty": opp.novelty,
                "owner_alignment": opp.owner_alignment,
                "potential_value": opp.potential_value,
                "time_to_evidence": opp.time_to_evidence,
                "reversibility": opp.reversibility_score,
                "competitive_asymmetry": opp.competitive_asymmetry,
                "execution_readiness": opp.execution_readiness,
                "uncertainty_penalty": opp.uncertainty_penalty,
                "risk_penalty": opp.risk_penalty,
            },
            "effective_independent_sources": effective_source_count(sources),
            "date_missing_rate": round(date_missing, 3),
            "stale": stale,
            "injection_flags": injection_flags,
        },
    )
    opp.scores = breakdown.as_dict()
    return opp, breakdown
