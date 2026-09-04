"""brain_schema — قرارداد ورودی مغز (GAP-066، فریز قبل از قابلیت).

مغز ۱۸۰ وقتی رویداد خام می‌بیند، فقط «چیزی شده» را می‌فهمد — نه «چه کاری
باید بکند». این قرارداد رویداد را structured می‌کند تا مغز بتواند proposal
عملیاتی بسازد نه فقط confirmِ خام.

فریز شده با FROZEN pattern (همان الگوی runtime_truth_v1). فقط stdlib.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple

CONTRACT_SCHEMA = "brain_input.v1"

EVENT_TYPES: Tuple[str, ...] = (
    "payment.verified",
    "payment.claimed",
    "communication.quote_requested",
    "communication.sent",
    "lead.discovered",
    "order.received",
)

BUSINESS_IDS: Tuple[str, ...] = (
    "painting", "ziman", "studio",
)

ACTION_TYPES: Tuple[str, ...] = (
    "rank", "propose", "verify", "hold", "escalate",
)


class SchemaViolation(ValueError):
    pass


@dataclass(frozen=True)
class BrainEvent:
    """یک رویداد structured که مغز می‌فهمد."""
    event_type: str
    business_id: str
    lead_id: str
    occurred_at: str
    amount_aud: float | None = None
    detail: str = ""

    def __post_init__(self) -> None:
        if self.event_type not in EVENT_TYPES:
            raise SchemaViolation(
                f"event_type {self.event_type!r} not in {EVENT_TYPES}")
        if self.business_id not in BUSINESS_IDS:
            raise SchemaViolation(
                f"business_id {self.business_id!r} not in {BUSINESS_IDS}")

    def as_dict(self) -> dict:
        return {
            "event_type": self.event_type,
            "business_id": self.business_id,
            "lead_id": self.lead_id,
            "occurred_at": self.occurred_at,
            "amount_aud": self.amount_aud,
            "detail": self.detail,
        }


@dataclass(frozen=True)
class BrainProposal:
    """پاسخ عملیاتی مغز — نه متن آزاد."""
    business_id: str
    action: str            # rank | propose | verify | hold | escalate
    summary: str
    confidence: float      # 0.0-1.0
    evidence_shas: Tuple[str, ...] = ()
    hold_external: bool = True
    may_authorize: bool = False

    def __post_init__(self) -> None:
        if self.action not in ACTION_TYPES:
            raise SchemaViolation(
                f"action {self.action!r} not in {ACTION_TYPES}")
        if self.business_id not in BUSINESS_IDS:
            raise SchemaViolation(
                f"business_id {self.business_id!r} not in {BUSINESS_IDS}")
        if not (0.0 <= self.confidence <= 1.0):
            raise SchemaViolation(
                f"confidence {self.confidence} outside [0,1]")
        if self.may_authorize:
            raise SchemaViolation(
                "may_authorize=True is forbidden — brain never authorizes")
