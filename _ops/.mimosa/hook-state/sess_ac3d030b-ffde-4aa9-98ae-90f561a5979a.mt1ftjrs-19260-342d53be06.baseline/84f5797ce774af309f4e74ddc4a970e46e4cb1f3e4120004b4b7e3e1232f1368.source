#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""criticality_metrics.py — OTLP metrics → Grafana Alloy (local), never Grafana cloud creds.

Uses OTEL_EXPORTER_OTLP_METRICS_ENDPOINT (default http://127.0.0.1:4318/v1/metrics).
No Authorization headers in code. Fail-soft if SDK/endpoint unavailable.
"""
from __future__ import annotations

import os
from typing import Any

_FLAG = "OCTOPUS_WIRE_CRITICALITY_OTLP"  # default OFF

_meter = None
_gauges: dict[str, Any] = {}


def _enabled() -> bool:
    return os.environ.get(_FLAG, "0") == "1"


def configure_criticality_meter():
    """Configure meter provider exporting to Alloy via OTLP/HTTP. No Grafana secrets."""
    global _meter, _gauges
    if not _enabled():
        return None
    try:
        from opentelemetry import metrics
        from opentelemetry.exporter.otlp.proto.http.metric_exporter import (
            OTLPMetricExporter,
        )
        from opentelemetry.sdk.metrics import MeterProvider
        from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
        from opentelemetry.sdk.resources import Resource
    except ImportError:
        return None

    # Endpoint from env only — never bake cloud credentials.
    endpoint = os.environ.get(
        "OTEL_EXPORTER_OTLP_METRICS_ENDPOINT",
        "http://127.0.0.1:4318/v1/metrics",
    )
    # Refuse non-local endpoints unless explicitly allowed (safety).
    allow_remote = os.environ.get("OCTOPUS_OTLP_ALLOW_REMOTE", "0") == "1"
    if (not allow_remote) and ("127.0.0.1" not in endpoint) and ("localhost" not in endpoint):
        return None

    exporter = OTLPMetricExporter(endpoint=endpoint)
    reader = PeriodicExportingMetricReader(
        exporter, export_interval_millis=15_000, export_timeout_millis=5_000
    )
    provider = MeterProvider(
        resource=Resource.create({
            "service.name": os.environ.get("OTEL_SERVICE_NAME", "octopus-ai-core"),
            "octopus.component": "criticality-v2",
            "deployment.environment": "shadow",
        }),
        metric_readers=[reader],
    )
    metrics.set_meter_provider(provider)
    _meter = metrics.get_meter("octopus.criticality", "1.0.0")
    _gauges = {
        "c_t": _meter.create_gauge("octopus.criticality.c_t"),
        "radius": _meter.create_gauge("octopus.spectral.radius"),
        "lambda2": _meter.create_gauge("octopus.spectral.lambda2"),
        "sigma": _meter.create_gauge("octopus.spectral.heuristic_sigma"),
        "divergence": _meter.create_gauge("octopus.pulse.shadow_divergence_pct"),
    }
    return _meter


def emit_criticality(snapshot: Any, *, graph_version: str, confidence: str) -> None:
    """Emit gauges. Attributes: versioned ids only — never DM/prompt/context."""
    if not _enabled():
        return
    if not _gauges:
        configure_criticality_meter()
    if not _gauges:
        return
    attrs = {
        "octopus.graph_version": graph_version,
        "octopus.evidence_level": "SHADOW",
        "octopus.confidence": confidence,
    }
    try:
        # UNKNOWN must not be coerced to 0.0 — skip gauge when value is None.
        def _set(name: str, value: Any) -> None:
            if value is None:
                return
            _gauges[name].set(float(value), attrs)

        _set("c_t", getattr(snapshot, "c_t", None))
        _set("radius", getattr(snapshot, "spectral_radius", None))
        _set("lambda2", getattr(snapshot, "lambda_2", None))
        sigma = getattr(snapshot, "spectral_heuristic", None)
        if sigma is None:
            sigma = getattr(snapshot, "sigma_heuristic", None)
        _set("sigma", sigma)
    except Exception:  # noqa: BLE001
        pass


def emit_shadow_divergence(pct: float, *, run_id: str = "") -> None:
    if not _enabled() or not _gauges:
        return
    try:
        _gauges["divergence"].set(
            float(pct),
            {
                "octopus.evidence_level": "SHADOW",
                "octopus.run_id": (run_id or "")[:32],
            },
        )
    except Exception:  # noqa: BLE001
        pass
