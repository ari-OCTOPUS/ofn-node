#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_epistemic_selector_metrics.py — experiment selector + benchmark metrics.

دو ماژولِ Phase 2.5/2.6 را pin می‌کند:
  ۱. experiment_selector: SAFE_EXPERIMENTS/FORBIDDEN + eligible() fail-closed
  ۲. benchmark_metrics: Brier/calibration/leakage/UFBR + go_no_go
"""
from __future__ import annotations

import sys
from pathlib import Path

_OPS = Path(__file__).resolve().parents[1]
if str(_OPS) not in sys.path:
    sys.path.insert(0, str(_OPS))

from epistemics import experiment_selector as SEL  # noqa: E402
from epistemics import benchmark_metrics as M  # noqa: E402
from epistemics.schemas import (  # noqa: E402
    Authority, ClaimType, EpistemicClaim, ExecutionScope, Falsifier,
    Prediction, PredictionDirection, WorldMode,
)


def _claim(**over):
    base = dict(
        claim_id="CLM-1", claim_type=ClaimType.CAUSAL,
        operational_definition="B beats A on holdout.",
        competing_claim_ids=["CLM-null"],
        predictions=[Prediction(variable="discovery_rate",
                                direction=PredictionDirection.INCREASE,
                                operational_ref="holdout mean")],
        falsifier=Falsifier(description="x", operational_ref="r", metric="m",
                            threshold="t"),
        testability=0.8, prior=0.5, source_git_sha="abc1234",
        source_config_hash="deadbeefdeadbeef",
        requested_authority=Authority.PROPOSE,
        world_mode=WorldMode.HYPOTHESIS,
        execution_scope=ExecutionScope.SANDBOX_ONLY,
    )
    base.update(over)
    return EpistemicClaim(**base)


# ---------------------------------------------------------------------------
# selector — invariant #10 + safe/forbidden sets
# ---------------------------------------------------------------------------
def t_safe_and_forbidden_disjoint():
    """هیچ نوعی هم مجاز و هم ممنون نیست."""
    assert SEL.SAFE_EXPERIMENTS.isdisjoint(SEL.FORBIDDEN_EXPERIMENTS)


def t_safe_set_matches_review():
    """دقیقاً ۵ نوعِ مجازِ بازبینی."""
    assert SEL.SAFE_EXPERIMENTS == frozenset({
        "historical_replay", "fixture_query", "sandbox_simulation",
        "read_only_retrieval", "test_execution_with_mocked_tools",
    })


def t_forbidden_set_matches_review():
    """دقیقاً ۷ نوعِ ممنونِ بازبینی."""
    assert SEL.FORBIDDEN_EXPERIMENTS == frozenset({
        "network_scan", "real_world_outreach", "state_mutation",
        "credential_use", "production_tool_call", "memory_promotion",
        "policy_change",
    })


def t_eligible_happy_path():
    """claim درست + experiment درست → ok=True."""
    c = _claim()
    exp = SEL.ExperimentSpec(experiment_id="e1", type="historical_replay",
                             cost=0.1, risk_penalty=0.0,
                             has_preregistered_falsifier=True)
    d = SEL.eligible(claim=c, experiment=exp, remaining_budget=1.0)
    assert d.ok is True and d.reason == "eligible"


def t_eligible_reality_claim_rejected():
    """invariant #4: claim با world_mode=REALITY ممنون — ولی schema قبلاً ردش می‌کند.
    اینجا با simulation تست می‌کنیم (reality روی claim ساخته نمی‌شود)."""
    c = _claim(world_mode=WorldMode.SIMULATION)   # غیر hypothesis
    exp = SEL.ExperimentSpec(experiment_id="e1", type="historical_replay",
                             has_preregistered_falsifier=True)
    d = SEL.eligible(claim=c, experiment=exp)
    assert d.ok is False
    assert "world_mode" in d.reason


def t_eligible_forbidden_type_rejected():
    """network_scan همیشه رد می‌شود حتی اگر همه‌چیز درست باشد."""
    c = _claim()
    exp = SEL.ExperimentSpec(experiment_id="e1", type="network_scan",
                             has_preregistered_falsifier=True)
    d = SEL.eligible(claim=c, experiment=exp)
    assert d.ok is False and "forbidden" in d.reason


def t_eligible_unknown_type_fail_closed():
    """نوع ناشناخته → fail-closed (False)، نه True."""
    c = _claim()
    exp = SEL.ExperimentSpec(experiment_id="e1", type="bogus_replay",
                             has_preregistered_falsifier=True)
    d = SEL.eligible(claim=c, experiment=exp)
    assert d.ok is False and "unsafe" in d.reason


def t_eligible_no_falsifier_rejected():
    """آزمونِ بی‌falsifier مجاز نیست."""
    c = _claim()
    exp = SEL.ExperimentSpec(experiment_id="e1", type="historical_replay",
                             has_preregistered_falsifier=False)
    d = SEL.eligible(claim=c, experiment=exp)
    assert d.ok is False and "falsifier" in d.reason


def t_eligible_budget_exceeded():
    """cost > budget → رد."""
    c = _claim()
    exp = SEL.ExperimentSpec(experiment_id="e1", type="historical_replay",
                             cost=0.9, has_preregistered_falsifier=True)
    d = SEL.eligible(claim=c, experiment=exp, remaining_budget=0.5)
    assert d.ok is False and "budget" in d.reason


def t_eligible_risk_nonzero_rejected():
    """risk_penalty != 0 → رد."""
    c = _claim()
    exp = SEL.ExperimentSpec(experiment_id="e1", type="historical_replay",
                             risk_penalty=0.1, has_preregistered_falsifier=True)
    d = SEL.eligible(claim=c, experiment=exp)
    assert d.ok is False and "risk" in d.reason


# ---------------------------------------------------------------------------
# benchmark metrics
# ---------------------------------------------------------------------------
def _o(**k):
    base = dict(case_id="c", arm="C", predicted_prob=0.5, actual_outcome=0.0,
                claim_count=0, unsupported_claims=0, cost=0.0)
    base.update(k)
    return M.Outcome(**base)


def t_brier_perfect_is_zero():
    assert M.brier_score([_o(predicted_prob=0.0, actual_outcome=0.0)]) == 0.0


def t_brier_random_balanced():
    """p=0.5 برای 0/1 → 0.25."""
    b = M.brier_score([_o(predicted_prob=0.5, actual_outcome=0.0),
                       _o(predicted_prob=0.5, actual_outcome=1.0)])
    assert abs(b - 0.25) < 1e-9


def t_calibration_perfect_is_zero():
    os_ = [_o(predicted_prob=0.0, actual_outcome=0.0),
           _o(predicted_prob=1.0, actual_outcome=1.0)]
    assert M.calibration_error(os_, n_bins=5) == 0.0


def t_unsupported_claim_rate():
    os_ = [_o(claim_count=10, unsupported_claims=2),
           _o(claim_count=10, unsupported_claims=3)]
    assert abs(M.unsupported_claim_rate(os_) - 0.25) < 1e-9


def test_claim_precision_complement():
    os_ = [_o(claim_count=10, unsupported_claims=2)]
    assert abs(M.claim_precision(os_) - 0.8) < 1e-9


def t_ufbr_zero_pursued_is_zero():
    """صفر pursued → 0.0 (نه NaN، نه تقسیم بر صفر)."""
    assert M.ufbr([_o(pursued_false_hypotheses=0)]) == 0.0


def t_ufbr_ratio():
    os_ = [_o(pursued_false_hypotheses=10, useful_from_false=3)]
    assert abs(M.ufbr(os_) - 0.3) < 1e-9


def t_leakage_rate_zero_by_default():
    assert M.leakage_rate([_o(), _o()]) == 0.0


def t_hypothesis_churn_healthy():
    ch = M.hypothesis_churn(created=10, refuted=4, revised=3, accumulated=3)
    assert ch["disposition_ratio"] == 0.7
    assert ch["healthy"] is True


def t_hypothesis_churn_accumulation_unhealthy():
    ch = M.hypothesis_churn(created=10, refuted=0, revised=0, accumulated=50)
    assert ch["healthy"] is False


# ---------------------------------------------------------------------------
# Go/No-Go
# ---------------------------------------------------------------------------
def t_go_no_go_passes_when_c_beats_a_cleanly():
    a = [_o(arm="A", had_useful_finding=False, claim_count=10, unsupported_claims=3)]
    c = [_o(arm="C", had_useful_finding=True, claim_count=10, unsupported_claims=1,
            cost=0.5)]
    v = M.go_no_go(arm_a=a, arm_c=c, success_threshold=0.0, budget_ceiling=1.0)
    assert v.ok is True, v.reason


def t_go_no_go_fails_on_leakage():
    a = [_o(arm="A", had_useful_finding=True)]
    c = [_o(arm="C", had_useful_finding=True, claim_count=10,
            label_leakage_events=1)]
    v = M.go_no_go(arm_a=a, arm_c=c, success_threshold=0.0)
    assert v.ok is False
    assert "c_leakage_zero" in v.reason


def t_go_no_go_fails_on_external_effect():
    a = [_o(arm="A", had_useful_finding=True)]
    c = [_o(arm="C", had_useful_finding=True, had_external_effect=True)]
    v = M.go_no_go(arm_a=a, arm_c=c, success_threshold=0.0)
    assert v.ok is False
    assert "external" in v.reason


def t_go_no_go_fails_when_c_not_better_than_a():
    a = [_o(arm="A", had_useful_finding=True)]
    c = [_o(arm="C", had_useful_finding=False)]
    v = M.go_no_go(arm_a=a, arm_c=c, success_threshold=0.5)
    assert v.ok is False
    assert "threshold" in v.reason or "delta" in v.reason


TESTS = [
    t_safe_and_forbidden_disjoint,
    t_safe_set_matches_review,
    t_forbidden_set_matches_review,
    t_eligible_happy_path,
    t_eligible_reality_claim_rejected,
    t_eligible_forbidden_type_rejected,
    t_eligible_unknown_type_fail_closed,
    t_eligible_no_falsifier_rejected,
    t_eligible_budget_exceeded,
    t_eligible_risk_nonzero_rejected,
    t_brier_perfect_is_zero,
    t_brier_random_balanced,
    t_calibration_perfect_is_zero,
    t_unsupported_claim_rate,
    test_claim_precision_complement,
    t_ufbr_zero_pursued_is_zero,
    t_ufbr_ratio,
    t_leakage_rate_zero_by_default,
    t_hypothesis_churn_healthy,
    t_hypothesis_churn_accumulation_unhealthy,
    t_go_no_go_passes_when_c_beats_a_cleanly,
    t_go_no_go_fails_on_leakage,
    t_go_no_go_fails_on_external_effect,
    t_go_no_go_fails_when_c_not_better_than_a,
]

if __name__ == "__main__":
    failed = 0
    for _t in TESTS:
        try:
            _t()
            print(f"  PASS  {_t.__name__}")
        except Exception as exc:
            print(f"  FAIL  {_t.__name__}: {exc}")
            failed += 1
    print(f"\n{len(TESTS) - failed}/{len(TESTS)} passed")
    sys.exit(failed)
