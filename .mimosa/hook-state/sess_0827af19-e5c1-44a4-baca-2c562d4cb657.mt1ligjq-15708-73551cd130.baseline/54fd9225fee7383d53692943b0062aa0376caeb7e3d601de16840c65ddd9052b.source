"""Five off-loop epistemic metrics. The MATH is real; DATA ADAPTERS are TODO (readers.py).

Numbers are MEANINGLESS until Phase 1-3 fill the upstream data streams (outbox,
fitness, telemetry, reconcile). Off-loop only; do not wire until Phase 5.

Dependency: numpy.
"""
from __future__ import annotations

import math
from collections import Counter
from typing import Iterable, Sequence

import numpy as np

from . import contracts as C


# 1) identifiability — N_eff via perplexity of the distribution over internal states
def identifiability(state_labels: Iterable) -> dict:
    counts = Counter(state_labels)
    n = sum(counts.values())
    if n == 0:
        return C.make_metric(C.IDENTIFIABILITY, None, 0, "no samples")
    probs = [c / n for c in counts.values()]
    entropy = -sum(p * math.log(p) for p in probs if p > 0)   # nats
    n_eff = math.exp(entropy)                                  # perplexity
    return C.make_metric(
        C.IDENTIFIABILITY, round(n_eff, 4), n,
        f"perplexity (N_eff) over {len(counts)} distinct states",
    )


# 2) channel — mutual information I(X;Y) plug-in estimator (biased on small n)
def channel(pairs: Sequence[tuple]) -> dict:
    n = len(pairs)
    if n == 0:
        return C.make_metric(C.CHANNEL, None, 0, "no paired samples (readers TODO)")
    joint = Counter(pairs)
    px = Counter(x for x, _ in pairs)
    py = Counter(y for _, y in pairs)
    mi = 0.0
    for (x, y), cxy in joint.items():
        pxy = cxy / n
        mi += pxy * math.log(pxy / ((px[x] / n) * (py[y] / n)))
    return C.make_metric(
        C.CHANNEL, round(mi, 4), n,
        "I(X;Y) in nats; plug-in estimator, positively biased on small n",
    )


# 3) levels — L_G graph Laplacian spectrum from an adjacency matrix
def levels(adjacency) -> dict:
    if adjacency is None:
        return C.make_metric(C.LEVELS, None, 0, "no topology (readers.read_topology TODO)")
    A = np.asarray(adjacency, dtype=float)
    if A.ndim != 2 or A.shape[0] != A.shape[1] or A.shape[0] < 2:
        return C.make_metric(C.LEVELS, None, int(A.shape[0] if A.ndim else 0), "invalid/trivial graph")
    A = np.maximum(A, A.T)                       # symmetrize
    D = np.diag(A.sum(axis=1))
    L = D - A
    eig = np.sort(np.linalg.eigvalsh(L))         # symmetric -> real eigenvalues
    return C.make_metric(
        C.LEVELS,
        {
            "eigenvalues": [round(float(e), 4) for e in eig],
            "algebraic_connectivity": round(float(eig[1]), 4),  # Fiedler value
            "spectral_gap": round(float(eig[1] - eig[0]), 4),
        },
        int(A.shape[0]),
        "Laplacian spectrum of the internal graph",
    )


# 4) self_reference — SOG = mean(err_other) - mean(err_self) with twin-control.
#    FUNCTIONAL verdict ONLY. Never a consciousness / transcendence claim.
def self_reference(err_self: Sequence[float], err_other: Sequence[float]) -> dict:
    n = min(len(err_self), len(err_other))
    if n == 0:
        return C.make_metric(C.SELF_REFERENCE, None, 0, "no paired errors (readers.read_self_vs_twin TODO)")
    es = np.asarray(err_self[:n], dtype=float)
    eo = np.asarray(err_other[:n], dtype=float)
    sog = float(np.mean(eo - es))                # > 0: self-model beats baseline twin
    return C.make_metric(
        C.SELF_REFERENCE, round(sog, 6), n,
        "FUNCTIONAL self-modeling verdict only (>0 = better-than-twin). "
        "NOT a consciousness/transcendence claim.",
    )


# 5) method — S=>L conditional proposition ONLY (never unconditional/metaphysical)
def method() -> dict:
    prop = {
        "antecedent_S": "identifiability, channel, levels, self_reference all hold above calibrated thresholds",
        "consequent_L": "the system MAY be labeled as exhibiting FUNCTIONAL relative self-modeling",
        "conditional": True,
        "unconditional_claim": False,
        "phenomenal_claim": False,
    }
    return C.make_metric(
        C.METHOD, prop, 1,
        "conditional S=>L only; asserts nothing unconditional or phenomenal",
    )
