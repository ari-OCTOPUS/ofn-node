#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""criticality_v2.py — SHADOW-only composite criticality C_t.

C_t = clip01(w_r * ρ̃_A + w_v * Var(Δa)̃ + w_s * σ̃)

σ is explicitly named spectral_heuristic (legacy doctor/spectral sense).
Read-only. Never gates, writes organism period, or invokes tools/effectors.
Traces append to state/criticality/criticality-v2.jsonl (component scores kept).
"""
from __future__ import annotations

import json
import os
import time
from collections import deque
from dataclasses import asdict, dataclass
from math import isfinite
from pathlib import Path
from typing import Any

_HERE = Path(__file__).resolve().parent
_OPS = _HERE.parent
# 2026-08-23 — همان اصلاحِ `chat_log.py` در همین batch: مسیر باید
# `OCTOPUS_STATE_DIR` را ببیند وگرنه هر تستی که این ماژول را لمس کند در
# `_ops/state/criticality/criticality-v2.jsonl` ِ **tracked** می‌نویسد.
# پیش‌فرض بایت‌به‌بایت همان مسیرِ قبلی است ⇒ رفتارِ تولیدی بدونِ این env
# تغییر نمی‌کند. قرارداد مشترک با run_store/memory_formation/brain_pulse.
_STATE = Path(os.environ.get("OCTOPUS_STATE_DIR", str(_OPS / "state")))
_TRACE = _STATE / "criticality" / "criticality-v2.jsonl"
VERSION = "criticality_v2.v1"

try:
    import networkx as nx
    import numpy as np
    _HAS_GRAPH = True
except ImportError:  # pragma: no cover
    nx = None  # type: ignore
    np = None  # type: ignore
    _HAS_GRAPH = False


@dataclass(frozen=True)
class CriticalitySnapshot:
    spectral_radius: float | None
    activity_variance: float
    spectral_heuristic: float | None  # σ legacy -- None = UNKNOWN (not 0.0)
    lambda_2: float | None
    lambda_max: float | None
    c_t: float | None
    confidence: str
    connectivity_ratio_v2: float | None = None  # v2 ratio; None when meaningless
    node_count: int = 0
    edge_count: int = 0
    evidence_level: str = "SHADOW"
    measurement_status: str = "OK"  # OK | PARTIAL | UNKNOWN
    version: str = VERSION

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)

    def metrics(self) -> dict[str, float | int | str | None]:
        """Export names suitable for OTLP mapping. None = UNKNOWN, never fake zero."""
        return {
            "octopus.spectral.radius": self.spectral_radius,
            "octopus.spectral.lambda2": self.lambda_2,
            "octopus.spectral.lambda_max": self.lambda_max,
            "octopus.spectral.sigma_legacy": self.spectral_heuristic,
            "octopus.spectral.heuristic_sigma": self.spectral_heuristic,
            "octopus.spectral.connectivity_ratio_v2": self.connectivity_ratio_v2,
            "octopus.criticality.c_t": self.c_t,
            "octopus.criticality.confidence": self.confidence,
            "octopus.criticality.measurement_status": self.measurement_status,
            "octopus.graph.node_count": self.node_count,
            "octopus.graph.edge_count": self.edge_count,
        }


class CriticalityV2:
    """Read-only. Never gates, writes ledger, or invokes tools."""

    def __init__(
        self,
        window: int = 32,
        eps: float = 1e-9,
        weights: tuple[float, float, float] = (1 / 3, 1 / 3, 1 / 3),
    ) -> None:
        if window < 4 or len(weights) != 3 or abs(sum(weights) - 1.0) > 1e-9:
            raise ValueError("invalid criticality configuration")
        self.window = window
        self.eps = eps
        self.weights = weights
        self.activity: deque[float] = deque(maxlen=window)

    @staticmethod
    def _clip01(x: float) -> float:
        return max(0.0, min(1.0, x)) if isfinite(x) else 1.0

    def observe(self, graph: Any, activity_count: int) -> CriticalitySnapshot:
        self.activity.append(float(activity_count))

        if not _HAS_GRAPH:
            return CriticalitySnapshot(
                spectral_radius=None, activity_variance=0.0, spectral_heuristic=None,
                lambda_2=None, lambda_max=None, c_t=None, confidence="NONE",
                measurement_status="UNKNOWN",
            )

        n = int(graph.number_of_nodes())
        m = int(graph.number_of_edges())
        if n < 2:
            return CriticalitySnapshot(
                spectral_radius=None, activity_variance=0.0, spectral_heuristic=None,
                lambda_2=None, lambda_max=None, c_t=None, confidence="LOW",
                node_count=n, edge_count=m, measurement_status="UNKNOWN",
            )

        # Telemetry sensor path — never gates routing.
        from doctor.spectral_metrics import calculate_spectral_metrics
        sm = calculate_spectral_metrics(graph, weight="weight", epsilon=self.eps)
        if sm.status == "UNKNOWN" or sm.confidence == "NONE":
            return CriticalitySnapshot(
                spectral_radius=sm.spectral_radius,
                activity_variance=0.0,
                spectral_heuristic=None,
                lambda_2=sm.lambda_2,
                lambda_max=sm.lambda_max,
                c_t=None,
                confidence="NONE",
                node_count=n,
                edge_count=m,
                measurement_status="UNKNOWN",
            )

        rho_a = sm.spectral_radius
        lambda_2 = sm.lambda_2
        lambda_max = sm.lambda_max
        sigma = sm.sigma_heuristic  # may be None (PARTIAL)

        deltas = np.diff(np.asarray(self.activity, dtype=float))
        activity_var = float(np.var(deltas)) if len(deltas) >= 2 else 0.0

        parts: list[tuple[float, float]] = []
        w_r, w_v, w_s = self.weights
        if rho_a is not None:
            parts.append((w_r, self._clip01(float(rho_a) / (float(rho_a) + 1.0))))
        parts.append((w_v, self._clip01(activity_var / (activity_var + 1.0))))
        if sigma is not None:
            parts.append((
                w_s,
                self._clip01(abs(float(sigma) - 1.0) / (abs(float(sigma) - 1.0) + 1.0)),
            ))
        wsum = sum(w for w, _ in parts) or 1.0
        c_t = self._clip01(sum((w / wsum) * v for w, v in parts))

        if sm.status == "PARTIAL" or sigma is None:
            confidence = "MEDIUM"
            mstatus = "PARTIAL"
        elif len(self.activity) >= self.window and sm.confidence == "HIGH":
            confidence = "HIGH"
            mstatus = "OK"
        else:
            confidence = "LOW"
            mstatus = sm.status
        return CriticalitySnapshot(
            spectral_radius=rho_a,
            activity_variance=activity_var,
            spectral_heuristic=sigma,
            lambda_2=lambda_2,
            lambda_max=lambda_max,
            c_t=c_t,
            confidence=confidence,
            connectivity_ratio_v2=sm.connectivity_ratio_v2,
            node_count=n,
            edge_count=m,
            measurement_status=mstatus,
        )


def append_trace(snap: CriticalitySnapshot, *, run_id: str = "", tick: int = 0) -> None:
    """Append component scores — never prompt/DM text."""
    disc = (
        snap.lambda_2 is not None
        and abs(float(snap.lambda_2)) < 1e-8
        and snap.node_count >= 3
    )
    rec = {
        "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "run_id": run_id,
        "tick": tick,
        "policy_version": VERSION,
        "evidence_level": "SHADOW",
        "graph_disconnected": disc,
        "measurement_status": snap.measurement_status,
        **snap.as_dict(),
        "components": {
            "rho_A": snap.spectral_radius,
            "var_delta_a": snap.activity_variance,
            "spectral_heuristic_sigma": snap.spectral_heuristic,
            "c_t": snap.c_t,
        },
        "metrics": snap.metrics(),
    }
    try:
        _TRACE.parent.mkdir(parents=True, exist_ok=True)
        with _TRACE.open("a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    except OSError:
        pass
    # OTLP → Alloy only when OCTOPUS_WIRE_CRITICALITY_OTLP=1 (no Grafana creds).
    try:
        from telemetry.criticality_metrics import emit_criticality
        emit_criticality(
            snap, graph_version=VERSION, confidence=str(snap.confidence)
        )
    except Exception:  # noqa: BLE001
        pass


def demo_path_graph(n: int = 6) -> Any:
    if not _HAS_GRAPH:
        raise RuntimeError("networkx/numpy required")
    return nx.path_graph(n)
