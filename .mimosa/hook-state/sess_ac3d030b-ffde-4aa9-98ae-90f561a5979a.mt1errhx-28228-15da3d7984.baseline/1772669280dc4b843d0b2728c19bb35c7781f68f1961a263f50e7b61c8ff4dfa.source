"""
brain/hypotheses.py — 14 falsifiable research hypotheses from the SOG synthesis.

Each hypothesis has:
    - independent variables (what we manipulate)
    - dependent variables (what we measure)
    - metric (how we measure it)
    - falsifier (what result would kill it)

These form a research agenda. The auto-experiment system can queue
and test them.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Hypothesis:
    """A single falsifiable research hypothesis."""
    id: int
    statement: str
    independent_vars: list[str]
    dependent_vars: list[str]
    metric: str
    expected_failure: str
    falsifier: str
    required_modules: list[str] = field(default_factory=list)


# ════════════════════════════════════════════════════════════════════════
#  The 14 hypotheses from the synthesis document
# ════════════════════════════════════════════════════════════════════════

HYPOTHESES: list[Hypothesis] = [
    Hypothesis(
        id=1,
        statement="Private scratchpads improve only tasks with real hidden intermediate state",
        independent_vars=["scratchpad on/off/corrupted"],
        dependent_vars=["accuracy", "log-loss"],
        metric="L_b - L_i (Δ_self)",
        expected_failure="Easy tasks show no gain",
        falsifier="No significant gain on hard multi-step tasks",
        required_modules=["worker", "dual-track evaluator"],
    ),
    Hypothesis(
        id=2,
        statement="Reflection gated by estimated Δ_self saves compute without hurting accuracy",
        independent_vars=["gate threshold"],
        dependent_vars=["accuracy", "tokens", "latency"],
        metric="accuracy per token",
        expected_failure="Threshold too strict",
        falsifier="Accuracy drops more than compute savings justify",
        required_modules=["worker", "gate", "verifier"],
    ),
    Hypothesis(
        id=3,
        statement="Shadow summaries can route many tasks nearly as well as full-state access",
        independent_vars=["summary size/detail"],
        dependent_vars=["routing success"],
        metric="full-state vs shadow-routing regret",
        expected_failure="Summaries omit rare critical details",
        falsifier="Shadow routing performs much worse",
        required_modules=["orchestrator", "shadow probe"],
    ),
    Hypothesis(
        id=4,
        statement="Private provenance metadata improves fan-in attribution",
        independent_vars=["metadata on/off"],
        dependent_vars=["source attribution accuracy"],
        metric="correct attribution rate",
        expected_failure="Metadata ignored or collisions occur",
        falsifier="No attribution gain",
        required_modules=["parent", "subagents", "aggregator"],
    ),
    Hypothesis(
        id=5,
        statement="Excessive dither increases diversity but lowers reliability",
        independent_vars=["temperature", "branch count"],
        dependent_vars=["diversity", "hallucination", "accuracy"],
        metric="Pareto curve",
        expected_failure="Randomness dominates reasoning",
        falsifier="No tradeoff observed",
        required_modules=["worker", "regulator"],
    ),
    Hypothesis(
        id=6,
        statement="Temporal probes recover hidden policy better than single-output probes",
        independent_vars=["probe sequence length"],
        dependent_vars=["next-action prediction"],
        metric="predictive log-loss",
        expected_failure="Target detects probing",
        falsifier="Sequential probes show no gain",
        required_modules=["probe agent", "target worker"],
    ),
    Hypothesis(
        id=7,
        statement="Leakage firewall reduces private-state inference from public outputs",
        independent_vars=["firewall on/off"],
        dependent_vars=["secret recovery rate", "answer quality"],
        metric="attack success probability",
        expected_failure="Utility collapses",
        falsifier="Leakage unchanged",
        required_modules=["adversary probe", "firewall"],
    ),
    Hypothesis(
        id=8,
        statement="Prompt anchors reduce long-context mode drift",
        independent_vars=["anchor type/frequency"],
        dependent_vars=["drift", "adherence"],
        metric="tool-choice entropy, instruction adherence",
        expected_failure="Anchors overconstrain",
        falsifier="No drift reduction",
        required_modules=["worker", "monitor"],
    ),
    Hypothesis(
        id=9,
        statement="Informed evaluators can be more biased than blind evaluators when rationales are persuasive but wrong",
        independent_vars=["rationale visibility"],
        dependent_vars=["grading accuracy"],
        metric="false acceptance rate",
        expected_failure="Rationale bias dominates",
        falsifier="Informed eval never worsens",
        required_modules=["blind eval", "informed eval"],
    ),
    Hypothesis(
        id=10,
        statement="Censored consensus improves hard tasks but may hurt easy tasks",
        independent_vars=["censor threshold"],
        dependent_vars=["accuracy by difficulty"],
        metric="stratified accuracy",
        expected_failure="Predictable correct votes downweighted",
        falsifier="Uniform improvement or uniform harm",
        required_modules=["voters", "censor", "aggregator"],
    ),
    Hypothesis(
        id=11,
        statement="Self-reported confidence is weaker than behavioral self-model score",
        independent_vars=["confidence access vs behavioral score"],
        dependent_vars=["calibration"],
        metric="Brier score, log-loss",
        expected_failure="Confident hallucination",
        falsifier="Self-report perfectly predicts correctness",
        required_modules=["worker", "evaluator"],
    ),
    Hypothesis(
        id=12,
        statement="Single-agent baseline beats MAS when coordination cost exceeds private-state gain",
        independent_vars=["task decomposability", "context length"],
        dependent_vars=["accuracy per cost"],
        metric="utility per token/latency",
        expected_failure="Handoff overhead dominates",
        falsifier="MAS always wins on atomic tasks",
        required_modules=["single agent", "MAS orchestrator"],
    ),
    Hypothesis(
        id=13,
        statement="Original-worker continuation beats fresh-worker only when private memory is causally relevant",
        independent_vars=["original vs fresh routing"],
        dependent_vars=["task success", "recovery time"],
        metric="handoff loss",
        expected_failure="Private memory stale",
        falsifier="Original worker never outperforms fresh",
        required_modules=["router", "original worker", "fresh worker"],
    ),
    Hypothesis(
        id=14,
        statement="Null-model rejection improves cost-adjusted quality",
        independent_vars=["baseline threshold"],
        dependent_vars=["accepted-answer quality", "rejection rate"],
        metric="margin over null",
        expected_failure="Baseline too weak/strong",
        falsifier="Rejection lowers quality or saves no cost",
        required_modules=["null model", "evaluator"],
    ),
]


def get_hypothesis(hid: int) -> Optional[Hypothesis]:
    """Get a hypothesis by ID."""
    for h in HYPOTHESES:
        if h.id == hid:
            return h
    return None


def get_testable_hypotheses() -> list[Hypothesis]:
    """Get all hypotheses (all are testable in principle)."""
    return HYPOTHESES


def queue_hypothesis_for_testing(hid: int):
    """Queue a hypothesis for the auto-experiment system."""
    h = get_hypothesis(hid)
    if h is None:
        return
    try:
        from memory.store import save_hypothesis
        save_hypothesis(
            domain=f"hypothesis-{hid}",
            hypothesis=h.statement,
            rationale=f"metric: {h.metric}; falsifier: {h.falsifier}",
        )
    except Exception:
        pass


if __name__ == "__main__":
    print(f"=== {len(HYPOTHESES)} Falsifiable Hypotheses ===\n")
    for h in HYPOTHESES:
        print(f"H{h.id}: {h.statement}")
        print(f"   metric: {h.metric}")
        print(f"   falsifier: {h.falsifier}")
        print()
