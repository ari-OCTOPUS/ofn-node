#!/usr/bin/env python3
"""b4_fusion.py — B4: fusion φ_t (A=−L(G)) coupling to Dreamer novelty.

DOCTOR-BOX-OF-AGENTS-SPEC Part 8·B4: «φ_t (A=−L(G)) به‌عنوانِ میدانِ مشترک به
Dreamer novelty؛ ablationِ on/off.»

φ_t = fusion field از fusion_sim.py (A=−L(G)). Dreamer novelty از φ_t تغذیه می‌کند:
اگر φ_t نزدیکِ گذارِ فاز (σ≈1) → novelty بالا → exploration بیشتر.
ablation: on (φ_t feeds novelty) vs off (random novelty).

هیچ import از *_gate/chrono/money. $0 آفلاین.
"""
from __future__ import annotations

import math
import random
from dataclasses import dataclass

try:
    import numpy as np
    _HAS_NUMPY = True
except ImportError:
    _HAS_NUMPY = False


def compute_phi_t(edges: list[tuple[int, int]], n_nodes: int,
                  agent_states: list[float] | None = None) -> dict:
    """φ_t = fusion field. A = −L(G). φ = dynamics on graph.
    خروجی: {phi_vec, sigma, spectral_gap, near_critical}.
    از fusion_sim.stability_matrix استفاده می‌کند."""
    try:
        import sys as _sys
        from pathlib import Path as _P
        _here = _P(__file__).resolve().parent
        _ta = _P(__file__).resolve().parents[3] / "07 - Knowledge" / "Time-Architecture"
        for _p in (str(_here), str(_ta)):
            if _p not in _sys.path:
                _sys.path.insert(0, _p)
        from fusion_sim import stability_matrix
    except Exception:  # noqa: BLE001
        return {"phi_vec": [0.0] * n_nodes, "sigma": 0.0,
                "spectral_gap": 0.0, "near_critical": False, "available": False}

    if n_nodes == 0 or not edges:
        return {"phi_vec": [0.0] * n_nodes, "sigma": 0.0,
                "spectral_gap": 0.0, "near_critical": False, "available": True}
    A = stability_matrix(edges, n_nodes)
    phi_vec = [0.0] * n_nodes
    if agent_states and len(agent_states) >= n_nodes:
        # φ = A · x (one step of diffusion)
        for i in range(n_nodes):
            if _HAS_NUMPY:
                row = A[i]
                phi_vec[i] = float(sum(row[j] * agent_states[j]
                                       for j in range(min(n_nodes, len(agent_states)))))
            else:
                row = A[i] if i < len(A) else [0.0] * n_nodes
                phi_vec[i] = sum(row[j] * agent_states[j]
                                 for j in range(min(len(row), len(agent_states))))
    # σ from spectral
    if _HAS_NUMPY:
        try:
            eigvals = np.linalg.eigvalsh(np.asarray(A, dtype=float))
            eigvals_sorted = sorted(float(e) for e in eigvals)
            l_max = max(eigvals_sorted) if eigvals_sorted else 0.0
            l2 = eigvals_sorted[1] if len(eigvals_sorted) > 1 else l_max
            sigma = min(abs(l_max) / (abs(l2) + 1e-6), 10.0) if l2 != 0 else 0.0
            gap = abs(eigvals_sorted[1] - eigvals_sorted[0]) if len(eigvals_sorted) > 1 else 0.0
            near = abs(sigma - 1.0) < 0.3
            return {"phi_vec": [round(p, 4) for p in phi_vec],
                    "sigma": round(sigma, 3), "spectral_gap": round(gap, 4),
                    "near_critical": near, "available": True}
        except Exception:  # noqa: BLE001
            pass
    return {"phi_vec": [round(p, 4) for p in phi_vec], "sigma": 0.0,
            "spectral_gap": 0.0, "near_critical": False, "available": True}


def phi_to_novelty(phi_t: dict, base_novelty: float = 0.3) -> float:
    """φ_t → Dreamer novelty drive. اگر نزدیکِ critical → novelty بالا.
    ablation: اگر φ_t available نباشد → base_novelty (off mode)."""
    if not phi_t.get("available", False):
        return base_novelty   # off mode: random/base
    sigma = phi_t.get("sigma", 0.0)
    near = phi_t.get("near_critical", False)
    # near-critical → boost novelty (edge-of-chaos = creative)
    if near:
        return min(1.0, base_novelty + 0.4)
    # moderate sigma → moderate boost
    return min(1.0, base_novelty + 0.1 * min(sigma, 1.0))


@dataclass
class FusionAblation:
    """نتایجِ ablation: on (φ_t) vs off (random)."""
    novelty_on: float
    novelty_off: float
    phi_sigma: float
    phi_near_critical: bool
    novelty_boost: float    # on - off


def run_ablation(edges: list, n_nodes: int,
                 agent_states: list[float] | None = None,
                 base_novelty: float = 0.3) -> FusionAblation:
    """Ablation: novelty with φ_t vs without.
    نشان می‌دهد φ_t coupling چه تاثیری دارد."""
    phi_t = compute_phi_t(edges, n_nodes, agent_states)
    nov_on = phi_to_novelty(phi_t, base_novelty)
    nov_off = base_novelty
    return FusionAblation(
        novelty_on=nov_on, novelty_off=nov_off,
        phi_sigma=phi_t.get("sigma", 0.0),
        phi_near_critical=phi_t.get("near_critical", False),
        novelty_boost=round(nov_on - nov_off, 3))
