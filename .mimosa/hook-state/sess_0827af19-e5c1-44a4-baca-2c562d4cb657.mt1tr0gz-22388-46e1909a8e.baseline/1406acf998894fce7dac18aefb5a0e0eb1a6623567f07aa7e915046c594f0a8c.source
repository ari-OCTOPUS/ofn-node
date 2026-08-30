# brains/hypothesis_brain.py — مغز فرضیهٔ اکتپوس
# طبق HYPOTHESIS-BRAIN-SPEC.md v1.0 (2026-08-12)
# اصل بنیادین: باور غلطِ آزمون‌پذیر > باور درستِ آزمون‌ناپذیر.
# این مغز «باور» نمی‌سازد؛ فرضیه + طرح آزمون + شرط مرگ می‌سازد.
# خروجی = proposal (الگوی ADR-034) — هرگز registry را مستقیم نمی‌نویسد.
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import uuid4

from base_brain import BaseBrain, BrainError
from schemas import (
    GRADE_WEIGHTS,
    BeliefUpdateResult,
    EvidenceGrade,
    HypothesisProposal,
    HypothesisRecord,
    HypothesisStatus,
    logit,
    sigmoid,
)

PURSUE_THRESHOLD = 0.3
TESTABILITY_HARD_FLOOR = 0.0     # testability==0 → reject، فارغ از usefulness
MAX_ACTIVE = 20
EVIDENCED_THRESHOLD = 0.7
FALSIFIED_THRESHOLD = 0.15
W_SCAFFOLD = 0.5                 # وزن usefulness در pursue score

# گذارهای مجاز چرخهٔ عمر (از spec §۳)
ALLOWED_TRANSITIONS = {
    HypothesisStatus.SPECULATIVE: {HypothesisStatus.HYPOTHESIZING, HypothesisStatus.ARCHIVED},
    HypothesisStatus.HYPOTHESIZING: {HypothesisStatus.TESTING, HypothesisStatus.ARCHIVED},
    HypothesisStatus.TESTING: {HypothesisStatus.EVIDENCED, HypothesisStatus.FALSIFIED,
                               HypothesisStatus.ARCHIVED},
    HypothesisStatus.EVIDENCED: {HypothesisStatus.FALSIFIED, HypothesisStatus.ARCHIVED},
    HypothesisStatus.FALSIFIED: set(),    # نهایی — بایگانی، هرگز حذف نمی‌شود
    HypothesisStatus.ARCHIVED: set(),     # نهایی
}


def new_hypothesis_id() -> str:
    return f"HYP-{datetime.now(timezone.utc):%Y-%m-%d}-{uuid4().hex[:6].upper()}"


def pursue_score(h: HypothesisRecord, value_if_true: float = 1.0,
                 option_value: float = 0.0, budget_hours: float = 4.0) -> float:
    """p_e·V + EIG + u_s·w_s + u_o − c − risk  (spec §۳)"""
    p_e_v = h.existence_probability * value_if_true
    u_t = h.expected_information_gain
    u_s = h.usefulness_probability * W_SCAFFOLD
    c = (h.cost_of_testing_hours or 0.0) / budget_hours
    risk = 1.0 - h.testability             # آزمون‌ناپذیری = ریسک
    return p_e_v + u_t + u_s + option_value - c - risk


class HypothesisBrain(BaseBrain):
    """مغز فرضیه — تولید/رتبه‌بندی/به‌روزرسانی فرضیه‌ها (proposal-only)"""

    def __init__(self):
        super().__init__("hypothesis_brain")

    # ------------------------------------------------------------------
    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        op = input_data.get("op", "propose")
        if op == "propose":
            return self._propose(input_data)
        if op == "prioritize":
            return self._prioritize(input_data)
        if op == "update":
            return self._update(input_data)
        raise BrainError(self.name, f"op ناشناخته: {op}", recoverable=False)

    # ------------------------------------------------------------------
    def _propose(self, inp: Dict[str, Any]) -> Dict[str, Any]:
        h = HypothesisRecord(
            id=inp.get("id") or new_hypothesis_id(),
            statement=inp["statement"],
            existence_probability=inp.get("p_existence", 0.1),
            usefulness_probability=inp.get("p_usefulness", 0.5),
            testability=inp.get("testability", 0.5),
            cost_of_testing_hours=inp.get("cost_hours"),
            expected_information_gain=inp.get("eig", 0.0),
            test_plan=inp.get("test_plan"),
            kill_condition=inp.get("kill_condition"),
        )
        score = pursue_score(
            h,
            value_if_true=inp.get("value_if_true", 1.0),
            option_value=inp.get("option_value", 0.0),
        )
        reject_reason = None
        if h.testability <= TESTABILITY_HARD_FLOOR:
            reject_reason = "testability==0 — آزمون‌ناپذیر (قاعدهٔ سخت)"
        elif score < PURSUE_THRESHOLD:
            reject_reason = f"priority {score:.3f} < θ={PURSUE_THRESHOLD}"
        verdict = "reject" if reject_reason else "pursue"

        proposal = HypothesisProposal(
            record=h,
            priority_score=score,
            rationale=self._rationale(h, score, verdict, reject_reason),
            verdict=verdict,
        )
        return {
            "proposal": proposal.model_dump(mode="json"),
            "verdict": verdict,
            "reject_reason": reject_reason,
            "status": "completed",
        }

    # ------------------------------------------------------------------
    def _prioritize(self, inp: Dict[str, Any]) -> Dict[str, Any]:
        """مرتب‌سازی فرضیه‌های فعال بر اساس pursue_score با سقف MAX_ACTIVE."""
        records = [HypothesisRecord(**r) for r in inp.get("hypotheses", [])]
        active = [h for h in records if h.status in (
            HypothesisStatus.SPECULATIVE, HypothesisStatus.HYPOTHESIZING,
            HypothesisStatus.TESTING)]
        scored = sorted(
            ((pursue_score(h), h) for h in active),
            key=lambda t: t[0], reverse=True,
        )
        ranked = [
            {"id": h.id, "statement": h.statement, "priority": round(s, 4),
             "status": h.status.value}
            for s, h in scored
        ]
        overflow = ranked[MAX_ACTIVE:]
        return {
            "ranked": ranked[:MAX_ACTIVE],
            "overflow_count": len(overflow),
            "overflow_ids": [r["id"] for r in overflow],
            "status": "completed",
        }

    # ------------------------------------------------------------------
    def _update(self, inp: Dict[str, Any]) -> Dict[str, Any]:
        """تنها راه تغییر p_e: شواهد متصل به ledger. تزریق مستقیم ممنوع."""
        evidence_id = inp.get("evidence_id")
        if not evidence_id:
            raise BrainError(
                self.name,
                "update بدون evidence_id ممنوع است — تنها راه تغییر باور، شواهد است",
                recoverable=False,
            )
        h = HypothesisRecord(**inp["hypothesis"])
        grade = EvidenceGrade(inp.get("grade", "C"))
        direction = inp.get("direction")
        if direction not in ("support", "contradict"):
            raise BrainError(self.name, f"direction نامعتبر: {direction}",
                             recoverable=False)

        p_before = h.existence_probability
        w = GRADE_WEIGHTS[grade]
        h.existence_probability = sigmoid(
            logit(p_before) + (w if direction == "support" else -w))
        if direction == "support":
            h.supporting_evidence_count += 1
        else:
            h.contradictory_evidence_count += 1
        if evidence_id not in h.evidence_ids:
            h.evidence_ids.append(evidence_id)
        h.last_updated = datetime.now(timezone.utc)

        # گذار خودکار وضعیت بر اساس آستانه‌ها (فقط در TESTING)
        transitioned = False
        if h.status == HypothesisStatus.TESTING:
            if h.existence_probability >= EVIDENCED_THRESHOLD:
                h.status = HypothesisStatus.EVIDENCED
                transitioned = True
            elif h.existence_probability <= FALSIFIED_THRESHOLD:
                h.status = HypothesisStatus.FALSIFIED
                transitioned = True

        result = BeliefUpdateResult(
            hypothesis_id=h.id, p_before=p_before,
            p_after=h.existence_probability, evidence_id=evidence_id,
            direction=direction, weight=w, new_status=h.status,
            transitioned=transitioned,
        )
        return {
            "update": result.model_dump(mode="json"),
            "hypothesis": h.model_dump(mode="json"),
            "status": "completed",
        }

    # ------------------------------------------------------------------
    @staticmethod
    def _rationale(h: HypothesisRecord, score: float, verdict: str,
                   reject_reason: Optional[str]) -> str:
        if verdict == "pursue":
            return (
                f"p_e={h.existence_probability:.2f} (حتی اگر پایین) ولی "
                f"EIG={h.expected_information_gain:.2f} + usefulness="
                f"{h.usefulness_probability:.2f} ⇒ ارزش آزمون دارد. "
                f"score={score:.3f} ≥ θ."
            )
        return f"reject: {reject_reason}. score={score:.3f}."

    # ------------------------------------------------------------------
    @staticmethod
    def can_transition(src: HypothesisStatus, dst: HypothesisStatus) -> bool:
        return dst in ALLOWED_TRANSITIONS.get(src, set())
