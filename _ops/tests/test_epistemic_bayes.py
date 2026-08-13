#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_epistemic_bayes.py — belief update + discovery value (ADR-039 C4, Phase 2.5).

دو مسیرِ belief-update را pin می‌کند:
  ۱. Bayesian (likelihood معلوم): Δlog-odds = log(BF)، clipped
  ۲. Score-band (evidence مبهم): delta=0 — posterior تا review تغییر نمی‌کند

همچنین DiscoveryBlock (EVSI − cost − risk → net_value) و EvidenceScoreBand.
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

_OPS = Path(__file__).resolve().parents[1]
if str(_OPS) not in sys.path:
    sys.path.insert(0, str(_OPS))

import epistemics.bayes as B  # noqa: E402
from epistemics.schemas import (  # noqa: E402
    DiscoveryBlock,
    EvidenceScoreBand,
)


# ---------------------------------------------------------------------------
# Bayesian path
# ---------------------------------------------------------------------------
def t_bayes_supporting_evidence_increases_belief():
    """P(E|H) > P(E|¬H) → delta > 0."""
    d = B.update_bayesian(prior=0.5, p_e_given_h=0.8, p_e_given_not_h=0.2,
                          clip_log_odds=6.0)
    assert d.method == "bayesian"
    assert d.log_odds_delta > 0.0
    # log(0.8/0.2) = log(4) ≈ 1.386
    assert abs(d.log_odds_delta - math.log(4)) < 1e-6


def t_bayes_contradicting_evidence_decreases_belief():
    """P(E|H) < P(E|¬H) → delta < 0."""
    d = B.update_bayesian(prior=0.5, p_e_given_h=0.2, p_e_given_not_h=0.8)
    assert d.log_odds_delta < 0.0
    assert abs(d.log_odds_delta - math.log(0.25)) < 1e-6


def t_bayes_clip_bounds_delta():
    """delta هرگز از clip بیشتر نمی‌شود (حتی با Bayes factor عظیم)."""
    d = B.update_bayesian(prior=0.01, p_e_given_h=1.0, p_e_given_not_h=1e-9,
                          clip_log_odds=3.0)
    assert d.log_odds_delta <= 3.0 + 1e-9
    assert d.log_odds_delta >= -3.0 - 1e-9


def t_bayes_dogmatic_prior_rejected():
    """prior جزمیِ ۰/۱ ممنون."""
    for bad in (0.0, 1.0):
        try:
            B.update_bayesian(prior=bad, p_e_given_h=0.5, p_e_given_not_h=0.5)
            raise AssertionError(f"prior {bad} باید رد شود")
        except ValueError:
            pass


def t_bayes_invalid_likelihood_rejected():
    """likelihood نامعتبر رد می‌شود."""
    for bad in (0.0, -0.1, 1.5):
        try:
            B.update_bayesian(prior=0.5, p_e_given_h=bad, p_e_given_not_h=0.5)
            raise AssertionError(f"p_e_given_h {bad} باید رد شود")
        except ValueError:
            pass


def t_posterior_from_delta_consistency():
    """posterior ∈ (0,1) و با delta سازگار."""
    prior = 0.3
    d = B.update_bayesian(prior=prior, p_e_given_h=0.7, p_e_given_not_h=0.4)
    post = B.posterior_from_delta(prior, d)
    assert 0.0 < post < 1.0
    assert post > prior   # evidence موافق


# ---------------------------------------------------------------------------
# Score-band path — invariant #8/#9
# ---------------------------------------------------------------------------
def t_score_band_never_changes_belief():
    """evidence مبهم → delta=0 (posterior تا review تغییر نمی‌کند)."""
    for direction in ("supports", "contradicts", "ambiguous"):
        d = B.update_score_band(support_direction=direction, strength="strong")
        assert d.method == "score_band"
        assert d.log_odds_delta == 0.0, f"{direction}: delta باید صفر باشد"


def t_score_band_invalid_direction_rejected():
    """direction نامعتبر رد می‌شود."""
    try:
        B.update_score_band(support_direction="bogus", strength="weak")
        raise AssertionError("direction bogus باید رد شود")
    except ValueError:
        pass


def t_aggregate_disagreement_penalty():
    """shardهای متضاد → جریمهٔ disagreement جمع را به صفر نزدیک می‌کند."""
    d_for = B.update_bayesian(prior=0.5, p_e_given_h=0.8, p_e_given_not_h=0.2)
    d_against = B.update_bayesian(prior=0.5, p_e_given_h=0.2, p_e_given_not_h=0.8)
    # بدون جریمه: جمع صفر (متضادِ متقارن)
    agg = B.aggregate_independent([d_for, d_against], lambda_disagreement=0.5)
    assert abs(agg.log_odds_delta) < 1e-6
    # دو شاهدِ هم‌جهت → جمع می‌شود
    agg2 = B.aggregate_independent([d_for, d_for], lambda_disagreement=0.5)
    assert agg2.log_odds_delta > 0.0


def t_aggregate_empty_is_zero():
    """بدون شاهد → delta=0 (invariant #9: no-evidence != evidence-of-absence)."""
    agg = B.aggregate_independent([], lambda_disagreement=0.5)
    assert agg.log_odds_delta == 0.0


# ---------------------------------------------------------------------------
# DiscoveryBlock — invariant #2 (useful != true)
# ---------------------------------------------------------------------------
def t_discovery_net_value_computed():
    """net_value = EIG + ESV − cost − risk، محاسبه‌شده در validator."""
    db = DiscoveryBlock(expected_information_gain=0.55, expected_sample_value=0.31,
                        estimated_cost=0.06, risk_penalty=0.0)
    assert abs(db.net_value - (0.55 + 0.31 - 0.06 - 0.0)) < 1e-9


def t_discovery_negative_when_cost_dominates():
    """اگر cost/risk بزرگ‌تر از EIG باشد → net_value منفی (آزمون不值得)."""
    db = DiscoveryBlock(expected_information_gain=0.1, estimated_cost=0.5,
                        risk_penalty=0.3)
    assert db.net_value < 0.0


def t_discovery_bounds_enforced():
    """EIG/cost/risk ∈ [0,1]؛ خارج رد می‌شود."""
    try:
        DiscoveryBlock(expected_information_gain=1.5)
        raise AssertionError("EIG>1 باید رد شود")
    except Exception:
        pass


# ---------------------------------------------------------------------------
# EvidenceScoreBand model
# ---------------------------------------------------------------------------
def t_evidence_score_band_model():
    """EvidenceScoreBand: direction/strength الزامی، forbid extra."""
    esb = EvidenceScoreBand(evidence_id="e-1", support_direction="supports",
                            strength="moderate", provenance="derived")
    assert esb.support_direction == "supports"
    try:
        EvidenceScoreBand(evidence_id="e-1", support_direction="supports",
                          strength="moderate", bogus=True)  # type: ignore[call-arg]
        raise AssertionError("extra field باید forbid شود")
    except Exception:
        pass


TESTS = [
    t_bayes_supporting_evidence_increases_belief,
    t_bayes_contradicting_evidence_decreases_belief,
    t_bayes_clip_bounds_delta,
    t_bayes_dogmatic_prior_rejected,
    t_bayes_invalid_likelihood_rejected,
    t_posterior_from_delta_consistency,
    t_score_band_never_changes_belief,
    t_score_band_invalid_direction_rejected,
    t_aggregate_disagreement_penalty,
    t_aggregate_empty_is_zero,
    t_discovery_net_value_computed,
    t_discovery_negative_when_cost_dominates,
    t_discovery_bounds_enforced,
    t_evidence_score_band_model,
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
