"""
REAL experiment for specs/consolidation.yaml — H-OWN-04 / EXP-002.

Tests the raw files' H-OWN-04 [P L1486] / EXP-002 [P L1811]: memory
consolidation that converts repeated episodes into a REUSABLE SCHEMA LIBRARY
should transfer better than merely REPLAYING raw episodes, at equal offline
budget.

All three arms share a base agent (tabular Q on the abstract minimal-sufficient
representation, trained B_TRAIN episodes on train tasks). Then, at equal offline
budget B_CONS:
  no_consolidation  base agent, frozen.
  raw_replay        B_CONS more Q-learning episodes on the train tasks (the
                    standard experience-replay analog — keep refitting).
  schema_library    consolidate experience into a clean library: roll out the
                    base greedy policy on train tasks, and for each abstract bin
                    tally the action taken on WINNING episodes; seed a fresh Q to
                    prefer each bin's most-winning action. A denoised, reusable
                    rule set — "episodes -> schema" rather than "replay raw".

All arms are evaluated on the SAME heldout tasks. Primary metric = schema
transfer minus raw-replay transfer (does library-learning beat replay). Reuses
gridworld_wm verbatim (improve-not-rewrite). Seed family 998000+ (disjoint from
all others). Zero LLM.
"""
from __future__ import annotations

from collections import Counter
from operator import itemgetter
from random import Random
from typing import List, Sequence, Tuple

from spec_compiler.harness import Condition

from .gridworld_wm import (
    EPS_LO, EVAL_STARTS, MAX_STEPS, MINIMAL_SUFFICIENT, N_TRAIN, _step,
    build_suite, evaluate, train,
)

CONS_BASE_SEED = 998_000
SLOTS = MINIMAL_SUFFICIENT          # shared abstract representation for all arms
B_TRAIN = 120_000
B_CONS = 120_000                    # equal offline budget for replay vs schema
CONS_LOG: dict = {}


def _key_of(slots: Sequence[int]):
    return itemgetter(*slots) if len(slots) > 1 else (lambda f, _i=slots[0]: (f[_i],))


def consolidate_library(Q_base: dict, tasks, slots, episodes: int, rng: Random) -> dict:
    """Roll out the base greedy policy; per abstract bin, tally actions taken on
    WINNING episodes; return a fresh Q seeded to prefer each bin's most-winning
    action (tie -> lowest index). This is the reusable schema library."""
    key_of = _key_of(slots)
    wins_by_bin: dict = {}
    for ep in range(episodes):
        task = tasks[ep % len(tasks)]
        pos = task.free[rng.randrange(len(task.free))]
        traj = []
        won = False
        for _ in range(MAX_STEPS):
            k = key_of(task.feats[pos])
            q = Q_base.get(k)
            a = rng.randrange(4) if q is None else q.index(max(q))
            traj.append((k, a))
            pos, _r, done, win = _step(task, pos, a)
            if done:
                won = win
                break
        if won:
            for (k, a) in traj:
                wins_by_bin.setdefault(k, Counter())[a] += 1
    Q_schema: dict = {}
    for k, c in wins_by_bin.items():
        best_a, best_n = 0, -1
        for a in sorted(c):                 # lowest action index on tie
            if c[a] > best_n:
                best_a, best_n = a, c[a]
        q = [0.0, 0.0, 0.0, 0.0]
        q[best_a] = 1.0
        Q_schema[k] = q
    return Q_schema


def _three_arms(suite, rng: Random):
    """Return (base_tr, replay_tr, schema_tr) heldout transfer for one universe."""
    train_tasks, held = suite[:N_TRAIN], suite[N_TRAIN:]
    # base
    Q_base: dict = {}
    train(Q_base, train_tasks, SLOTS, B_TRAIN, rng)
    base_tr = evaluate(Q_base, held, SLOTS, EVAL_STARTS)
    # raw replay: low-exploration refinement over the same train tasks (NOT a
    # fresh high-exploration restart, which would unfairly corrupt the base)
    Q_replay = {k: list(v) for k, v in Q_base.items()}
    train(Q_replay, train_tasks, SLOTS, B_CONS, rng, eps_hi=EPS_LO, eps_lo=EPS_LO)
    replay_tr = evaluate(Q_replay, held, SLOTS, EVAL_STARTS)
    # schema library: consolidate experience into reusable rules
    Q_schema = consolidate_library(Q_base, train_tasks, SLOTS, B_CONS, rng)
    schema_tr = evaluate(Q_schema, held, SLOTS, EVAL_STARTS)
    return base_tr, replay_tr, schema_tr


def _make(name: str, kind: str) -> Condition:
    counter = {"i": 0}

    def run(rng: Random) -> float:
        i = counter["i"]
        counter["i"] += 1
        suite = build_suite(CONS_BASE_SEED + i)
        base_tr, replay_tr, schema_tr = _three_arms(suite, rng)
        CONS_LOG.setdefault(name, []).append(
            {"seed_index": i, "base": round(base_tr, 3),
             "raw_replay": round(replay_tr, 3), "schema_library": round(schema_tr, 3),
             "schema_minus_replay": round(schema_tr - replay_tr, 3),
             "schema_minus_base": round(schema_tr - base_tr, 3)})
        if kind == "schema_vs_base":
            return schema_tr - base_tr
        return schema_tr - replay_tr        # PRIMARY

    return Condition(name, run, name)


def consolidation() -> Tuple[List[Condition], str]:
    conditions = [
        _make("schema_vs_base", "schema_vs_base"),     # control: library vs no consolidation
        _make("schema_vs_replay", "schema_vs_replay"),  # PRIMARY: library vs raw replay
    ]
    return conditions, "schema_vs_replay"


# ---------------------------------------------------------------- smoke
if __name__ == "__main__":
    import json
    import time
    B_TRAIN = 60_000       # noqa: F811  (smaller for smoke)
    B_CONS = 60_000        # noqa: F811
    t0 = time.time()
    suite = build_suite(CONS_BASE_SEED)
    b, r, s = _three_arms(suite, Random(0))
    print(json.dumps({"base": round(b, 3), "raw_replay": round(r, 3),
                      "schema_library": round(s, 3),
                      "schema_minus_replay": round(s - r, 3),
                      "schema_minus_base": round(s - b, 3)}, indent=1))
    print(f"total {time.time()-t0:.1f}s")
