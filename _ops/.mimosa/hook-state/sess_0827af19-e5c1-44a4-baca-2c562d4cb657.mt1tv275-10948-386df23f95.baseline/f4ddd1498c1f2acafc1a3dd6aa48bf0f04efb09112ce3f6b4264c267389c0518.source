#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_kalman_shadow_pipeline.py — shadow period never overrides production."""
from __future__ import annotations

import math
import sys
from pathlib import Path
from types import SimpleNamespace

_OPS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_OPS))
sys.path.insert(0, str(_OPS / "tests"))

import harness  # noqa: E402
from heart.kalman_shadow_pipeline import KalmanShadowPipeline  # noqa: E402


class FakeEstimator:
    def __init__(self, periods):
        self._periods = iter(periods)

    def step(self, observation):
        return SimpleNamespace(period=next(self._periods))


class FakeProduction:
    def compute_period(self, observation):
        return 60.0


def t_shadow_never_overrides_production():
    pipeline = KalmanShadowPipeline(FakeEstimator([61.0]), FakeProduction())
    tick = pipeline.tick("run-1", 0, observation=1.0)
    assert tick.production_period == 60.0
    assert tick.shadow_period == 61.0
    assert tick.status == "OK"
    assert tick.evidence_level == "SHADOW"


def t_invalid_estimate_marked_not_crashed():
    pipeline = KalmanShadowPipeline(FakeEstimator([math.nan]), FakeProduction())
    tick = pipeline.tick("run-1", 0, observation=1.0)
    assert tick.status == "INVALID_ESTIMATE"
    assert tick.shadow_period is None


def t_estimator_exception_is_isolated():
    class BrokenEstimator:
        def step(self, observation):
            raise RuntimeError("boom")

    pipeline = KalmanShadowPipeline(BrokenEstimator(), FakeProduction())
    tick = pipeline.tick("run-1", 0, observation=1.0)
    assert tick.status == "ESTIMATOR_ERROR"


CHECKS = [
    ("shadow-never-overrides", t_shadow_never_overrides_production),
    ("invalid-estimate", t_invalid_estimate_marked_not_crashed),
    ("estimator-exception", t_estimator_exception_is_isolated),
]

failed = harness.run(CHECKS)
sys.exit(1 if failed else 0)
