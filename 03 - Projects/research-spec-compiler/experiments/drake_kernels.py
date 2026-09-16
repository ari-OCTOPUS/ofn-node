"""
REAL experiment for specs/drake_kernels.yaml — a Monte-Carlo "Drake census"
over a simulated multiverse.

Each universe u is an independent task suite (seed family 997000+, disjoint
from H-OWN-03's pilot 987000 and confirmatory 991000+ families). Inside each
universe the FROZEN EXP-001 protocol runs unchanged (same budget, gating,
eval). The census metric is Drake-style:

    f_transfer = (1/U) * sum_u [ transfer_accuracy(u) > VIABILITY_THRESHOLD ]

i.e. the fraction of universes in which a transferable abstraction "emerges".
VIABILITY_THRESHOLD = 0.5 is semantic (the agent solves the majority of
heldout episodes), not tuned.

SCOPE: C0 tabular agents in this simulated family only. No claim about the
physical multiverse or biological consciousness — the point is that THIS is
the only multiverse for which a Drake factor is measurable at all (contrast:
specs/drake_multiverse.yaml, which the validator rejects as unfalsifiable).
"""
from __future__ import annotations

from random import Random
from typing import List, Tuple

from spec_compiler.harness import Condition

from .gridworld_wm import (
    EVAL_STARTS, N_FEATURES, N_TRAIN, PRIMARY_K, TOTAL_EPISODE_BUDGET,
    build_suite, evaluate, select_slots, train,
)

N_UNIVERSES = 10
UNIVERSE_BASE_SEED = 997_000
VIABILITY_THRESHOLD = 0.5

CENSUS_LOG: dict = {}


def _universe_transfer(suite, limited: bool, rng: Random) -> float:
    if limited:
        slots, spent = select_slots(suite, PRIMARY_K, rng)
        budget = TOTAL_EPISODE_BUDGET - spent
    else:
        slots, budget = tuple(range(N_FEATURES)), TOTAL_EPISODE_BUDGET
    Q: dict = {}
    train(Q, suite[:N_TRAIN], slots, budget, rng)
    return evaluate(Q, suite[N_TRAIN:], slots, EVAL_STARTS)


def _make_census(name: str, desc: str, limited: bool) -> Condition:
    counter = {"i": 0}

    def run(rng: Random) -> float:
        i = counter["i"]
        counter["i"] += 1
        per_universe: List[float] = []
        for u in range(N_UNIVERSES):
            suite = build_suite(UNIVERSE_BASE_SEED + i * N_UNIVERSES + u)
            per_universe.append(_universe_transfer(suite, limited, rng))
        CENSUS_LOG.setdefault(name, []).append(
            {"seed_index": i, "per_universe_transfer": per_universe})
        return sum(1 for t in per_universe if t > VIABILITY_THRESHOLD) / N_UNIVERSES

    return Condition(name, run, desc)


def drake_kernels() -> Tuple[List[Condition], str]:
    conditions = [
        _make_census("unlimited_census",
                     "raw unlimited buffer kernel, per-universe census", False),
        _make_census("limited_wm_census",
                     f"K={PRIMARY_K} gated WM kernel, per-universe census", True),
    ]
    return conditions, "limited_wm_census"
