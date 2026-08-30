# impl/schemas.py — قراردادهای دادهٔ مغزِ فرضیه (Pydantic v2)
#
# طبق HYPOTHESIS-BRAIN-SPEC §2. تنها کابینِ _ops که Pydantic دارد (ADR-037).
# فیلدهای احتمال با Field(ge=0.0, le=1.0) محدود شده‌اند. extra="ignore" تا
# دورتایپ (round-trip) از dictهای مشتق‌شده از YAML (با کلیدهای اضافی مثل
# created_at/forbidden_effects/falsification_reason) بی‌صدا تحمل شود.
from __future__ import annotations

import math
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


# ---------------------------------------------------------------------------
# نردبان وضعیتِ فرضیه
# ---------------------------------------------------------------------------
class HypothesisStatus(str, Enum):
    SPECULATIVE = "SPECULATIVE"
    HYPOTHESIZING = "HYPOTHESIZING"
    TESTING = "TESTING"
    EVIDENCED = "EVIDENCED"
    FALSIFIED = "FALSIFIED"
    ARCHIVED = "ARCHIVED"


# ---------------------------------------------------------------------------
# درجهٔ شاهد (A قوی‌ترین … E ضعیف‌ترین) و وزنِ بیزیِ هر یک
# ---------------------------------------------------------------------------
class EvidenceGrade(str, Enum):
    A = "A"
    B = "B"
    C = "C"
    D = "D"
    E = "E"


GRADE_WEIGHTS: Dict[EvidenceGrade, float] = {
    EvidenceGrade.A: 1.0,
    EvidenceGrade.B: 0.6,
    EvidenceGrade.C: 0.35,
    EvidenceGrade.D: 0.15,
    EvidenceGrade.E: 0.05,
}


# ---------------------------------------------------------------------------
# ابزارهای ریچی: logit / sigmoid (پایدار در برابر سرریز و 0/1)
# ---------------------------------------------------------------------------
def logit(p: float) -> float:
    """log-odds(p) = ln(p/(1-p)). p∉(0,1) → ±inf (با sigmoid دورِ هم می‌خورَد)."""
    try:
        p = float(p)
    except (TypeError, ValueError):
        return 0.0
    if p <= 0.0:
        return -math.inf
    if p >= 1.0:
        return math.inf
    return math.log(p / (1.0 - p))


def sigmoid(x: float) -> float:
    """1/(1+e^-x). پایدار در برابر سرریز؛ x=+inf→1، x=-inf→0."""
    try:
        x = float(x)
    except (TypeError, ValueError):
        return 0.5
    if x == math.inf:
        return 1.0
    if x == -math.inf:
        return 0.0
    if x >= 0.0:
        z = math.exp(-x)
        return 0.0 if math.isinf(z) else 1.0 / (1.0 + z)
    z = math.exp(x)
    return z / (1.0 + z)


# ---------------------------------------------------------------------------
# مدل‌ها
# ---------------------------------------------------------------------------
class HypothesisRecord(BaseModel):
    """یک فرضیهٔ آزمون‌پذیر با شواهد (نه یک باور)."""

    model_config = ConfigDict(extra="ignore")

    id: str
    statement: str
    status: HypothesisStatus = HypothesisStatus.SPECULATIVE
    existence_probability: float = Field(default=0.1, ge=0.0, le=1.0)
    usefulness_probability: float = Field(default=0.5, ge=0.0, le=1.0)
    testability: float = Field(default=0.5, ge=0.0, le=1.0)
    cost_of_testing_hours: Optional[float] = None
    expected_information_gain: float = Field(default=0.0, ge=0.0, le=1.0)
    supporting_evidence_count: int = 0
    contradictory_evidence_count: int = 0
    test_plan: Optional[str] = None
    kill_condition: Optional[str] = None
    evidence_ids: List[str] = Field(default_factory=list)
    may_gate: bool = False
    may_trigger_tool: bool = False
    may_mutate_ledger: bool = False
    last_updated: Optional[datetime] = None
    created_at: Optional[datetime] = None


class HypothesisProposal(BaseModel):
    """خروجیِ مغز — پیشنهاد، نه تصمیم (الگوی ADR-034)."""

    model_config = ConfigDict(extra="ignore")

    record: HypothesisRecord
    priority_score: float
    rationale: str
    verdict: str
    trace_id: str = ""


class BeliefUpdateResult(BaseModel):
    """گزارشِ یک به‌روزرسانیِ بیزیِ p_e از مسیر شواهد."""

    model_config = ConfigDict(extra="ignore")

    hypothesis_id: str
    p_before: float
    p_after: float
    evidence_id: str
    direction: str
    weight: float
    new_status: HypothesisStatus
    transitioned: bool
