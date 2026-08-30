"""Representation competition, scored by held-out link prediction.

This is the non-circular part: the ground truth (which edges were hidden) comes
from the data, never from the representation being judged. The random control
must land at AUC ≈ 0.50 — if it does not, the split leaked and the whole report
is void, so we check it and say so.
"""

from __future__ import annotations

import numpy as np
from sklearn.metrics import average_precision_score, roc_auc_score

from ...kernel.types import BakeoffReport, LinkGraph, RepresentationScore
from .representations import REGISTRY, Representation, adjacency

__all__ = ["run_bakeoff", "split_edges"]

BASELINE = "adamic_adar"


def split_edges(n: int, edges: list[tuple[int, int]], seed: int, test_frac: float):
    """Hide a fraction of edges; sample an equal number of true non-edges.

    Negatives are drawn from the non-edges of the FULL graph, so a hidden
    positive can never be handed back as a negative.
    """
    rng = np.random.default_rng(seed)
    E = np.array(edges)
    n_test = max(10, int(round(test_frac * len(E))))
    n_test = min(n_test, len(E) - 1)
    perm = rng.permutation(len(E))
    test_e = E[perm[:n_test]]
    train_e = [tuple(x) for x in E[perm[n_test:]]]

    full = {(min(a, b), max(a, b)) for a, b in edges}
    negs: list[tuple[int, int]] = []
    tries = 0
    seen: set[tuple[int, int]] = set()
    while len(negs) < n_test and tries < n_test * 2000:
        u, v = int(rng.integers(0, n)), int(rng.integers(0, n))
        tries += 1
        if u == v:
            continue
        k = (min(u, v), max(u, v))
        if k in full or k in seen:
            continue
        seen.add(k)
        negs.append(k)

    pairs = [(int(min(a, b)), int(max(a, b))) for a, b in test_e] + negs
    y = np.r_[np.ones(len(test_e)), np.zeros(len(negs))]
    return train_e, pairs, y


def run_bakeoff(
    graph: LinkGraph,
    *,
    seeds: list[int] | None = None,
    test_frac: float = 0.20,
    representations: tuple[Representation, ...] = REGISTRY,
    progress=None,
) -> BakeoffReport:
    seeds = seeds or [0, 1, 2, 3, 4]
    n, edges = graph.n, graph.edges
    notes: list[str] = []

    if n < 20 or len(edges) < 25:
        return BakeoffReport(
            n_nodes=n, n_edges=len(edges), test_frac=test_frac, seeds=seeds,
            scores=[], winner=None, winner_beats_baseline_by=None,
            baseline=BASELINE, control_auc=None, control_ok=False,
            notes=[f"graph too small for a meaningful benchmark "
                   f"(n={n}, m={len(edges)}); need ≥20 nodes and ≥25 edges"],
        )

    active, skipped = [], []
    for r in representations:
        (active if n <= r.max_nodes else skipped).append(r)
    for r in skipped:
        notes.append(f"SKIPPED {r.name}: needs n ≤ {r.max_nodes:,}, this graph has n = {n:,}")

    auc = {r.name: [] for r in active}
    ap = {r.name: [] for r in active}
    secs = {r.name: 0.0 for r in active}

    total = len(seeds) * len(active)
    step = 0
    for seed in seeds:
        train_e, pairs, y = split_edges(n, edges, seed, test_frac)
        A = adjacency(n, train_e)
        for r in active:
            rng = np.random.default_rng(seed * 7919 + hash(r.name) % 100_000)
            s, dt = r.score(A, pairs, rng)
            auc[r.name].append(roc_auc_score(y, s))
            ap[r.name].append(average_precision_score(y, s))
            secs[r.name] += dt
            step += 1
            if progress:
                progress(step / total, f"{r.label} · seed {seed}")

    scores = [
        RepresentationScore(
            name=r.name,
            auc_mean=float(np.mean(auc[r.name])), auc_std=float(np.std(auc[r.name])),
            ap_mean=float(np.mean(ap[r.name])), ap_std=float(np.std(ap[r.name])),
            n_splits=len(seeds), seconds=round(secs[r.name], 2),
        ) for r in active
    ] + [
        RepresentationScore(name=r.name, auc_mean=float("nan"), auc_std=float("nan"),
                            ap_mean=float("nan"), ap_std=float("nan"),
                            n_splits=0, seconds=0.0, skipped=True,
                            skip_reason=f"n={n:,} > max_nodes={r.max_nodes:,}")
        for r in skipped
    ]

    real = [s for s in scores if not s.skipped and s.name != "random_control"]
    winner = max(real, key=lambda s: s.auc_mean).name if real else None
    ctrl = next((s for s in scores if s.name == "random_control"), None)
    control_auc = ctrl.auc_mean if ctrl else None
    # with k seeds the control's standard error is ~std/sqrt(k); allow 3 SE.
    control_ok = True
    if ctrl and ctrl.n_splits:
        se = max(ctrl.auc_std / max(1, np.sqrt(ctrl.n_splits)), 0.01)
        control_ok = abs(ctrl.auc_mean - 0.5) <= 3 * se
        if not control_ok:
            notes.append(
                f"CONTROL FAILED: random scorer reached AUC {ctrl.auc_mean:.3f} "
                f"(expected ≈0.500 ± {3*se:.3f}). Suspect leakage — do not trust these numbers.")

    base = next((s for s in scores if s.name == BASELINE and not s.skipped), None)
    delta = None
    if winner and base:
        delta = float(next(s.auc_mean for s in scores if s.name == winner) - base.auc_mean)

    for s in real:
        if s.auc_mean < 0.45:
            notes.append(f"{s.name} scored {s.auc_mean:.3f} — WORSE than chance on this "
                         f"vault; it is anti-predictive here, not merely useless.")

    return BakeoffReport(
        n_nodes=n, n_edges=len(edges), test_frac=test_frac, seeds=seeds,
        scores=sorted(scores, key=lambda s: (s.skipped, -(s.auc_mean if s.auc_mean == s.auc_mean else -1))),
        winner=winner, winner_beats_baseline_by=delta, baseline=BASELINE,
        control_auc=control_auc, control_ok=control_ok, notes=notes,
    )
