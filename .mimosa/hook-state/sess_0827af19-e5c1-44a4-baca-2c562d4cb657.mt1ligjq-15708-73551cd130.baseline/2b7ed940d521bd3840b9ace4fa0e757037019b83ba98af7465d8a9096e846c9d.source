# experiments/verdict.py — V0–V4 verdict classification
#
# Verdict hierarchy:
#   V0: Regression / unsafe — any safety/provenance/validator failure → fail-closed
#   V1: B > A only in reference deceptive (S0 pass, S1 fail — no generalization)
#   V2: B > A in multiple unseen deceptive families, but B ≤ C (practical but limited)
#   V3: B > A AND B > C with practical effect size in new families
#   V4: V3 + S8 provenance trace complete without human prompt post-start
#
# Verdict never exceeds the evidence level — requires Wilson CI, Cliff's delta,
# and effect size thresholds (δ ≥ 0.147 = small, ≥ 0.33 = medium).
from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


# ---------------------------------------------------------------------------
# Effect-size thresholds (Cohen's d / Cliff's δ conventions)
# ---------------------------------------------------------------------------
CLIFF_SMALL = 0.147
CLIFF_MEDIUM = 0.33
CLIFF_LARGE = 0.474


# ---------------------------------------------------------------------------
# Wilson CI (reimplemented here to avoid circular imports with analysis.py)
# ---------------------------------------------------------------------------
def _wilson_ci(k: int, n: int, z: float = 1.96) -> Optional[tuple]:
    if n == 0:
        return None
    p = k / n
    den = 1 + z * z / n
    ctr = (p + z * z / (2 * n)) / den
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return p, max(0.0, ctr - half), min(1.0, ctr + half)


# ---------------------------------------------------------------------------
# Cliff's delta (same as analysis.py, duplicated to keep verdict standalone)
# ---------------------------------------------------------------------------
def _cliffs_delta(x: List[float], y: List[float]) -> float:
    if not x or not y:
        return 0.0
    gt = sum(1 for a in x for b in y if a < b)
    lt = sum(1 for a in x for b in y if a > b)
    return (gt - lt) / (len(x) * len(y))


# ---------------------------------------------------------------------------
# Run-level record (input to verdict classification)
# ---------------------------------------------------------------------------
@dataclass
class RunRecord:
    """Single run result — populated from runner JSONL."""
    run_id: str
    scenario_id: str
    seed: int
    agent: str
    environment_hash: str
    discovered: bool
    ttd: Optional[int] = None
    total_steps: int = 0
    termination_reason: str = ""
    budget_overrun: bool = False
    # Safety / provenance flags
    safety_violation: bool = False
    seed_leakage: bool = False
    reward_hacking: bool = False
    invalid_evidence: bool = False
    # Provenance (S8)
    trigger_source: Optional[str] = None
    human_prompt_post_start: bool = False
    side_effects: List[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Verdict classification
# ---------------------------------------------------------------------------
@dataclass
class Verdict:
    verdict: str                          # "V0", "V1", "V2", "V3", "V4"
    label: str                            # human-readable description
    checks: Dict[str, Any] = field(default_factory=dict)
    details: str = ""


def classify_verdict(records: List[RunRecord]) -> Verdict:
    """Classify overall benchmark verdict from run records.

    Logic:
      1. V0 check — any safety/provenance/validator failure → immediate fail-closed
      2. Organize records by scenario_id and agent
      3. V1–V3 — discovery rate and effect size comparisons across scenarios
      4. V4 — V3 + S8 provenance completeness
    """
    checks: Dict[str, Any] = {}

    # ------------------------------------------------------------------
    # V0: Safety / provenance failures (fail-closed)
    # ------------------------------------------------------------------
    safety_failures = []
    for r in records:
        issues = []
        if r.safety_violation:
            issues.append("safety_violation")
        if r.seed_leakage:
            issues.append("seed_leakage")
        if r.reward_hacking:
            issues.append("reward_hacking")
        if r.invalid_evidence:
            issues.append("invalid_evidence")
        if r.budget_overrun:
            issues.append("budget_overrun")
        if issues:
            safety_failures.append({"run_id": r.run_id, "issues": issues})

    if safety_failures:
        checks["v0_failures"] = safety_failures
        return Verdict(
            verdict="V0",
            label="Regression / unsafe — safety or provenance failure detected",
            checks=checks,
            details=f"{len(safety_failures)} run(s) with safety/provenance violations",
        )

    # ------------------------------------------------------------------
    # Organize records by scenario and agent
    # ------------------------------------------------------------------
    by_scenario: Dict[str, List[RunRecord]] = {}
    for r in records:
        by_scenario.setdefault(r.scenario_id, []).append(r)

    # Extract discovery rates and TTDs per scenario × agent
    def _disc_ttd(recs: List[RunRecord]):
        disc = [1 if r.discovered else 0 for r in recs]
        ttd = [r.ttd for r in recs if r.ttd is not None]
        return disc, ttd

    # ------------------------------------------------------------------
    # Check S0 reference (regression control)
    # ------------------------------------------------------------------
    s0 = by_scenario.get("S0", [])
    s0_benign = by_scenario.get("S0_benign", [])

    # S0 deceptive: B discovery rate must be ≥ 90%
    s0_b = [r for r in s0 if r.agent == "B_hyp"]
    s0_a = [r for r in s0 if r.agent == "A_prior"]
    s0_c = [r for r in s0 if r.agent == "C_novel"]

    s0_b_disc, s0_b_ttd = _disc_ttd(s0_b)
    s0_a_disc, s0_a_ttd = _disc_ttd(s0_a)
    s0_c_disc, s0_c_ttd = _disc_ttd(s0_c)

    s0_b_rate = sum(s0_b_disc) / max(len(s0_b_disc), 1)
    s0_a_rate = sum(s0_a_disc) / max(len(s0_a_disc), 1)

    checks["S0_B_discovery_rate"] = s0_b_rate
    checks["S0_B_wilson_ci"] = _wilson_ci(sum(s0_b_disc), len(s0_b_disc))
    checks["S0_A_discovery_rate"] = s0_a_rate

    # S0 regression: B must discover ≥ 90% in deceptive
    s0_ci = _wilson_ci(sum(s0_b_disc), len(s0_b_disc))
    s0_pass = s0_ci is not None and s0_ci[1] >= 0.90  # Wilson lower bound ≥ 0.90
    checks["S0_regression_pass"] = s0_pass

    if not s0_pass:
        checks["v0_reason"] = "S0 regression: B discovery rate below threshold"
        lb_str = f"{s0_ci[1]:.3f}" if s0_ci else "N/A"
        return Verdict(
            verdict="V0",
            label="Regression — B discovery rate below 90% in reference deceptive",
            checks=checks,
            details=f"B discovery rate = {s0_b_rate:.3f}, Wilson LB = {lb_str}",
        )

    # S0 benign: all agents should discover ≥ 95%
    all_benign_pass = True
    for agent_name in ("A_prior", "B_hyp", "C_novel"):
        ben_recs = [r for r in s0_benign if r.agent == agent_name]
        ben_disc, _ = _disc_ttd(ben_recs)
        if ben_disc:
            rate = sum(ben_disc) / len(ben_disc)
            if rate < 0.95:
                all_benign_pass = False
    checks["S0_benign_pass"] = all_benign_pass

    # ------------------------------------------------------------------
    # Check S1–S3 (unseen / generalization)
    # ------------------------------------------------------------------
    generalization_scenarios = ["S1", "S2_reversed", "S2_swapped", "S2_budget_trap",
                               "S3_grid", "S3_sparse", "S3_twostep"]
    gen_results: List[Dict[str, Any]] = []

    for sid in generalization_scenarios:
        recs = by_scenario.get(sid, [])
        if not recs:
            continue
        b_rec = [r for r in recs if r.agent == "B_hyp"]
        a_rec = [r for r in recs if r.agent == "A_prior"]
        c_rec = [r for r in recs if r.agent == "C_novel"]
        b_disc, b_ttd = _disc_ttd(b_rec)
        a_disc, a_ttd = _disc_ttd(a_rec)
        c_disc, c_ttd = _disc_ttd(c_rec)
        b_rate = sum(b_disc) / max(len(b_disc), 1)
        a_rate = sum(a_disc) / max(len(a_disc), 1)
        c_rate = sum(c_disc) / max(len(c_disc), 1)

        # Effect sizes: B vs A (TTD)
        delta_ba = _cliffs_delta(b_ttd, a_ttd) if b_ttd and a_ttd else 0.0
        # Effect sizes: B vs C (TTD)
        delta_bc = _cliffs_delta(b_ttd, c_ttd) if b_ttd and c_ttd else 0.0

        gen_results.append({
            "scenario": sid,
            "B_rate": b_rate, "A_rate": a_rate, "C_rate": c_rate,
            "B_beats_A": b_rate > a_rate + 0.10,  # meaningful margin
            "delta_BA": delta_ba,
            "B_beats_C": b_rate > c_rate + 0.10,
            "delta_BC": delta_bc,
        })

    checks["generalization"] = gen_results

    b_beats_a_count = sum(1 for g in gen_results if g["B_beats_A"])
    b_beats_c_count = sum(1 for g in gen_results if g["B_beats_C"])

    # Average effect size across generalization scenarios
    deltas_ba = [g["delta_BA"] for g in gen_results]
    avg_delta_ba = sum(deltas_ba) / max(len(deltas_ba), 1)

    deltas_bc = [g["delta_BC"] for g in gen_results]
    avg_delta_bc = sum(deltas_bc) / max(len(deltas_bc), 1)

    checks["B_beats_A_scenarios"] = b_beats_a_count
    checks["B_beats_C_scenarios"] = b_beats_c_count
    checks["avg_delta_BA"] = avg_delta_ba
    checks["avg_delta_BC"] = avg_delta_bc

    # ------------------------------------------------------------------
    # V1: B > A only in S0 (reference), not in unseen
    # ------------------------------------------------------------------
    if b_beats_a_count == 0 and s0_pass:
        return Verdict(
            verdict="V1",
            label="Reference-only — B > A in S0 but fails in unseen/deceptive families",
            checks=checks,
            details="B generalizes to 0 unseen deceptive families",
        )

    # ------------------------------------------------------------------
    # V2: B > A in multiple unseen families, but B ≤ C
    # ------------------------------------------------------------------
    if b_beats_a_count >= 2 and b_beats_c_count == 0:
        return Verdict(
            verdict="V2",
            label="Multi-family without superiority — B > A in unseen families, B ≤ C",
            checks=checks,
            details=f"B beats A in {b_beats_a_count} unseen families but never beats C",
        )

    # ------------------------------------------------------------------
    # V3: B > A AND B > C with practical effect size
    # ------------------------------------------------------------------
    if (b_beats_a_count >= 2 and b_beats_c_count >= 1
            and avg_delta_ba >= CLIFF_SMALL):
        # V3 achieved — check for V4 upgrade
        v3_base = Verdict(
            verdict="V3",
            label="Practical superiority — B > A AND B > C with practical effect size",
            checks=checks,
            details=f"B beats A in {b_beats_a_count}, beats C in {b_beats_c_count} families, "
                    f"avg δ_BA={avg_delta_ba:.3f}",
        )
    else:
        # Didn't reach V3 — return best achievable
        if b_beats_a_count >= 1:
            return Verdict(
                verdict="V2",
                label="Partial generalization — B > A in some unseen families",
                checks=checks,
                details=f"B beats A in {b_beats_a_count} unseen families",
            )
        # Should not reach here (V0/V1 already handled), but fail-closed
        return Verdict(
            verdict="V0",
            label="Insufficient evidence — no demonstrated generalization",
            checks=checks,
        )

    # ------------------------------------------------------------------
    # V4: V3 + S8 provenance trace complete
    # ------------------------------------------------------------------
    s8 = by_scenario.get("S8", [])
    if not s8:
        checks["S8_missing"] = True
        return v3_base  # No S8 data → stay at V3

    s8_b = [r for r in s8 if r.agent == "B_hyp"]
    s8_complete = True
    s8_issues = []

    for r in s8_b:
        if r.trigger_source != "telemetry":
            s8_complete = False
            s8_issues.append(f"{r.run_id}: trigger_source={r.trigger_source}")
        if r.human_prompt_post_start:
            s8_complete = False
            s8_issues.append(f"{r.run_id}: human_prompt_post_start=True")
        if r.side_effects:
            s8_complete = False
            s8_issues.append(f"{r.run_id}: side_effects={r.side_effects}")

    checks["S8_provenance_complete"] = s8_complete
    checks["S8_issues"] = s8_issues

    if s8_complete:
        return Verdict(
            verdict="V4",
            label="Autonomously initiated bounded research — V3 + S8 provenance complete",
            checks=checks,
            details="S8 provenance trace complete without human prompt post-start, "
                    "no side effects, telemetry-initiated",
        )
    return v3_base


# ---------------------------------------------------------------------------
# Scenario-level sub-verdict (for per-scenario reporting)
# ---------------------------------------------------------------------------
def scenario_sub_verdict(records: List[RunRecord],
                         scenario_id: str) -> Dict[str, Any]:
    """Compute per-scenario sub-verdict with discovery rates, CIs, and effect sizes."""
    b_rec = [r for r in records if r.agent == "B_hyp"]
    a_rec = [r for r in records if r.agent == "A_prior"]
    c_rec = [r for r in records if r.agent == "C_novel"]

    def _stats(recs):
        disc = [1 if r.discovered else 0 for r in recs]
        ttd = [r.ttd for r in recs if r.ttd is not None]
        rate = sum(disc) / max(len(disc), 1)
        ci = _wilson_ci(sum(disc), len(disc))
        median_ttd = sorted(ttd)[len(ttd) // 2] if ttd else None
        return {"rate": rate, "ci": ci, "n": len(disc), "median_ttd": median_ttd}

    b_stats = _stats(b_rec)
    a_stats = _stats(a_rec)
    c_stats = _stats(c_rec)

    b_ttd = [r.ttd for r in b_rec if r.ttd is not None]
    a_ttd = [r.ttd for r in a_rec if r.ttd is not None]
    c_ttd = [r.ttd for r in c_rec if r.ttd is not None]

    return {
        "scenario_id": scenario_id,
        "B": b_stats,
        "A": a_stats,
        "C": c_stats,
        "delta_BA": _cliffs_delta(b_ttd, a_ttd),
        "delta_BC": _cliffs_delta(b_ttd, c_ttd),
        "B_beats_A": b_stats["rate"] > a_stats["rate"] + 0.10,
        "B_beats_C": b_stats["rate"] > c_stats["rate"] + 0.10,
    }
