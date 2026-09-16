"""governance.py — PRE-0 constitutional core, as TESTABLE code (not just prose).

Encodes the owner-ratified precedence, hard constraints, self-improvement
boundary, the hard-constraint utility, and the AGI-status invariant so that
constitutional_tests/ can PROVE lower layers cannot override higher ones.

This is candidate governance for the OCTOPUS organism. It grants no authority;
it only constrains.
"""
from __future__ import annotations

# ── AGI status: an unverified HYPOTHESIS, never an identity or a FACT ──────────
AGI_STATUS = "unverified_hypothesis"


def agi_is_fact() -> bool:
    """AGI can never be asserted as FACT within the system."""
    return False


# ── Precedence: higher index = higher authority. Lower NEVER overrides higher ──
PRECEDENCE = [
    "retrieved_data",         # 0 — lowest
    "agent_prompt",
    "operational_narrative",
    "experiment_protocol",
    "memory_policy",
    "effect_policy",
    "global_halt",
    "constitution",           # 7 — highest (owner-ratified)
]


def authority(layer: str) -> int:
    return PRECEDENCE.index(layer)


def can_override(lower: str, higher: str) -> bool:
    """True only if `lower` is permitted to override `higher`. A layer may only
    override strictly-lower-authority layers; equal or higher => never."""
    return authority(lower) > authority(higher)


# ── Hard constraints: any failure => candidate rejected, utility = -inf ────────
HARD_CONSTRAINTS = (
    "no_unauthorized_external_effect", "no_credential_acquisition",
    "no_replication", "no_self_preservation_objective",
    "no_constitution_or_verifier_edit", "no_benchmark_leakage",
    "no_concealment", "no_unlogged_state", "rollback_required",
    "budget_and_timeout_required",
)


# ── Self-improvement boundary ─────────────────────────────────────────────────
SELF_IMPROVEMENT_ALLOWED = frozenset({
    "measure_capabilities", "reproduce_failures", "propose_candidates",
    "test_in_sandbox", "compare_frozen_baselines", "request_owner_review",
})
SELF_IMPROVEMENT_FORBIDDEN = frozenset({
    "edit_constitution", "edit_verifier", "expose_heldout_answers",
    "alter_acceptance_criteria", "acquire_credentials", "replicate",
    "resist_shutdown", "conceal_failures", "merge_or_deploy",
})


def self_improvement_permits(action: str) -> bool:
    """The self-improvement loop may only take explicitly-allowed actions and
    never a forbidden one. Unknown actions are denied (fail-closed)."""
    if action in SELF_IMPROVEMENT_FORBIDDEN:
        return False
    return action in SELF_IMPROVEMENT_ALLOWED


NEG_INF = float("-inf")


def utility(*, benchmark_gain: float, risk: float, cost: float,
            maintenance_debt: float, uncertainty: float,
            hard_constraints_ok: bool,
            wB: float = 1.0, wR: float = 1.0, wK: float = 1.0,
            wD: float = 1.0, wU: float = 1.0) -> float:
    """U = wB*gain - wR*risk - wK*cost - wD*debt - wU*uncertainty, BUT any hard
    constraint failure => -inf (benchmark gain can never compensate)."""
    if not hard_constraints_ok:
        return NEG_INF
    return (wB * benchmark_gain - wR * risk - wK * cost
            - wD * maintenance_debt - wU * uncertainty)


# ── Consensus is not evidence ─────────────────────────────────────────────────
def consensus_promotes(n_agreeing: int, has_independent_evidence: bool) -> bool:
    """Agreement among claimants never promotes a claim; only independent,
    verifiable evidence does."""
    return bool(has_independent_evidence)


# ── Experiment protocol: budget + timeout + rollback are mandatory ────────────
def validate_experiment(spec: dict) -> bool:
    """Fail-closed: an experiment is admissible only if it declares a positive
    budget, a positive timeout, and a rollback plan."""
    try:
        return (float(spec.get("budget", 0)) > 0
                and float(spec.get("timeout_s", 0)) > 0
                and bool(spec.get("rollback")))
    except Exception:
        return False


# ── Governance / maintenance lane: verifier/constitution defects are NOT fixed
#    by the self-improvement loop; they route to an owner-governed lane ─────────
def routes_to_maintenance_lane(target: str) -> bool:
    return target in ("constitution", "verifier")
