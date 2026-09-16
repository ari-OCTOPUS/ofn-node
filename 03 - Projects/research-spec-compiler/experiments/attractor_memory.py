"""
REAL experiment for specs/attractor_memory.yaml — H-GEO-02 (GEOMETRY.md section 3).

SUBSTRATE for the Hopfield energy-landscape row of GEOMETRY.md section 3
([SPEC] -> now [RUN]): "associative memory = energy system; retrieval =
falling to the floor of an attraction basin" [P L59, L539]. This module makes
that geometric claim executable and falsifiable: content-addressable retrieval
from NOISY probes must be attractor completion (descent into a stored basin),
which an exact-match lookup structurally cannot do. Only flip-noise probes
(exactly k corrupted bits) are tested here — masked/partial cues are NOT
exercised, so no claim is made about partial-probe completion.

Mechanism under test (a REAL Hopfield energy descent, not a metaphor):
  - M distinct random bipolar patterns xi^mu in {-1,+1}^N are stored by the
    Hebbian outer-product rule  W_ij = sum_mu xi_i^mu * xi_j^mu, W_ii = 0
    (integer weights -> exact arithmetic, no float drift).
  - A probe is a stored pattern with exactly k bits flipped.
  - attractor retrieval = asynchronous sign updates in fixed index order
    (x_i <- sign(sum_j W_ij x_j), field 0 -> keep) until a full sweep changes
    nothing (energy strictly decreases on every flip, so convergence to a
    fixed point is guaranteed; MAX_SWEEPS is only a safety cap).
    Retrieval SUCCEEDS iff the fixed point equals the true source pattern
    EXACTLY. Landing in a spurious minimum or a wrong/inverted basin fails.
  - exact_lookup retrieval = hash-table hit on the exact probe key; any
    corrupted probe misses and falls back to a CRC-seeded guess among the M
    stored patterns (expected accuracy 1/M). The guess fallback is the
    NON-STRAWMAN choice: it strictly dominates "fail on miss" (accuracy 0),
    so the attractor must beat a baseline that already gets 1/M for free.

Conditions (all PAIRED: per seed-index i every condition sees the identical
stored patterns, identical probes, identical fallback draws):
  null_same_vs_same          exact_lookup minus exact_lookup on the same noisy
                             probes and same fallback seeds -> exactly 0.0.
                             Verifies the pairing machinery adds no phantom
                             signal.
  clean_probe_gap            discriminating control, k=0 flips: exact lookup
                             is perfect on clean probes, so the attractor gets
                             ~0 advantage (slightly NEGATIVE if a stored
                             pattern is not a stable fixed point / spurious
                             attractors intrude). If this were as large as the
                             primary, the "advantage" would be about lookup
                             quality, not basin completion.
  saturating_noise_gap       second control, k=N/2 flips: the probe sits at
                             the distance of a RANDOM point from every stored
                             pattern, so no method can work. The advantage
                             collapses; in fact it goes slightly NEGATIVE
                             (~ -1/M): the descent lands in spurious/mixture
                             minima (accuracy ~0) while the exact arm keeps
                             its 1/M guess fallback [FACT: pilot 944_000,
                             k=32 -> attractor 0.000, exact 0.127,
                             gap -0.127]. Direct proof the primary is not
                             structurally positive.
  overload_gap               capacity ablation, same k as primary but
                             M_OVERLOAD patterns (load 0.375 >> Hopfield
                             capacity ~0.138N): cross-talk destroys the
                             basins, descent lands in spurious minima, and the
                             advantage must collapse (can go NEGATIVE, because
                             the exact arm still collects its 1/M fallback
                             while the attractor arm converges to garbage).
                             This is the mechanism-specific signature: the
                             advantage exists only inside the energy
                             landscape's capacity bound.
  noisy_retrieval_advantage  PRIMARY: acc(attractor) - acc(exact_lookup) at
                             the frozen operating point (M_STORED patterns,
                             K_NOISY flipped bits). Falsifiable: <= 0 whenever
                             basins fail (overload, saturation) — the paired
                             delta is not structurally positive.

Why this is not trivially clearable without the mechanism: the gated quantity
is the mechanism-specific completion advantage. Remove the descent (exact arm)
and the score is 1/M by construction; replace the landscape with an
overloaded one and the SAME descent code collapses (overload_gap). The
non-trivial content mirrors H-GEO-01's discipline: the primary plus THREE
zero/collapse controls pin the effect to basin geometry, not to "any fuzzy
matcher beats exact match" (which would be true but unfalsifiable-by-design;
here the controls make the claim breakable).

Determinism: EVERYTHING (patterns, flip positions, fallback guesses) is
seeded from CRCs of (family, seed-index, condition kind), NOT from the
harness RNG (whose seed differs by condition name). Universes are memoized
per (family, i, M) so paired conditions share one build. Zero LLM. Pure
stdlib. A full 5-seed run finishes in ~1-2 minutes.

Seed discipline (ADR-001/ADR-008 style): pilot family 944_000 calibrated the
operating point and the bands (run `python -m experiments.attractor_memory
--calibrate`); the CONFIRMATORY family 944_500+ is disjoint and was never
piloted. Constants below are FROZEN from the pilot.

SCOPE: C0 (functional). This is associative retrieval as basin descent in a
Hopfield landscape — no claim about biological memory, and NEVER a phenomenal
/ qualia claim (C0-C3 firewall, GEOMETRY.md section 0). Results hold for
SYNTHETIC random bipolar patterns only: the schema-key application to the
kernel memory store is future work, and real key distributions are correlated
(which lowers Hopfield capacity below ~0.138N), so carrying the effect over
is not established by this experiment (ADR-019 caveat 3).
"""
from __future__ import annotations

import zlib
from random import Random
from typing import Dict, List, Sequence, Tuple

from spec_compiler.harness import Condition

# ---------------------------------------------------------------- constants
N_BITS = 64                 # pattern dimension
M_STORED = 8                # stored patterns at the operating point (load 0.125)
M_OVERLOAD = 24             # capacity ablation (load 0.375 >> ~0.138 capacity)
N_PROBES = 150              # probes per seed (balanced across stored patterns)
K_NOISY = 14                # FROZEN from pilot 944_000: ~22% corruption —
                            # attractor completes at ~0.7-0.9 (off the
                            # ceiling: pilot seeds 0.693-0.913), exact ~1/M;
                            # pilot mean gap +0.685 over 5 pilot seeds
K_SATURATING = N_BITS // 2  # 50% corruption = distance of a random point
MAX_SWEEPS = 60             # safety cap; async descent converges long before
CONFIRM_FAMILY = 944_500    # CONFIRMATORY family (disjoint, never piloted)
PILOT_FAMILY = 944_000      # pilot/calibration only — never confirmatory

ATTRACTOR_LOG: dict = {}
_UNIVERSE_CACHE: dict = {}  # (family, i, m) -> (patterns, weights)


# ---------------------------------------------------------------- landscape
def _make_patterns(m: int, rng: Random) -> List[tuple]:
    """m DISTINCT random bipolar patterns in {-1,+1}^N_BITS."""
    pats: List[tuple] = []
    seen = set()
    while len(pats) < m:
        p = tuple(1 if rng.random() < 0.5 else -1 for _ in range(N_BITS))
        if p not in seen:
            seen.add(p)
            pats.append(p)
    return pats


def _weights(pats: Sequence[tuple]) -> List[List[int]]:
    """Hebbian outer-product weights, integer, zero diagonal."""
    n = len(pats[0])
    W = [[0] * n for _ in range(n)]
    for p in pats:
        for i in range(n):
            pi, Wi = p[i], W[i]
            for j in range(n):
                Wi[j] += pi * p[j]
    for i in range(n):
        W[i][i] = 0
    return W


def _descend(W: List[List[int]], probe: tuple) -> tuple:
    """Asynchronous energy descent in fixed index order until a fixed point.
    sign(0) keeps the current bit, so every flip strictly lowers the Hopfield
    energy E = -1/2 sum x_i W_ij x_j -> guaranteed convergence."""
    x = list(probe)
    n = len(x)
    for _ in range(MAX_SWEEPS):
        changed = False
        for i in range(n):
            h = 0
            Wi = W[i]
            for j in range(n):
                h += Wi[j] * x[j]
            if h > 0:
                if x[i] != 1:
                    x[i] = 1
                    changed = True
            elif h < 0:
                if x[i] != -1:
                    x[i] = -1
                    changed = True
        if not changed:
            break
    return tuple(x)


# ---------------------------------------------------------------- probes
def _make_probes(pats: Sequence[tuple], k_flips: int,
                 rng: Random) -> List[Tuple[int, tuple]]:
    """N_PROBES probes: source index (round-robin -> balanced) + a copy of the
    source with EXACTLY k_flips bits flipped at rng-chosen positions."""
    out: List[Tuple[int, tuple]] = []
    m = len(pats)
    for t in range(N_PROBES):
        src = t % m
        p = list(pats[src])
        if k_flips:
            for i in rng.sample(range(N_BITS), k_flips):
                p[i] = -p[i]
        out.append((src, tuple(p)))
    return out


# ---------------------------------------------------------------- retrieval
def _acc_exact(pats: Sequence[tuple], probes: Sequence[Tuple[int, tuple]],
               fb_tag: str) -> float:
    """Exact-key lookup: hit only on an exact pattern match; miss -> CRC-seeded
    guess among the stored patterns (expected 1/M — the fair fallback)."""
    table: Dict[tuple, int] = {p: idx for idx, p in enumerate(pats)}
    hits = 0
    for t, (src, probe) in enumerate(probes):
        idx = table.get(probe)
        if idx is None:
            fb = Random(zlib.crc32(f"fb|{fb_tag}|{t}".encode()))
            idx = fb.randrange(len(pats))
        hits += 1 if idx == src else 0
    return hits / len(probes)


def _acc_attractor(pats: Sequence[tuple], W: List[List[int]],
                   probes: Sequence[Tuple[int, tuple]]) -> float:
    """Basin descent: success iff the fixed point IS the source pattern."""
    hits = 0
    for src, probe in probes:
        if _descend(W, probe) == pats[src]:
            hits += 1
    return hits / len(probes)


# ---------------------------------------------------------------- universes
def _universe(family: int, i: int, m: int) -> Tuple[List[tuple], List[List[int]]]:
    key = (family, i, m)
    if key not in _UNIVERSE_CACHE:
        rng = Random(zlib.crc32(f"pat|{family}|{i}|{m}".encode()))
        pats = _make_patterns(m, rng)
        _UNIVERSE_CACHE[key] = (pats, _weights(pats))
    return _UNIVERSE_CACHE[key]


def _gap(family: int, i: int, m: int, k_flips: int) -> Tuple[float, float, float]:
    """Paired (attractor, exact, attractor-exact) on identical probes."""
    pats, W = _universe(family, i, m)
    probes = _make_probes(
        pats, k_flips, Random(zlib.crc32(f"probe|{family}|{i}|{m}|{k_flips}".encode())))
    acc_a = _acc_attractor(pats, W, probes)
    acc_e = _acc_exact(pats, probes, fb_tag=f"{family}|{i}|{m}|{k_flips}")
    return acc_a, acc_e, acc_a - acc_e


# ---------------------------------------------------------------- conditions
def _make(name: str, kind: str, family: int = CONFIRM_FAMILY) -> Condition:
    counter = {"i": 0}

    def run(_rng: Random) -> float:
        i = counter["i"]
        counter["i"] += 1
        if kind == "null":
            # same-vs-same: the SAME arm evaluated twice on the SAME probes
            # and fallback seeds -> the delta is 0 by construction IF the
            # pairing machinery is sound (that is what the null verifies).
            pats, _W = _universe(family, i, M_STORED)
            probes = _make_probes(
                pats, K_NOISY,
                Random(zlib.crc32(f"probe|{family}|{i}|{M_STORED}|{K_NOISY}".encode())))
            tag = f"{family}|{i}|{M_STORED}|{K_NOISY}"
            delta = _acc_exact(pats, probes, tag) - _acc_exact(pats, probes, tag)
            acc_a = acc_e = None
        elif kind == "clean":
            acc_a, acc_e, delta = _gap(family, i, M_STORED, 0)
        elif kind == "saturating":
            acc_a, acc_e, delta = _gap(family, i, M_STORED, K_SATURATING)
        elif kind == "overload":
            acc_a, acc_e, delta = _gap(family, i, M_OVERLOAD, K_NOISY)
        else:  # "noisy" — PRIMARY
            acc_a, acc_e, delta = _gap(family, i, M_STORED, K_NOISY)
        ATTRACTOR_LOG.setdefault(name, []).append(
            {"seed_index": i,
             "attractor": None if acc_a is None else round(acc_a, 3),
             "exact": None if acc_e is None else round(acc_e, 3),
             "delta": round(delta, 3)})
        return delta

    return Condition(name, run, kind)


def attractor_memory() -> Tuple[List[Condition], str]:
    """Registry entry: (conditions, primary). First condition is the ablation
    baseline for the harness delta column; primary is designated explicitly."""
    conditions = [
        _make("null_same_vs_same", "null"),
        _make("clean_probe_gap", "clean"),
        _make("saturating_noise_gap", "saturating"),
        _make("overload_gap", "overload"),
        _make("noisy_retrieval_advantage", "noisy"),
    ]
    return conditions, "noisy_retrieval_advantage"


REGISTRY_REAL = {"attractor_memory": attractor_memory}


# ---------------------------------------------------------------- smoke / pilot
if __name__ == "__main__":
    import json
    import sys
    import time

    t0 = time.time()

    if "--calibrate" in sys.argv:
        # PILOT (family 944_000, DISJOINT from confirmatory): sweep corruption
        # and load to choose the frozen operating point + honest bands.
        print(f"# PILOT family {PILOT_FAMILY}  N={N_BITS}  probes={N_PROBES}")
        for m in (8, 24):
            print(f"\nM={m}  (load {m / N_BITS:.3f}; Hopfield capacity ~0.138)")
            for k in (0, 4, 8, 12, 14, 16, 20, 24, 32):
                acc_a, acc_e, delta = _gap(PILOT_FAMILY, 0, m, k)
                print(f"  k={k:<3} attractor={acc_a:.3f}  exact={acc_e:.3f}  "
                      f"delta={delta:+.3f}")
        print(f"\n# pilot multi-seed at the candidate operating point "
              f"(M={M_STORED}, k={K_NOISY})")
        vals = []
        for i in range(5):
            acc_a, acc_e, delta = _gap(PILOT_FAMILY, i, M_STORED, K_NOISY)
            vals.append(delta)
            print(f"  seed {i}: attractor={acc_a:.3f}  exact={acc_e:.3f}  "
                  f"delta={delta:+.3f}")
        print(f"  mean delta = {sum(vals) / len(vals):+.4f}")
        print(f"total {time.time() - t0:.1f}s")

    else:
        # quick single-seed smoke through the registry path (CONFIRMATORY
        # family, 1 seed only — the official verdict is `rsc.py run`).
        conditions, primary = attractor_memory()
        for c in conditions:
            v = c.run(Random(0))
            print(f"{c.name:<28} delta={v:+.3f}")
        print(f"primary = {primary}")
        print(json.dumps(ATTRACTOR_LOG, indent=1))
        print(f"total {time.time() - t0:.1f}s")
