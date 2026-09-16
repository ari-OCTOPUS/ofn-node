#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""sog_metrics_v2.py — SOG/DARE gauges via one OTel multi-instrument callback.

Observation only. No Grafana credentials. No DM/prompt attributes.
Fail-soft if OpenTelemetry SDK missing or OTLP flag off.
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from threading import Lock
from typing import Any


@dataclass(frozen=True)
class SOGSnapshot:
    posterior_variance: float
    kalman_gain: float
    informed_floor: float
    blind_floor: float
    self_information: float
    shadow_information: float
    theory_empirical_abs_error: float
    rho: float
    mc_gate_passed: bool
    evidence_level: str = "LOCKED"


class SOGTelemetry:
    def __init__(self) -> None:
        self._lock = Lock()
        self._latest: SOGSnapshot | None = None
        self._enabled = os.environ.get("OCTOPUS_WIRE_CRITICALITY_OTLP", "0") == "1"
        self._meter_ok = False
        self.gate_pass = None
        self.gate_fail = None
        if self._enabled:
            self._wire()

    def _wire(self) -> None:
        try:
            from opentelemetry import metrics
            from opentelemetry.sdk.metrics import MeterProvider
            from opentelemetry.sdk.resources import Resource

            # Prefer existing global provider; otherwise set a no-reader stub.
            try:
                meter = metrics.get_meter("octopus.sog", "1.0.0")
            except Exception:
                metrics.set_meter_provider(
                    MeterProvider(
                        resource=Resource.create({"service.name": "octopus-ai-core"})
                    )
                )
                meter = metrics.get_meter("octopus.sog", "1.0.0")

            self.posterior_variance = meter.create_observable_gauge(
                "octopus.sog.posterior_variance", unit="1"
            )
            self.kalman_gain = meter.create_observable_gauge(
                "octopus.sog.kalman_gain", unit="1"
            )
            self.informed_floor = meter.create_observable_gauge(
                "octopus.sog.informed_floor", unit="1"
            )
            self.blind_floor = meter.create_observable_gauge(
                "octopus.sog.blind_floor", unit="1"
            )
            self.self_information = meter.create_observable_gauge(
                "octopus.sog.self_information_nat_per_step", unit="1"
            )
            self.shadow_information = meter.create_observable_gauge(
                "octopus.sog.shadow_information_nat_per_step", unit="1"
            )
            self.theory_error = meter.create_observable_gauge(
                "octopus.sog.theory_empirical_abs_error", unit="1"
            )
            self.rho = meter.create_observable_gauge("octopus.dare.rho", unit="1")

            # API differs across OTel versions — try register_callback then skip.
            instruments = [
                self.posterior_variance,
                self.kalman_gain,
                self.informed_floor,
                self.blind_floor,
                self.self_information,
                self.shadow_information,
                self.theory_error,
                self.rho,
            ]
            if hasattr(meter, "register_callback"):
                meter.register_callback(self._observe_all, instruments)
            self.gate_pass = meter.create_counter(
                "octopus.sog.mc_gate_pass_total", unit="{gate}"
            )
            self.gate_fail = meter.create_counter(
                "octopus.sog.mc_gate_fail_total", unit="{gate}"
            )
            self._meter_ok = True
        except Exception:
            self._meter_ok = False

    def update(self, snapshot: SOGSnapshot) -> None:
        with self._lock:
            self._latest = snapshot
        if not self._meter_ok:
            return
        attrs = {"octopus.evidence_level": snapshot.evidence_level}
        try:
            ctr = self.gate_pass if snapshot.mc_gate_passed else self.gate_fail
            if ctr is not None:
                ctr.add(1, attrs)
        except Exception:
            pass

    def _observe_all(self, options) -> None:
        """OTel callback — signature varies; keep duck-typed."""
        with self._lock:
            snapshot = self._latest
        if snapshot is None:
            return
        attrs = {"octopus.evidence_level": snapshot.evidence_level}
        try:
            # Newer API: options.observe(instrument, value, attrs)
            observe = getattr(options, "observe", None)
            if observe is None:
                return
            observe(self.posterior_variance, snapshot.posterior_variance, attrs)
            observe(self.kalman_gain, snapshot.kalman_gain, attrs)
            observe(self.informed_floor, snapshot.informed_floor, attrs)
            observe(self.blind_floor, snapshot.blind_floor, attrs)
            observe(self.self_information, snapshot.self_information, attrs)
            observe(self.shadow_information, snapshot.shadow_information, attrs)
            observe(self.theory_error, snapshot.theory_empirical_abs_error, attrs)
            observe(self.rho, snapshot.rho, attrs)
        except Exception:
            pass

    def latest(self) -> SOGSnapshot | None:
        with self._lock:
            return self._latest


def snapshot_from_sog_math(
    *,
    rho: float = 0.9,
    lam: float = 1.0,
    se: float = 1.0,
    sz: float = 1.0,
    sd: float = 0.5,
) -> SOGSnapshot:
    """Build snapshot from heart.sog_math primitives (read-only)."""
    from heart import sog_math as sm

    fl = sm.solve_floors(rho, lam, se, sz, sd)
    P_closed = sm.p_closed(rho, lam, se * se, sz * sz)
    P_iter = sm.p_iter(rho, lam, se * se, sz * sz)
    return SOGSnapshot(
        posterior_variance=float(fl["P"]),
        kalman_gain=float(fl["K"]),
        informed_floor=float(fl["S"]),
        blind_floor=float(fl["S_b"]),
        self_information=float(sm.delta_self(fl)),
        shadow_information=float(sm.e_shadow(fl)),
        theory_empirical_abs_error=abs(P_closed - P_iter),
        rho=float(rho),
        mc_gate_passed=abs(P_closed - P_iter) < 1e-6,
        evidence_level="LOCKED",
    )
