"""
REAL experiment for specs/geometry_abstraction.yaml — H-GEO-01.

Geometrizes principle #7 (abstraction is stable when useful for
prediction/compression/transfer) as a measurable representational-geometry
quantity, and tests whether that geometry PREDICTS the learned agent's
transfer. See GEOMETRY.md §2. Zero LLM; everything derives from the
deterministic grid-world + BFS.

NAMING (post adversarial review): the metric is RTA = Representational
Transfer Alignment. It is NOT RSA. RSA/CKA/D_causal (cited in GEOMETRY.md as
lineage/motivation only) correlate two dissimilarity matrices; RTA is a
supervised train->heldout bin-majority-action hit rate. It also approximates
the realizable ceiling of the tabular agent's own policy class, so a high
alignment->transfer correlation is near-definitional; the informative signals
are the two controls (shuffle ~ 0, and compression-fails-while-RTA-works).

For a representation phi (a fixed set of feature slots) and a universe:
  alignment(phi)   RTA: fraction of HELDOUT states where "look up your
                   representational bin from TRAIN, act by its majority optimal
                   action" hits the true optimal action. Depends only on phi
                   and the environment (not on Q).
  compression(phi) 1 - |unique phi-keys on heldout| / |heldout states|.
  transfer(phi)    the actual trained tabular agent's heldout accuracy
                   (reuses gridworld_wm.train/evaluate, equal budget).

H-GEO-01 primary metric: Spearman rho between alignment and transfer across a
fixed sweep of representations. shuffle_control shuffles transfer before
correlating (must give rho ~ 0).

Determinism: BFS + fixed suites; agent stochasticity from the harness RNG;
shuffle uses a CRC-seeded permutation (no global RNG).
"""
from __future__ import annotations

from collections import Counter, deque
from operator import itemgetter
from random import Random
from typing import Dict, List, Sequence, Tuple

from spec_compiler.harness import Condition

from .gridworld_wm import (
    GRID, MOVES, N_FEATURES, N_TRAIN, build_suite, evaluate, train,
)

GEO_BASE_SEED = 993_000          # disjoint from pilot/confirmatory/census
GEO_BUDGET = 150_000
GEO_EVAL_STARTS = 5

# fixed representation sweep (name, slot tuple). No gating cost -> fast + reproducible.
# spans the alignment axis from task-id-heavy (poor) to relational (good).
SWEEP: List[Tuple[str, Tuple[int, ...]]] = [
    ("unlimited",         tuple(range(N_FEATURES))),
    ("minimal_sufficient", (5, 6, 7, 8, 9, 10)),
    ("k2",                (5, 6)),
    ("k4",                (5, 6, 7, 8)),
    ("k8",                (5, 6, 7, 8, 9, 10, 11, 12)),
    ("random6",           (2, 4, 7, 10, 13, 16)),
    ("taskid6",           (0, 1, 2, 14, 15, 16)),   # coords + layout + raw attrs
]

GEO_LOG: dict = {}


# ---------------------------------------------------------------- optimal action
def optimal_actions(task) -> Dict[Tuple[int, int], int]:
    """a*(cell) via BFS on the deterministic grid: distance-to-target over cells
    that are in-bounds, not walls, and not the loser (stepping on loser = loss,
    so an optimal path never uses it). Action = the move minimizing neighbor
    distance-to-target; blocked move keeps the cell (its own distance); tie ->
    lowest action index. Cells with no admissible path to target are omitted."""
    walls, target, loser = task.walls, task.target, task.loser
    passable = {(x, y) for x in range(GRID) for y in range(GRID)
                if (x, y) not in walls and (x, y) != loser}
    passable.add(target)
    dist: Dict[Tuple[int, int], int] = {target: 0}
    dq = deque([target])
    while dq:
        c = dq.popleft()
        for dx, dy in MOVES:
            n = (c[0] + dx, c[1] + dy)
            if n in passable and n not in dist:
                dist[n] = dist[c] + 1
                dq.append(n)
    out: Dict[Tuple[int, int], int] = {}
    for cell in task.feats:
        if cell == target or cell == loser or cell not in dist:
            continue
        best_a, best_d = None, None
        for a, (dx, dy) in enumerate(MOVES):
            nb = (cell[0] + dx, cell[1] + dy)
            if nb not in passable:              # off-grid / wall / loser -> stay
                nb = cell
            d = dist.get(nb)
            if d is None:
                continue
            if best_d is None or d < best_d:
                best_a, best_d = a, d
        if best_a is not None:
            out[cell] = best_a
    return out


# ---------------------------------------------------------------- geometry metrics
def _entropy(counts: Sequence[int]) -> float:
    import math
    tot = sum(counts)
    if tot == 0:
        return 0.0
    h = 0.0
    for c in counts:
        if c:
            p = c / tot
            h -= p * math.log(p)
    return h


def alignment_and_compression(
    suite, slots: Sequence[int]
) -> Tuple[float, float]:
    """Pure geometric quantities for representation `slots`.
    alignment: transfer-correct RSA (see module docstring).
    compression: 1 - |unique heldout keys| / |heldout states|."""
    key_of = itemgetter(*slots) if len(slots) > 1 else (lambda f, _i=slots[0]: (f[_i],))
    train_tasks = suite[:N_TRAIN]
    held_tasks = suite[N_TRAIN:]

    # train bins: rep_key -> Counter(optimal_action)
    bins: Dict[tuple, Counter] = {}
    for t in train_tasks:
        opt = optimal_actions(t)
        for cell, a in opt.items():
            bins.setdefault(key_of(t.feats[cell]), Counter())[a] += 1
    # per-bin majority optimal action; deterministic tie-break = lowest action index
    majority = {}
    for k, c in bins.items():
        best_a, best_n = None, -1
        for a in sorted(c):                     # lowest action index on tie
            if c[a] > best_n:
                best_a, best_n = a, c[a]
        majority[k] = best_a

    hits = total = 0
    heldout_keys: List[tuple] = []
    for t in held_tasks:
        opt = optimal_actions(t)
        for cell, a in opt.items():
            k = key_of(t.feats[cell])
            heldout_keys.append(k)
            total += 1
            if k in majority and majority[k] == a:
                hits += 1
    alignment = hits / total if total else 0.0
    compression = 1.0 - (len(set(heldout_keys)) / len(heldout_keys)) if heldout_keys else 0.0
    return alignment, compression


def _spearman(xs: Sequence[float], ys: Sequence[float]) -> float:
    """Spearman rho via Pearson on ranks (average ranks for ties). No SciPy."""
    n = len(xs)
    if n < 2:
        return 0.0

    def ranks(v: Sequence[float]) -> List[float]:
        order = sorted(range(n), key=lambda i: v[i])
        r = [0.0] * n
        i = 0
        while i < n:
            j = i
            while j + 1 < n and v[order[j + 1]] == v[order[i]]:
                j += 1
            avg = (i + j) / 2.0 + 1.0
            for k in range(i, j + 1):
                r[order[k]] = avg
            i = j + 1
        return r

    rx, ry = ranks(xs), ranks(ys)
    mx, my = sum(rx) / n, sum(ry) / n
    num = sum((rx[i] - mx) * (ry[i] - my) for i in range(n))
    dx = sum((rx[i] - mx) ** 2 for i in range(n)) ** 0.5
    dy = sum((ry[i] - my) ** 2 for i in range(n)) ** 0.5
    if dx == 0 or dy == 0:
        return 0.0
    return num / (dx * dy)


# ---------------------------------------------------------------- conditions
def _sweep_points(suite, rng: Random):
    """For each representation in SWEEP: (name, alignment, compression, transfer)."""
    pts = []
    for name, slots in SWEEP:
        align, comp = alignment_and_compression(suite, slots)
        Q: dict = {}
        train(Q, suite[:N_TRAIN], slots, GEO_BUDGET, rng)
        tr = evaluate(Q, suite[N_TRAIN:], slots, GEO_EVAL_STARTS)
        pts.append((name, align, comp, tr))
    return pts


def _make_condition(name: str, shuffle: bool) -> Condition:
    counter = {"i": 0}

    def run(rng: Random) -> float:
        import zlib
        i = counter["i"]
        counter["i"] += 1
        suite = build_suite(GEO_BASE_SEED + i)
        pts = _sweep_points(suite, rng)
        aligns = [p[1] for p in pts]
        transfers = [p[3] for p in pts]
        if shuffle:
            # deterministic CRC-seeded permutation of the transfer labels
            perm = list(range(len(transfers)))
            Random(zlib.crc32(f"geo-shuffle|{i}".encode())).shuffle(perm)
            transfers = [transfers[j] for j in perm]
        rho = _spearman(aligns, transfers)
        GEO_LOG.setdefault(name, []).append(
            {"seed_index": i, "rho": rho,
             "points": [{"rep": p[0], "alignment": round(p[1], 3),
                         "compression": round(p[2], 3), "transfer": round(p[3], 3)}
                        for p in pts]})
        return rho

    return Condition(name, run, name)


def geometry_abstraction() -> Tuple[List[Condition], str]:
    conditions = [
        _make_condition("shuffle_control", shuffle=True),
        _make_condition("geo_alignment", shuffle=False),
    ]
    return conditions, "geo_alignment"
