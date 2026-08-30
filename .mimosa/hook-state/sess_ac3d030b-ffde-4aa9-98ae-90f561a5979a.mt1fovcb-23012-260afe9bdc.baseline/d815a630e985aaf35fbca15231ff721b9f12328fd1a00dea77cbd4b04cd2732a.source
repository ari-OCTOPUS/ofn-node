"""
REAL experiment for specs/wm_abstraction_v2.yaml — H-OWN-03 v2 / EXP-001b.

v1 (wm_abstraction) used an ABSOLUTE transfer bar (0.67) that came from a
synthetic mock guess; the confirmatory run was REJECTED against it even though
the *relative* effect was large (+0.25). v2 preregisters the relative effect
directly: the primary metric is the PAIRED transfer gain (limited_wm minus
unlimited_memory on the same universe), with a null control (unlimited vs an
independent unlimited on the same universe). NOTE (adversarial review): the
null is a STRUCTURAL zero — heldout keys never hit the unlimited Q, so both
agents run identical deterministic fallbacks; it validates the plumbing only,
not training variance. The preregistered content of paired_gain is its
MAGNITUDE vs SESOI 0.10 (its positive sign is near-guaranteed vs a random-walk
floor); interpretability leans on v1's oracle_no_taskid control (ADR-001).

Fully reuses gridworld_wm (improve-not-rewrite). Seed family 994000+, disjoint
from confirmatory (991000+), census (997000+) and geometry (993000+).
"""
from __future__ import annotations

import zlib
from random import Random
from typing import List, Tuple

from spec_compiler.harness import Condition

from .gridworld_wm import (
    N_FEATURES, PRIMARY_K, TOTAL_EPISODE_BUDGET, _run_agent, build_suite,
    select_slots,
)

GAIN_BASE_SEED = 994_000
GAIN_LOG: dict = {}


def _make(name: str, kind: str) -> Condition:
    counter = {"i": 0}

    def run(rng: Random) -> float:
        i = counter["i"]
        counter["i"] += 1
        suite = build_suite(GAIN_BASE_SEED + i)
        all_slots = tuple(range(N_FEATURES))
        acc_unlimited = _run_agent(suite, all_slots, TOTAL_EPISODE_BUDGET, rng)
        if kind == "gain":
            slots, spent = select_slots(suite, PRIMARY_K, rng)
            acc_other = _run_agent(suite, slots, TOTAL_EPISODE_BUDGET - spent, rng)
        else:   # null: a second, independent unlimited agent on the same universe
            rng2 = Random(zlib.crc32(f"null2|{i}".encode()))
            acc_other = _run_agent(suite, all_slots, TOTAL_EPISODE_BUDGET, rng2)
        delta = acc_other - acc_unlimited
        GAIN_LOG.setdefault(name, []).append(
            {"seed_index": i, "unlimited": round(acc_unlimited, 3),
             "other": round(acc_other, 3), "delta": round(delta, 3)})
        return delta

    return Condition(name, run, name)


def wm_transfer_gain() -> Tuple[List[Condition], str]:
    conditions = [
        _make("null_gain", "null"),
        _make("paired_gain", "gain"),
    ]
    return conditions, "paired_gain"
