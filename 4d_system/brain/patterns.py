"""
brain/patterns.py — Architectural patterns from the SOG synthesis.

Each pattern is a reusable design that translates a theoretical SOG concept
into an implementable engineering decision. These are the "novel architecture
ideas" from the comprehensive synthesis document.

The patterns are dataclasses (not classes) — they describe decisions,
not execute them. The graph/nodes use them as decision policies.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional, Callable
from enum import Enum


# ════════════════════════════════════════════════════════════════════════
#  Pattern 1: Blind/Informed Dual-Track Evaluator
# ════════════════════════════════════════════════════════════════════════

class TrackType(Enum):
    NULL = "null"       # sees only marginal statistics
    BLIND = "blind"     # sees public trace only
    INFORMED = "informed"  # sees public + private state


@dataclass
class DualTrackEvaluation:
    """
    Run evaluation with blind and informed tracks.
    Measures whether private state actually helps (Δ_self in practice).

    Core insight: A private rationale is useful ONLY if access to it
    improves prediction or evaluation.

    Failure prevented: Treating scratchpads/CoT as trustworthy introspection
    without causal evidence.
    """
    blind_score: float       # L_b: score of blind evaluator
    informed_score: float    # L_i: score of informed evaluator
    null_score: float        # L_0: score of null/baseline evaluator

    @property
    def delta_self(self) -> float:
        """SMS = L_b - L_i: how much private state helped."""
        return self.blind_score - self.informed_score

    @property
    def shadow_leakage(self) -> float:
        """SLS = L_0 - L_b: how much was inferrable from public trace."""
        return self.null_score - self.blind_score

    @property
    def private_state_is_useful(self) -> bool:
        """True if private state meaningfully improved the outcome."""
        return self.delta_self > 0.01

    @property
    def verdict(self) -> str:
        if self.delta_self < 0.005:
            return "PRIVATE STATE DECORATIVE — scratchpad/memory adds no value"
        elif self.delta_self > 0.05:
            return "PRIVATE STATE CAUSAL — reflection/memory justified"
        else:
            return "PRIVATE STATE MARGINAL — small but non-zero gain"

    def summary(self) -> dict:
        return {
            "null": self.null_score,
            "blind": self.blind_score,
            "informed": self.informed_score,
            "Δ_self": self.delta_self,
            "shadow_leakage": self.shadow_leakage,
            "verdict": self.verdict,
        }


# ════════════════════════════════════════════════════════════════════════
#  Pattern 2: Delta-Self Reflection Gate
# ════════════════════════════════════════════════════════════════════════

@dataclass
class ReflectionGate:
    """
    Conditional reflection: only allow another reflection pass if
    the expected private-state gain exceeds cost.

    Core insight: Reflection should be conditional on expected marginal gain.
    Prevents endless "let me reconsider" loops.

    SOG concept: Self-model gain (Δ_self).
    """
    cost_per_reflection: float = 0.02   # token/latency cost threshold
    current_delta: float = 0.0          # measured gain from last reflection
    max_reflections: int = 3            # hard cap

    def should_reflect(self, reflection_count: int) -> bool:
        """
        Decide whether to allow another reflection pass.
        """
        if reflection_count >= self.max_reflections:
            return False
        # Only reflect if the last reflection produced meaningful gain
        return self.current_delta > self.cost_per_reflection

    def update(self, new_delta: float):
        """Update the measured gain from the latest reflection."""
        self.current_delta = new_delta


def reflect_should_revise(state: dict,
                          max_reflections: int | None = None) -> bool:
    """B1: تصمیمِ حلقه‌ی بازتاب — خالص و تست‌پذیر (بدونِ وابستگی به LangGraph).

    فلگ خاموش (پیش‌فرض): دقیقاً رفتارِ قبلی — تا وقتی quality == "REVISE" ادامه
    بده (تنها سقف، recursion_limit خودِ گراف بود که با خطای ناگرفته می‌ترکید).
    با REFLECT_GATE=1: سقفِ نرم اعمال می‌شود — بیش از REFLECT_MAX (پیش‌فرض ۳)
    بازنویسی نمی‌کنیم؛ حلقه‌ی «بگذار دوباره فکر کنم» تمام‌شدنی می‌شود.
    شمارنده (reflect_count) را reflect_node در state افزایش می‌دهد.
    """
    import os

    revise = state.get("quality") == "REVISE"
    if not revise:
        return False
    count = int(state.get("reflect_count", 0) or 0)

    # سقفِ سختِ بی‌قیدوشرط (حتی با فلگِ خاموش): حلقه‌ی report↔reflect نباید تا
    # recursion_limit با تماس‌های ابریِ واقعی بچرخد. بازبینیِ خصمانه نشان داد
    # پیش‌فرضِ قبلی (فلگ خاموش → بی‌سقف) مصرفِ ابری را منفجر می‌کرد.
    hard_cap = int(os.getenv("REFLECT_HARD_MAX", "5"))
    if count >= hard_cap:
        return False

    if os.getenv("REFLECT_GATE", "0") != "1":
        return revise                       # رفتارِ قبلی، ولی زیرِ سقفِ سخت
    cap = (max_reflections if max_reflections is not None
           else int(os.getenv("REFLECT_MAX", "3")))
    return count < cap


# ════════════════════════════════════════════════════════════════════════
#  Pattern 3: Shadow-Guided Routing
# ════════════════════════════════════════════════════════════════════════

@dataclass
class ShadowRouter:
    """
    Route based on compressed public shadows, not full private state.

    Core insight: Orchestrator should route from public summaries.
    Solves context-window/bandwidth explosion in large swarms.

    SOG concept: E_shadow (public-state predictability).
    """
    shadow_leakage_score: float  # SLS from the dual-track evaluation
    full_state_routing_cost: float = 1.0  # relative cost of full-state routing

    @property
    def can_route_by_shadow(self) -> bool:
        """
        True if public trace carries enough signal for routing.
        High SLS = good for monitoring, bad for privacy.
        """
        return self.shadow_leakage_score > 0.01

    @property
    def routing_strategy(self) -> str:
        if self.can_route_by_shadow:
            return "SHADOW — route from public summaries (cheap)"
        else:
            return "FULL-STATE — shadow too weak, need full context (expensive)"


# ════════════════════════════════════════════════════════════════════════
#  Pattern 4: Epistemic Censor
# ════════════════════════════════════════════════════════════════════════

@dataclass
class EpistemicCensor:
    """
    Gate irreversible actions when internal evidence is weak.

    Core insight: High public confidence with high private uncertainty
    should trigger intervention.

    SOG concept: Blind/informed asymmetry.
    """
    public_confidence: float    # confidence shown to user
    private_uncertainty: float  # actual uncertainty from private state
    evidence_completeness: float  # 0..1, how complete is the evidence
    action_reversible: bool = True

    @property
    def confidence_gap(self) -> float:
        """Large gap = suspicious overconfidence."""
        return self.public_confidence - (1.0 - self.private_uncertainty)

    @property
    def should_block(self) -> bool:
        """
        Block if: irreversible AND (confident outside, uncertain inside)
        OR evidence is very incomplete.
        """
        if self.action_reversible and self.evidence_completeness > 0.7:
            return False
        if self.confidence_gap > 0.3 and self.private_uncertainty > 0.4:
            return True
        if self.evidence_completeness < 0.3:
            return True
        return False

    @property
    def verdict(self) -> str:
        if self.should_block:
            return "BLOCKED — epistemic censor: overconfident with weak evidence"
        return "ALLOWED"


# ════════════════════════════════════════════════════════════════════════
#  Pattern 5: Null-Model Baseline Rejection
# ════════════════════════════════════════════════════════════════════════

@dataclass
class NullModelRejection:
    """
    Reject outputs that don't beat a simple baseline.

    Core insight: No multi-agent output should be accepted unless it
    beats a cheap baseline. Prevents costly but trivial outputs.

    SOG concept: L_0 null floor.
    """
    worker_score: float       # actual output quality
    null_score: float         # baseline quality (retrieval-only, rules, etc.)
    margin_threshold: float = 0.05  # minimum improvement required

    @property
    def margin(self) -> float:
        return self.worker_score - self.null_score

    @property
    def should_accept(self) -> bool:
        return self.margin > self.margin_threshold

    @property
    def verdict(self) -> str:
        if self.should_accept:
            return f"ACCEPT — margin over null: +{self.margin:.3f}"
        return f"REJECT — no meaningful improvement (margin: {self.margin:.3f})"


# ════════════════════════════════════════════════════════════════════════
#  Pattern 6: Counterfactual Self-Surgery (ablation harness)
# ════════════════════════════════════════════════════════════════════════

@dataclass
class CounterfactualAblation:
    """
    Test whether private reasoning is causal by removing/corrupting it.

    Core insight: Private reasoning is causal ONLY if editing/removing it
    changes outcomes predictably.

    SOG concept: Informed-vs-blind causal gap.

    Run task with: original / removed / corrupted / shuffled private state.
    """
    original_score: float
    removed_score: float
    corrupted_score: float
    shuffled_score: float

    @property
    def causal_gap(self) -> float:
        """How much removing private state hurt."""
        return self.original_score - self.removed_score

    @property
    def is_causal(self) -> bool:
        """Private state is causal if removal significantly hurts."""
        return self.causal_gap > 0.03

    @property
    def robustness_to_corruption(self) -> float:
        """How sensitive to corruption (higher = more fragile)."""
        return self.original_score - self.corrupted_score

    def summary(self) -> dict:
        return {
            "original": self.original_score,
            "removed": self.removed_score,
            "corrupted": self.corrupted_score,
            "shuffled": self.shuffled_score,
            "causal_gap": self.causal_gap,
            "is_causal": self.is_causal,
            "corruption_sensitivity": self.robustness_to_corruption,
            "verdict": (
                "PRIVATE STATE IS CAUSAL — introspection trustworthy"
                if self.is_causal else
                "PRIVATE STATE DECORATIVE — post-hoc rationalization"
            ),
        }


# ════════════════════════════════════════════════════════════════════════
#  Pattern catalog for reference
# ════════════════════════════════════════════════════════════════════════

PATTERN_CATALOG = {
    "dual-track": {
        "class": DualTrackEvaluation,
        "name": "Blind/Informed Dual-Track Evaluator",
        "sog_concept": "Δ_self = L_b - L_i",
        "problem": "Distinguishing real private-state value from decorative scratchpads",
    },
    "reflection-gate": {
        "class": ReflectionGate,
        "name": "Delta-Self Reflection Gate",
        "sog_concept": "Self-model gain",
        "problem": "Prevents endless reflection loops",
    },
    "shadow-router": {
        "class": ShadowRouter,
        "name": "Shadow-Guided Orchestrator",
        "sog_concept": "E_shadow",
        "problem": "Context-window explosion in large swarms",
    },
    "epistemic-censor": {
        "class": EpistemicCensor,
        "name": "Epistemic Censor",
        "sog_concept": "Blind/informed asymmetry",
        "problem": "Unsafe tool use when evidence is weak",
    },
    "null-rejection": {
        "class": NullModelRejection,
        "name": "Null-Model Baseline Rejection",
        "sog_concept": "L_0 null floor",
        "problem": "Costly but non-informative outputs",
    },
    "counterfactual": {
        "class": CounterfactualAblation,
        "name": "Counterfactual Self-Surgery",
        "sog_concept": "Informed-vs-blind causal gap",
        "problem": "Separating real reasoning from rationalization",
    },
}


if __name__ == "__main__":
    print("=== Pattern Tests ===\n")

    # Dual-track
    dt = DualTrackEvaluation(blind_score=0.15, informed_score=0.03, null_score=0.17)
    print(f"1. Dual-Track: {dt.verdict}")
    print(f"   Δ_self={dt.delta_self:.3f}, leakage={dt.shadow_leakage:.3f}")

    # Reflection gate
    rg = ReflectionGate(cost_per_reflection=0.02)
    rg.update(0.05)  # last reflection gained 0.05
    print(f"\n2. Reflection Gate: should_reflect(1)={rg.should_reflect(1)}")
    rg.update(0.005)  # now barely helps
    print(f"   should_reflect(2)={rg.should_reflect(2)}")

    # Shadow router
    sr = ShadowRouter(shadow_leakage_score=0.013)
    print(f"\n3. Shadow Router: {sr.routing_strategy}")

    # Epistemic censor
    ec = EpistemicCensor(public_confidence=0.9, private_uncertainty=0.5,
                         evidence_completeness=0.3, action_reversible=False)
    print(f"\n4. Epistemic Censor: {ec.verdict}")

    # Null rejection
    nr = NullModelRejection(worker_score=0.12, null_score=0.10)
    print(f"\n5. Null Rejection: {nr.verdict}")

    # Counterfactual
    cf = CounterfactualAblation(original_score=0.15, removed_score=0.08,
                                 corrupted_score=0.10, shuffled_score=0.09)
    print(f"\n6. Counterfactual: {cf.summary()['verdict']}")
    print(f"   causal_gap={cf.causal_gap:.3f}")
