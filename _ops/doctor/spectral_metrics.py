#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""spectral_metrics.py — NetworkX + SciPy spectral helpers for C_t (SHADOW).

Fail-closed for decision use when graph unhealthy. Does not gate heart/router.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from math import isfinite
from typing import Any

import networkx as nx
import numpy as np

try:
    from spectral_definitions import (
        FORMULA_CONNECTIVITY_RATIO_V2,
        compute_connectivity_ratio_v2,
    )
except ImportError:  # هنگام بارگذاری به‌عنوان doctor.spectral_metrics
    from doctor.spectral_definitions import (
        FORMULA_CONNECTIVITY_RATIO_V2,
        compute_connectivity_ratio_v2,
    )


@dataclass(frozen=True)
class SpectralMetrics:
    """Telemetry sensor — not a crisis brain. UNKNOWN ≠ 0.0."""

    node_count: int
    edge_count: int
    spectral_radius: float | None
    lambda_2: float | None
    lambda_max: float | None
    sigma_heuristic: float | None  # legacy σ; None when meaningless
    confidence: str
    reason: str | None = None
    graph_disconnected: bool = False
    connectivity_ratio_v2: float | None = None  # v2 ratio; None when meaningless
    status: str = "OK"  # OK | UNKNOWN | PARTIAL


def calculate_spectral_metrics(
    graph: nx.Graph,
    *,
    weight: str = "weight",
    epsilon: float = 1e-9,
) -> SpectralMetrics:
    n = graph.number_of_nodes()
    m = graph.number_of_edges()

    if n < 3:
        return SpectralMetrics(
            n, m, None, None, None, None, "LOW", "graph_too_small", status="UNKNOWN"
        )

    if any(
        not isfinite(float(data.get(weight, 1.0)))
        or float(data.get(weight, 1.0)) < 0.0
        for _, _, data in graph.edges(data=True)
    ):
        return SpectralMetrics(
            n, m, None, None, None, None, "NONE", "invalid_edge_weight",
            status="UNKNOWN",
        )

    try:
        from scipy.sparse.linalg import eigs, eigsh

        adjacency = nx.to_scipy_sparse_array(
            graph, weight=weight, format="csr", dtype=float
        )

        if graph.is_directed():
            values = eigs(adjacency, k=1, which="LM", return_eigenvectors=False)
            radius = float(np.abs(values[0]))
            # Directed: only ρ(A); λ₂ / σ stay UNKNOWN (not zero).
            return SpectralMetrics(
                n, m, radius, None, None, None, "MEDIUM", "directed_graph",
                status="PARTIAL",
            )

        disconnected = not nx.is_connected(graph)
        laplacian = nx.laplacian_matrix(graph, weight=weight).astype(float)

        lambda_max = float(
            eigsh(laplacian, k=1, which="LA", return_eigenvectors=False)[0]
        )
        smallest = np.sort(
            eigsh(laplacian, k=2, which="SM", return_eigenvectors=False)
        )
        lambda_2 = float(smallest[1])
        radius = float(
            np.abs(eigsh(adjacency.astype(float), k=1, which="LA",
                         return_eigenvectors=False)[0])
        )

        if disconnected or abs(lambda_2) < 1e-8:
            # λ₂≈0 is real; σ is meaningless — UNKNOWN, not "very critical"
            return SpectralMetrics(
                n, m, radius, lambda_2, lambda_max, None, "MEDIUM",
                "graph_disconnected", graph_disconnected=True, status="PARTIAL",
            )

        sigma = lambda_max / (lambda_2 + epsilon)
        cr_v2 = compute_connectivity_ratio_v2(lambda_2, lambda_max, eps=epsilon)
        return SpectralMetrics(
            n, m, radius, lambda_2, lambda_max, sigma, "HIGH",
            connectivity_ratio_v2=cr_v2, status="OK",
        )
    except Exception as exc:  # noqa: BLE001
        return SpectralMetrics(
            n, m, None, None, None, None, "NONE",
            f"spectral_error:{type(exc).__name__}",
            status="UNKNOWN",
        )


def to_nx_from_activity(nodes: list[str], edges: list[tuple[str, str]]) -> Any:
    g = nx.Graph()
    g.add_nodes_from(nodes or ["_a", "_b", "_c"])
    g.add_edges_from(edges or [])
    if g.number_of_edges() == 0 and g.number_of_nodes() >= 2:
        # path fallback for tiny probes
        seq = list(g.nodes())
        g.add_edges_from(zip(seq, seq[1:]))
    return g
