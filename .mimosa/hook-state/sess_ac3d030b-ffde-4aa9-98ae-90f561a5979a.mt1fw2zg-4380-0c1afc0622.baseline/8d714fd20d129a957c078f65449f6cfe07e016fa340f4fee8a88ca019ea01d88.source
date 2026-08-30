"""opportunity.py — ساخت فرصت از تقاطع سیگنال‌ها.

بند ۱۱: کاندیداهای فرصت از تقاطع این سیگنال‌ها ساخته می‌شوند:
  تغییر تازه بازار × درد واقعی مشتری × ضعف رقیب × قابلیت اختاپوس × امکان آزمایش کم‌هزینه

دسته‌های فرصت: unmet-need, market-gap, competitor-weakness, regulatory-change,
pricing-anomaly, distribution-gap, workflow-inefficiency, new-public-dataset,
new-tender-pattern, underserved-geography, capability-composition, tool-opportunity,
partnership-opportunity, customer-acquisition-signal, operational-risk, ai-architecture-insight.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from .contracts import OPP_TYPES, Opportunity
from .competitor_intel import AsymmetryHypothesis


@dataclass
class OpportunitySeed:
    """ورودی برای ساخت یک فرصت."""

    claim: str
    opp_type: str
    discovery_id: str
    asymmetry: Optional[AsymmetryHypothesis] = None
    estimated_value: Optional[str] = None
    time_to_test_days: Optional[int] = None
    reversibility: str = "high"


def classify_opportunity_type(claim: str, asymmetry: Optional[AsymmetryHypothesis]) -> str:
    """حدس نوع فرصت از ادعا + asymmetry."""
    low = (claim or "").lower()

    if asymmetry and asymmetry.competitor_structural_weakness:
        w = asymmetry.competitor_structural_weakness.lower()
        if any(k in low for k in ("pric", "cost", "expensive")) or "expensive" in w:
            return "pricing-anomaly"
        if any(k in low for k in ("distribut", "channel", "reach")):
            return "distribution-gap"
        if any(k in low for k in ("workflow", "process", "inefficien")):
            return "workflow-inefficiency"
        if any(k in low for k in ("tool", "integration", "api")):
            return "tool-opportunity"
        if any(k in low for k in ("dataset", "data")):
            return "new-public-dataset"
        if any(k in low for k in ("architecture", "design", "approach")):
            return "ai-architecture-insight"
        # default وقتی asymmetry داریم
        return "competitor-weakness"

    if any(k in low for k in ("unmet", "no one", "missing", "gap in")):
        return "unmet-need"
    if any(k in low for k in ("market gap", "underserved", "neglect")):
        return "market-gap"
    if any(k in low for k in ("regulat", "law", "compliance")):
        return "regulatory-change"
    if any(k in low for k in ("tender", "procurement", "rfp")):
        return "new-tender-pattern"
    if any(k in low for k in ("partnership", "collaborat", "alliance")):
        return "partnership-opportunity"
    if any(k in low for k in ("acquisition", "lead", "customer signal")):
        return "customer-acquisition-signal"
    if any(k in low for k in ("threat", "risk", "danger")):
        return "operational-risk"
    if any(k in low for k in ("trend", "shift", "emerging")):
        return "trend"

    return "ai-architecture-insight"


def build_opportunity(seed: OpportunitySeed) -> Opportunity:
    """ساخت یک Opportunity از seed. امتیازدهی در scorer انجام می‌شود."""
    opp_type = seed.opp_type or classify_opportunity_type(seed.claim, seed.asymmetry)
    if opp_type not in OPP_TYPES:
        opp_type = "ai-architecture-insight"

    asym_str = ""
    if seed.asymmetry:
        asym_str = (
            f"مزیت نامتقارن: {seed.asymmetry.octopus_local_advantage} "
            f"در برابر ضعف {seed.asymmetry.competitor_advantage} رقیب."
        )

    return Opportunity(
        type=opp_type,
        claim=seed.claim,
        estimated_value=seed.estimated_value,
        time_to_test_days=seed.time_to_test_days,
        reversibility=seed.reversibility,
        discovery_id=seed.discovery_id,
        asymmetry=asym_str,
        confidence=0.0,  # تا scorer پر شود
    )


def opportunity_is_testable(
    opp: Opportunity,
    *,
    horizon_days: int,
    max_level: str = "L1",
) -> bool:
    """آیا این فرصت در افق و سطح مجاز قابل آزمایش است؟"""
    if opp.time_to_test_days is not None and opp.time_to_test_days > horizon_days:
        return False
    if opp.reversibility == "low":
        return False
    return True
