#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""kalman_shadow_pipeline.py — Shadow-Control observer for period estimates.

Read-only. Never mutates production_control_law state / never overrides period.
UNKNOWN / errors → None shadow fields (not fake zeros).
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from math import isfinite
from typing import Any, Protocol


@dataclass(frozen=True)
class ShadowTick:
    run_id: str
    tick: int
    production_period: float
    shadow_period: float | None
    absolute_delta: float | None
    relative_delta: float | None
    status: str
    evidence_level: str = "SHADOW"

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


class PeriodEstimator(Protocol):
    def step(self, observation: float) -> Any: ...


class ProductionControlLaw(Protocol):
    def compute_period(self, observation: float) -> float: ...


class KalmanShadowPipeline:
    """Read-only observer. Never mutates production_control_law state."""

    def __init__(
        self,
        kalman_estimator: PeriodEstimator,
        production_control_law: ProductionControlLaw,
    ) -> None:
        self.estimator = kalman_estimator
        self.production = production_control_law

    def tick(self, run_id: str, tick_index: int, observation: float) -> ShadowTick:
        production_period = float(self.production.compute_period(observation))

        try:
            estimate = self.estimator.step(observation)
        except Exception:
            return ShadowTick(
                run_id,
                tick_index,
                production_period,
                None,
                None,
                None,
                "ESTIMATOR_ERROR",
            )

        period = getattr(estimate, "period", None)
        if period is None or not isfinite(float(period)) or float(period) <= 0:
            return ShadowTick(
                run_id,
                tick_index,
                production_period,
                None,
                None,
                None,
                "INVALID_ESTIMATE",
            )

        shadow = float(period)
        delta = abs(shadow - production_period)
        rel = delta / production_period if production_period else None
        return ShadowTick(
            run_id,
            tick_index,
            production_period,
            shadow,
            delta,
            rel,
            "OK",
        )

    def run(self, run_id: str, observations: list[float]) -> list[ShadowTick]:
        return [self.tick(run_id, i, obs) for i, obs in enumerate(observations)]
