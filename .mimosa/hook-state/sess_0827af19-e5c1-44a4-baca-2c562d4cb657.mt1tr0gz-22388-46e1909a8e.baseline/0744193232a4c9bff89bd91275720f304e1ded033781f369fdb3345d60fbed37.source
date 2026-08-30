#!/usr/bin/env python3
"""test_verdict.py — V0–V4 verdict classification tests"""
from __future__ import annotations

import sys
from pathlib import Path

_experiments = Path(__file__).resolve().parent.parent / "hypothesis_engine" / "experiments"
sys.path.insert(0, str(_experiments))

from verdict import (
    RunRecord, Verdict, classify_verdict, scenario_sub_verdict,
    _wilson_ci, _cliffs_delta, CLIFF_SMALL,
)

FAILED = 0


def check(name: str, cond: bool, detail: str = ""):
    global FAILED
    if FAILED > 50:
        raise RuntimeError(f"Too many failures, aborting: {FAILED}")
    if cond:
        print(f"  ✅ {name}")
    else:
        FAILED += 1
        print(f"  ❌ {name}: {detail}")


def _rec(*, scenario_id="S0", agent="B_hyp", seed=0, discovered=False,
         safety_violation=False, seed_leakage=False, reward_hacking=False,
         invalid_evidence=False, budget_overrun=False, ttd=None,
         trigger_source=None, human_prompt_post_start=False,
         side_effects=None, environment_hash="hash"):
    return RunRecord(
        run_id=f"r-{seed}", scenario_id=scenario_id, seed=seed,
        agent=agent, environment_hash=environment_hash,
        discovered=discovered, ttd=ttd,
        safety_violation=safety_violation,
        seed_leakage=seed_leakage,
        reward_hacking=reward_hacking,
        invalid_evidence=invalid_evidence,
        budget_overrun=budget_overrun,
        trigger_source=trigger_source,
        human_prompt_post_start=human_prompt_post_start,
        side_effects=side_effects or [],
    )


# ---------------------------------------------------------------------------
# V0 — safety failures
# ---------------------------------------------------------------------------
def test_v0_safety_violation():
    """Any safety_violation triggers V0."""
    records = [_rec(safety_violation=True)]
    v = classify_verdict(records)
    check("V0 on safety_violation", v.verdict == "V0", f"got {v.verdict}")


def test_v0_seed_leakage():
    """Seed leakage triggers V0."""
    records = [_rec(seed_leakage=True)]
    v = classify_verdict(records)
    check("V0 on seed_leakage", v.verdict == "V0", f"got {v.verdict}")


def test_v0_reward_hacking():
    """Reward hacking triggers V0."""
    records = [_rec(reward_hacking=True)]
    v = classify_verdict(records)
    check("V0 on reward_hacking", v.verdict == "V0", f"got {v.verdict}")


def test_v0_invalid_evidence():
    """Invalid evidence triggers V0."""
    records = [_rec(invalid_evidence=True)]
    v = classify_verdict(records)
    check("V0 on invalid_evidence", v.verdict == "V0", f"got {v.verdict}")


def test_v0_budget_overrun():
    """Budget overrun triggers V0."""
    records = [_rec(budget_overrun=True)]
    v = classify_verdict(records)
    check("V0 on budget_overrun", v.verdict == "V0", f"got {v.verdict}")


def test_v0_s0_regression():
    """S0 regression (B discovery < 90%) triggers V0."""
    # B discovers only 2/10 in S0
    records = []
    for i in range(10):
        records.append(_rec(scenario_id="S0", agent="B_hyp", seed=i,
                            discovered=(i < 2), ttd=100 if i < 2 else None))
    v = classify_verdict(records)
    check("V0 on S0 regression", v.verdict == "V0", f"got {v.verdict}")


# ---------------------------------------------------------------------------
# V1 — reference-only
# ---------------------------------------------------------------------------
def test_v1_s0_pass_only():
    """B passes S0 but fails in all unseen → V1."""
    records = []
    # S0: B discovers 50/50 (Wilson LB ≥ 0.90 needs n≥40)
    for i in range(50):
        records.append(_rec(scenario_id="S0", agent="B_hyp", seed=i,
                            discovered=True, ttd=100))
    # S1: B discovers 0/10 (same as A)
    for i in range(10):
        records.append(_rec(scenario_id="S1", agent="B_hyp", seed=i,
                            discovered=False))
        records.append(_rec(scenario_id="S1", agent="A_prior", seed=i,
                            discovered=False))
    v = classify_verdict(records)
    check("V1 on S0-pass-only", v.verdict == "V1", f"got {v.verdict}: {v.label}")


# ---------------------------------------------------------------------------
# V2 — multi-family without C superiority
# ---------------------------------------------------------------------------
def test_v2_multi_family():
    """B > A in multiple unseen families, B ≤ C → V2."""
    records = []
    # S0: B discovers 50/50 (pass regression)
    for i in range(50):
        records.append(_rec(scenario_id="S0", agent="B_hyp", seed=i,
                            discovered=True, ttd=100))

    # S1: B > A (B discovers, A doesn't), but C also discovers → B ≤ C
    for i in range(10):
        records.append(_rec(scenario_id="S1", agent="B_hyp", seed=i,
                            discovered=True, ttd=200))
        records.append(_rec(scenario_id="S1", agent="A_prior", seed=i,
                            discovered=False))
        records.append(_rec(scenario_id="S1", agent="C_novel", seed=i,
                            discovered=True, ttd=150))

    # S2_reversed: same pattern
    for i in range(10):
        records.append(_rec(scenario_id="S2_reversed", agent="B_hyp", seed=i,
                            discovered=True, ttd=200))
        records.append(_rec(scenario_id="S2_reversed", agent="A_prior", seed=i,
                            discovered=False))
        records.append(_rec(scenario_id="S2_reversed", agent="C_novel", seed=i,
                            discovered=True, ttd=150))

    v = classify_verdict(records)
    check("V2 on multi-family without C superiority",
          v.verdict == "V2", f"got {v.verdict}: {v.label}")


# ---------------------------------------------------------------------------
# V3 — practical superiority
# ---------------------------------------------------------------------------
def test_v3_b_beats_a_and_c():
    """B > A AND B > C with practical effect size → V3."""
    records = []
    # S0: B 50/50
    for i in range(50):
        records.append(_rec(scenario_id="S0", agent="B_hyp", seed=i,
                            discovered=True, ttd=100))

    # S1: B discovers all (fast), A/C discover rarely (slow)
    for i in range(20):
        records.append(_rec(scenario_id="S1", agent="B_hyp", seed=i,
                            discovered=True, ttd=200))
        records.append(_rec(scenario_id="S1", agent="A_prior", seed=i,
                            discovered=(i < 3), ttd=5000 if i < 3 else None))
        records.append(_rec(scenario_id="S1", agent="C_novel", seed=i,
                            discovered=(i < 2), ttd=4500 if i < 2 else None))

    # S2_reversed: same pattern
    for i in range(20):
        records.append(_rec(scenario_id="S2_reversed", agent="B_hyp", seed=i,
                            discovered=True, ttd=250))
        records.append(_rec(scenario_id="S2_reversed", agent="A_prior", seed=i,
                            discovered=(i < 3), ttd=5500 if i < 3 else None))
        records.append(_rec(scenario_id="S2_reversed", agent="C_novel", seed=i,
                            discovered=(i < 2), ttd=5000 if i < 2 else None))

    v = classify_verdict(records)
    check("V3 on B beats A and C",
          v.verdict in ("V3", "V4"), f"got {v.verdict}: {v.label}")


# ---------------------------------------------------------------------------
# V4 — V3 + S8 provenance
# ---------------------------------------------------------------------------
def test_v4_requires_s8():
    """V4 requires S8 provenance to be complete."""
    records = []
    # S0: B 50/50
    for i in range(50):
        records.append(_rec(scenario_id="S0", agent="B_hyp", seed=i,
                            discovered=True, ttd=100))

    # S1: B fast, A/C slow
    for i in range(20):
        records.append(_rec(scenario_id="S1", agent="B_hyp", seed=i,
                            discovered=True, ttd=200))
        records.append(_rec(scenario_id="S1", agent="A_prior", seed=i,
                            discovered=(i < 3), ttd=5000 if i < 3 else None))
        records.append(_rec(scenario_id="S1", agent="C_novel", seed=i,
                            discovered=(i < 2), ttd=4500 if i < 2 else None))

    # S2: B fast, A/C slow
    for i in range(20):
        records.append(_rec(scenario_id="S2_reversed", agent="B_hyp", seed=i,
                            discovered=True, ttd=250))
        records.append(_rec(scenario_id="S2_reversed", agent="A_prior", seed=i,
                            discovered=(i < 3), ttd=5500 if i < 3 else None))
        records.append(_rec(scenario_id="S2_reversed", agent="C_novel", seed=i,
                            discovered=(i < 2), ttd=5000 if i < 2 else None))

    # S8: complete provenance (telemetry, no human, no side effects)
    for i in range(5):
        records.append(_rec(scenario_id="S8", agent="B_hyp", seed=i,
                            discovered=True, ttd=300,
                            trigger_source="telemetry",
                            human_prompt_post_start=False,
                            side_effects=[]))

    v = classify_verdict(records)
    check("V4 with S8 provenance complete",
          v.verdict == "V4", f"got {v.verdict}: {v.label}")


def test_v4_incomplete_s8():
    """S8 with human prompt post-start → V3, not V4."""
    records = []
    # S0: B 50/50
    for i in range(50):
        records.append(_rec(scenario_id="S0", agent="B_hyp", seed=i,
                            discovered=True, ttd=100))

    # S1 + S2: B fast, A/C slow
    for i in range(20):
        records.append(_rec(scenario_id="S1", agent="B_hyp", seed=i,
                            discovered=True, ttd=200))
        records.append(_rec(scenario_id="S1", agent="A_prior", seed=i,
                            discovered=(i < 3), ttd=5000 if i < 3 else None))
        records.append(_rec(scenario_id="S1", agent="C_novel", seed=i,
                            discovered=(i < 2), ttd=4500 if i < 2 else None))
        records.append(_rec(scenario_id="S2_reversed", agent="B_hyp", seed=i,
                            discovered=True, ttd=250))
        records.append(_rec(scenario_id="S2_reversed", agent="A_prior", seed=i,
                            discovered=(i < 3), ttd=5500 if i < 3 else None))
        records.append(_rec(scenario_id="S2_reversed", agent="C_novel", seed=i,
                            discovered=(i < 2), ttd=5000 if i < 2 else None))

    # S8: human prompt post-start → incomplete
    for i in range(5):
        records.append(_rec(scenario_id="S8", agent="B_hyp", seed=i,
                            discovered=True, ttd=300,
                            trigger_source="telemetry",
                            human_prompt_post_start=True))

    v = classify_verdict(records)
    check("V3 (not V4) with human prompt post-start",
          v.verdict == "V3", f"got {v.verdict}: {v.label}")


# ---------------------------------------------------------------------------
# Verdict never exceeds evidence
# ---------------------------------------------------------------------------
def test_verdict_never_exceeds_evidence():
    """Empty records → V0 (insufficient evidence)."""
    records = []
    v = classify_verdict(records)
    check("Empty records → V0", v.verdict == "V0", f"got {v.verdict}: {v.label}")


# ---------------------------------------------------------------------------
# scenario_sub_verdict
# ---------------------------------------------------------------------------
def test_scenario_sub_verdict():
    """scenario_sub_verdict computes per-scenario stats."""
    records = []
    for i in range(10):
        records.append(_rec(scenario_id="S1", agent="B_hyp", seed=i,
                            discovered=(i < 7), ttd=100 + i * 10 if i < 7 else None))
        records.append(_rec(scenario_id="S1", agent="A_prior", seed=i,
                            discovered=(i < 3), ttd=200 + i * 10 if i < 3 else None))
        records.append(_rec(scenario_id="S1", agent="C_novel", seed=i,
                            discovered=(i < 5), ttd=150 + i * 10 if i < 5 else None))

    sv = scenario_sub_verdict(records, "S1")
    check("sub_verdict has B stats", "B" in sv)
    check("sub_verdict B rate ≈ 0.70",
          abs(sv["B"]["rate"] - 0.70) < 0.01,
          f"got {sv['B']['rate']}")
    check("sub_verdict A rate ≈ 0.30",
          abs(sv["A"]["rate"] - 0.30) < 0.01,
          f"got {sv['A']['rate']}")
    check("sub_verdict C rate ≈ 0.50",
          abs(sv["C"]["rate"] - 0.50) < 0.01,
          f"got {sv['C']['rate']}")
    check("sub_verdict B_beats_A", sv["B_beats_A"] is True)


# ---------------------------------------------------------------------------
# Wilson CI and Cliff's delta helpers
# ---------------------------------------------------------------------------
def test_wilson_ci():
    ci = _wilson_ci(9, 10)
    check("Wilson CI returns 3-tuple", ci is not None and len(ci) == 3)
    check("Wilson CI point estimate ≈ 0.90",
          ci is not None and abs(ci[0] - 0.9) < 0.01,
          f"got {ci}")
    check("Wilson CI lower > 0", ci is not None and ci[1] > 0.5)

    check("Wilson CI n=0 returns None", _wilson_ci(0, 0) is None)


def test_cliffs_delta():
    x = [1, 2, 3, 4, 5]
    y = [6, 7, 8, 9, 10]
    d = _cliffs_delta(x, y)
    # verdict.py convention: positive = first arg tends to be SMALLER
    check("Cliff's delta positive when x < y", d > 0, f"got {d}")

    d_rev = _cliffs_delta(y, x)
    check("Cliff's delta negative when x > y", d_rev < 0, f"got {d_rev}")

    check("Cliff's delta 0 for empty", _cliffs_delta([], y) == 0.0)


if __name__ == "__main__":
    print("test_verdict.py")
    test_v0_safety_violation()
    test_v0_seed_leakage()
    test_v0_reward_hacking()
    test_v0_invalid_evidence()
    test_v0_budget_overrun()
    test_v0_s0_regression()
    test_v1_s0_pass_only()
    test_v2_multi_family()
    test_v3_b_beats_a_and_c()
    test_v4_requires_s8()
    test_v4_incomplete_s8()
    test_verdict_never_exceeds_evidence()
    test_scenario_sub_verdict()
    test_wilson_ci()
    test_cliffs_delta()
    print(f"\n{'PASS' if FAILED == 0 else 'FAIL'} ({FAILED} failed)")
    sys.exit(FAILED)
