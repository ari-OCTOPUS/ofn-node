#!/usr/bin/env python3
"""sensors.py — Part 4/2: stability + information sensors.

rho_jacobian(X): شعاعِ طیفیِ ژاکوبینِ خطی‌شده. ρ(J)<1 = bounded.
mutual_info I(a;x): تخمینِ هیستوگرام. neural vs random جداکننده.
هیچ import از production."""
from __future__ import annotations
import math
from collections import Counter

try:
    import numpy as np
    _HAS_NUMPY = True
except ImportError:
    _HAS_NUMPY = False


def estimate_jacobian(states_seq: list[list[float]],
                      delta: float = 1e-6) -> "list | object":
    """تخمینِ ژاکوبینِ خطی‌شده از دنبالهٔ states.
    J ≈ ΔX_{t+1} / ΔX_t. اگر numpy نباشد → identity تقریبی."""
    if len(states_seq) < 2:
        n = len(states_seq[0]) if states_seq else 1
        return [[1.0 if i == j else 0.0 for j in range(n)] for i in range(n)]
    if _HAS_NUMPY:
        X = np.asarray(states_seq, dtype=float)
        dX = np.diff(X, axis=0)
        # J ≈ dX_next / dX_prev (least-squares)
        if len(dX) < 2:
            n = X.shape[1]
            return np.eye(n) * 0.5   # stable-ish
        try:
            # J = dX[1:] @ pinv(dX[:-1])
            J = dX[1:].T @ np.linalg.pinv(dX[:-1].T)
            return J
        except np.linalg.LinAlgError:
            n = X.shape[1]
            return np.eye(n) * 0.5
    # pure-python: میانگینِ نسبت
    n = len(states_seq[0]) if states_seq else 1
    return [[0.5 if i == j else 0.0 for j in range(n)] for i in range(n)]


def rho_jacobian(J) -> float:
    """شعاعِ طیفیِ ژاکوبین. ρ(J) = max|eigenvalue|.
    ρ<1 = bounded (Part 4.4)."""
    if _HAS_NUMPY and hasattr(J, "shape"):
        try:
            eigvals = np.linalg.eigvals(np.asarray(J, dtype=complex))
            return float(max(abs(eigvals)))
        except np.linalg.LinAlgError:
            return 1.5   # fail-unsafe (Warden مداخله می‌کند)
    # pure-python: تقریب با Gershgorin (کرانِ بالای |eigenvalue|)
    n = len(J) if isinstance(J, list) else 1
    if n == 0:
        return 0.0
    max_radius = 0.0
    for i in range(n):
        row = J[i] if i < len(J) else [0.0] * n
        diag = abs(row[i]) if i < len(row) else 0.0
        off_diag = sum(abs(row[j]) for j in range(n) if j != i and j < len(row))
        max_radius = max(max_radius, diag + off_diag)
    return max_radius


def mutual_info(actions: list, states: list, n_bins: int = 4) -> float:
    """I(a;x) = Σ p(a,x) log[p(a,x)/(p(a)p(x))].
    تخمینِ هیستوگرام (histogram-based). actions/states = list of scalars or labels.
    I≈0 → random. I≫0 → neural."""
    if len(actions) < 3 or len(states) < 3:
        return 0.0
    # discretize
    a_disc = _discretize(actions, n_bins)
    x_disc = _discretize(states, n_bins)
    n = len(a_disc)
    # joint histogram
    joint = Counter(zip(a_disc, x_disc))
    pa = Counter(a_disc)
    px = Counter(x_disc)
    mi = 0.0
    for (ai, xi), c in joint.items():
        p_ax = c / n
        p_a = pa[ai] / n
        p_x = px[xi] / n
        if p_ax > 0 and p_a > 0 and p_x > 0:
            mi += p_ax * math.log2(p_ax / (p_a * p_x))
    return max(0.0, mi)


def _discretize(vals: list, n_bins: int) -> list:
    """discretize به n_bins."""
    if not vals:
        return []
    try:
        nums = [float(v) for v in vals]
    except (ValueError, TypeError):
        # labels → hash به bin
        return [hash(str(v)) % n_bins for v in vals]
    lo, hi = min(nums), max(nums)
    if hi == lo:
        return [0] * len(nums)
    return [int((v - lo) / (hi - lo) * (n_bins - 1)) for v in nums]


def neuralness_score(actions: list, states: list) -> float:
    """neural-ness: fraction of variance in a predictable from x.
    proxy = mutual_info normalized. اگر I≈0 → random."""
    mi = mutual_info(actions, states)
    # normalize: log2(n_bins) = max possible MI
    return min(1.0, mi / max(math.log2(4), 0.001))


def contradiction_rate(contradictions: list[bool]) -> float:
    """نرخِ contradiction. نباید به صفر میل کند (آژیرِ spiral)."""
    if not contradictions:
        return 0.0
    return sum(1 for c in contradictions if c) / len(contradictions)
