#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_nociceptor_chaos_shadow.py — pain chaos without Toxiproxy / production wire."""
from __future__ import annotations

import math
import sys
from pathlib import Path

_OPS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_OPS))
sys.path.insert(0, str(_OPS / "tests"))

import harness  # noqa: E402
from signals.shadow_channels import PainChaosRuntime  # noqa: E402


def t_pain_bounded_under_extreme_inputs():
    rt = PainChaosRuntime()
    result = rt.inject_pain(
        budget_pct=1.5,
        error_rate=5.0,
        freeze_active=1,
        partner_stress=3.0,
        afferent_ratio=-1.0,
        sigma=10.0,
    )
    assert result.pain is not None and 0.0 <= result.pain <= 1.0
    assert result.external_effects == ()


def t_nan_input_yields_unknown():
    rt = PainChaosRuntime()
    result = rt.inject_pain(sigma=math.nan)
    assert result.status == "UNKNOWN"
    assert result.decision_influence == "none"


def t_high_pain_only_proposes():
    rt = PainChaosRuntime()
    # Need enough weighted terms to clear historical protective θ≈0.7
    result = rt.inject_pain(
        freeze_active=1,
        budget_pct=1.0,
        error_rate=1.0,
        partner_stress=1.0,
        sigma=1.0,
    )
    assert result.pain is not None and result.pain > 0.7
    assert result.action_taken == "protective_proposal"
    assert result.route_changed is False
    assert result.tool_called is False


def t_kill_switch_blocks():
    rt = PainChaosRuntime()
    rt.inject_pain(freeze_active=1)
    rt.engage_kill_switch()
    result = rt.attempt_next_transition()
    assert result.decision == "block"


def t_redis_unavailable_fails_closed():
    rt = PainChaosRuntime()
    rt.simulate_dependency_down("redis")
    result = rt.attempt_next_transition()
    assert result.decision == "block"
    assert result.reason_code == "state_store_unavailable"


def t_scenario_replay_deterministic():
    rt = PainChaosRuntime()
    r1 = rt.run_scenario("event-storm", seed=47)
    r2 = rt.run_scenario("event-storm", seed=47)
    assert r1.trace_digest == r2.trace_digest


CHECKS = [
    ("pain-bounded", t_pain_bounded_under_extreme_inputs),
    ("pain-nan-unknown", t_nan_input_yields_unknown),
    ("pain-proposal-only", t_high_pain_only_proposes),
    ("kill-switch-block", t_kill_switch_blocks),
    ("redis-down-block", t_redis_unavailable_fails_closed),
    ("scenario-deterministic", t_scenario_replay_deterministic),
]

failed = harness.run(CHECKS)
sys.exit(1 if failed else 0)
