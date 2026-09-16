"""
REAL experiment for specs/memory_policy.yaml — H-OWN-06 / EXP-003b.

Tests the raw claim H-OWN-06: writing / retrieving / forgetting are
RESOURCE-RATIONAL DECISIONS, not indiscriminate database operations. If memory
is a decision policy, then under a BOUNDED store the WRITE/RETENTION rule must
matter: keeping the entries with the highest retention utility should transfer
better, at EQUAL capacity, than writing everything and evicting blindly. If the
store is unbounded there is no decision to make, so the advantage must vanish.

Design (fully reuses gridworld_wm — improve-not-rewrite):
  1. Train a competent base policy: tabular Q on the minimal-sufficient abstract
     representation (MINIMAL_SUFFICIENT, the same 6-slot key consolidation uses),
     on the train tasks of a grid-world universe.
  2. Roll out the base greedy policy on the train tasks and CONSOLIDATE it into a
     pool of episodic entries: for every abstract state-key seen on a WINNING
     trajectory, store (key -> majority winning action) and a retention weight =
     how often that key is visited on winning trajectories (its need-probability,
     a proxy for how often the SAME-family heldout tasks will need it — Anderson's
     rational analysis of memory). NB: this weight is derived from the SAME
     winning-success signal that eval later scores, so it is train-COUPLED, not an
     independent/unbiased estimate (see the objective-coupling guard below).
  3. COMPRESS the pool to a fixed capacity C by three write/retention policies:
       append_all  capacity-BLIND: a uniformly random C-subset of the pool
                   (writes indiscriminately, forgets without regard to utility —
                   the "database op" null).
       recency     capacity-blind but deterministic FIFO: keep the C
                   most-recently-DISCOVERED keys (evict-oldest, the natural DB
                   default). Discriminating control: shows the advantage is about
                   UTILITY, not merely "any non-random rule beats random".
       gated       resource-rational: keep the top-C keys by retention weight.
  4. Evaluate each compressed memory AS A POLICY on the SAME heldout tasks
     (memory hit -> stored action; miss -> CRC-seeded random fallback), using
     gridworld's frozen evaluate() verbatim. Fewer / worse-chosen entries -> more
     misses -> more random fallback -> lower success.

Primary metric = gated_success_advantage = success(gated) − success(append_all)
at EQUAL bounded capacity C (paired, same universe, same pool). Storage is held
equal, so "success per unit stored" reduces to the success difference at fixed C.

Non-strawman guards:
  - null_unbounded: the SAME gated−append_all delta at capacity ≥ pool size. Both
    policies then keep the ENTIRE pool -> identical memory -> delta is exactly 0.
    This proves the advantage is CAUSED by capacity pressure, not by the gate
    mechanism per se (the "no pressure -> gate ~0" control the hypothesis demands).
  - gated_vs_recency: gated − recency at bounded C. Recency is a deterministic,
    capacity-blind DB policy (evict oldest). If gated beats even recency, the
    edge is specifically about retention UTILITY, rebutting "the random baseline
    is a strawman". Reported control, outside the machine verdict.
  - Genuine falsifiability: success is a TRAJECTORY-level property (you need a
    correct action at EVERY key along the path to the goal). Keeping the
    individually-most-needed keys does NOT guarantee whole successful paths are
    preserved, so the gated advantage can come out ≤ 0. It is not a
    near-guaranteed-positive quantity.
  - Objective coupling (disclosed): the retention weight is derived from WINNING
    training trajectories and eval scores WINNING success, so the utility signal
    is coupled to the objective it is later scored on — part of gated's edge may
    reflect that coupling, not pure resource-rationality. The null_unbounded=0
    control still rules out a spurious extra-capacity artifact (unbounded -> all
    rules keep the whole pool -> delta exactly 0), so the advantage is
    capacity-pressure driven; but the utility estimate itself is NOT eval-independent.
  - Weak primary baseline (disclosed): the machine gate (gated_advantage) is
    measured against append_all = RANDOM eviction, the weakest baseline. The
    stronger deterministic FIFO baseline is the reported-only gated_vs_recency
    control above (gated beats it too, so the edge is utility-specific).

Determinism: EVERYTHING (base training, pool rollout, random subset) is seeded
from CRCs of the per-condition call counter i, NOT from the harness RNG (whose
seed differs by condition name). So for seed-index i every condition sees the
identical universe, base policy and pool; conditions differ ONLY in the
write/retention rule. The (universe, pool) is memoized per i so the three
conditions share one build. Pilot family 983500 (disjoint) set the bands;
confirmatory family 983000+ was never piloted. Zero LLM.

SCOPE: C0/C1 — episodic-store retention as a policy over a fixed abstract
representation. No claim about phenomenal memory or per-timestep write dynamics
inside an LLM; "utility" here is functional need-probability only.
"""
from __future__ import annotations

import zlib
from collections import Counter
from operator import itemgetter
from random import Random
from typing import Dict, List, Sequence, Tuple

from spec_compiler.harness import Condition

from .gridworld_wm import (
    EVAL_STARTS, MAX_STEPS, MINIMAL_SUFFICIENT, N_TRAIN, _step,
    build_suite, evaluate, train,
)

MEM_BASE_SEED = 983_000          # CONFIRMATORY family (disjoint from all others);
                                 # pilot/calibration used 983_500 (never confirmatory)
SLOTS = MINIMAL_SUFFICIENT       # shared abstract representation (6 slots)
B_TRAIN = 80_000                 # base-policy Q-learning episodes (FROZEN)
POOL_ROLLOUTS = 40_000           # greedy rollouts consolidated into the pool (FROZEN)
CAPACITY = 60                    # bounded store size C (FROZEN from pilot pressure)
UNBOUNDED = 100_000              # ≥ any pool size -> no capacity pressure (null)

MEM_LOG: dict = {}
_UNIVERSE_CACHE: dict = {}       # i -> (held, pool, weight, order); deterministic per i


def _key_of(slots: Sequence[int]):
    return itemgetter(*slots) if len(slots) > 1 else (lambda f, _i=slots[0]: (f[_i],))


def build_pool(Q_base: dict, tasks, slots: Sequence[int], episodes: int,
               rng: Random) -> Tuple[Dict, Dict, Dict]:
    """Consolidate the base greedy policy into an episodic pool.
    Returns (pool, weight, order):
      pool[k]   = majority action taken at key k on WINNING trajectories
      weight[k] = visitation count of k on winning trajectories (retention utility)
      order[k]  = first-encounter tick of k (for the recency / FIFO control)"""
    key_of = _key_of(slots)
    votes: Dict[tuple, Counter] = {}
    weight: Dict[tuple, int] = {}
    order: Dict[tuple, int] = {}
    tick = 0
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
                if k not in order:
                    order[k] = tick
                    tick += 1
                votes.setdefault(k, Counter())[a] += 1
                weight[k] = weight.get(k, 0) + 1
    pool: Dict[tuple, int] = {}
    for k, c in votes.items():
        best_a, best_n = 0, -1
        for a in sorted(c):                 # tie -> lowest action index
            if c[a] > best_n:
                best_a, best_n = a, c[a]
        pool[k] = best_a
    return pool, weight, order


def _as_Q(mem: Dict[tuple, int]) -> dict:
    """A memory {key->action} becomes a one-hot Q so gridworld.evaluate() can run
    it verbatim (argmax = stored action; a miss returns None -> random fallback)."""
    Q: dict = {}
    for k, a in mem.items():
        q = [0.0, 0.0, 0.0, 0.0]
        q[a] = 1.0
        Q[k] = q
    return Q


def _gated(pool, weight, C):
    keys = sorted(pool.keys(), key=lambda k: (-weight.get(k, 0), k))[:C]
    return {k: pool[k] for k in keys}


def _append_all(pool, C, rng):
    keys = sorted(pool.keys())              # deterministic base order
    rng.shuffle(keys)
    return {k: pool[k] for k in keys[:C]}


def _recency(pool, order, C):
    keys = sorted(pool.keys(), key=lambda k: (-order.get(k, 0), k))[:C]
    return {k: pool[k] for k in keys}


def _universe(i: int):
    """Deterministically build (held, pool, weight, order) for seed-index i.
    Memoized so the three conditions share one build per i."""
    if i in _UNIVERSE_CACHE:
        return _UNIVERSE_CACHE[i]
    suite = build_suite(MEM_BASE_SEED + i)
    train_tasks, held = suite[:N_TRAIN], suite[N_TRAIN:]
    Q_base: dict = {}
    train(Q_base, train_tasks, SLOTS, B_TRAIN, Random(zlib.crc32(f"base|{i}".encode())))
    pool, weight, order = build_pool(
        Q_base, train_tasks, SLOTS, POOL_ROLLOUTS,
        Random(zlib.crc32(f"pool|{i}".encode())))
    out = (held, pool, weight, order)
    _UNIVERSE_CACHE[i] = out
    return out


def _delta(i: int, C: int, other: str) -> Tuple[float, float, dict]:
    """gated success minus `other` success at capacity C on heldout, for
    universe i. other in {'append_all','recency'}. Returns (acc_gated, acc_other,
    log-dict)."""
    held, pool, weight, order = _universe(i)
    C_eff = min(C, len(pool))
    mem_g = _gated(pool, weight, C_eff)
    if other == "recency":
        mem_o = _recency(pool, order, C_eff)
    else:
        mem_o = _append_all(pool, C_eff, Random(zlib.crc32(f"append|{i}|{C}".encode())))
    acc_g = evaluate(_as_Q(mem_g), held, SLOTS, EVAL_STARTS)
    acc_o = evaluate(_as_Q(mem_o), held, SLOTS, EVAL_STARTS)
    return acc_g, acc_o, {"pool_size": len(pool), "capacity": C_eff}


def _make(name: str, kind: str) -> Condition:
    counter = {"i": 0}

    def run(_rng: Random) -> float:
        i = counter["i"]
        counter["i"] += 1
        if kind == "null":
            acc_g, acc_o, meta = _delta(i, UNBOUNDED, "append_all")
        elif kind == "recency":
            acc_g, acc_o, meta = _delta(i, CAPACITY, "recency")
        else:                                   # gated_advantage (PRIMARY)
            acc_g, acc_o, meta = _delta(i, CAPACITY, "append_all")
        delta = acc_g - acc_o
        MEM_LOG.setdefault(name, []).append(
            {"seed_index": i, "gated": round(acc_g, 3),
             "other": round(acc_o, 3), "delta": round(delta, 3), **meta})
        return delta

    return Condition(name, run, name)


def memory_policy() -> Tuple[List[Condition], str]:
    conditions = [
        _make("null_unbounded", "null"),        # control: no pressure -> ~0
        _make("gated_vs_recency", "recency"),   # discriminating control (utility, not just structure)
        _make("gated_advantage", "gated"),      # PRIMARY: gated − append_all @ equal bounded C
    ]
    return conditions, "gated_advantage"


REGISTRY_REAL = {"memory_policy": memory_policy}


# ---------------------------------------------------------------- smoke / pilot
if __name__ == "__main__":
    import json
    import sys
    import time

    t0 = time.time()

    if "--calibrate" in sys.argv:
        # PILOT: disjoint family 983500; measure pool size and the delta across a
        # capacity sweep to set honest, frozen bands. NOT the confirmatory family.
        PILOT = 983_500
        suite = build_suite(PILOT)
        train_tasks, held = suite[:N_TRAIN], suite[N_TRAIN:]
        Q_base: dict = {}
        train(Q_base, train_tasks, SLOTS, B_TRAIN, Random(zlib.crc32(b"base|pilot")))
        pool, weight, order = build_pool(
            Q_base, train_tasks, SLOTS, POOL_ROLLOUTS, Random(zlib.crc32(b"pool|pilot")))
        full_acc = evaluate(_as_Q(pool), held, SLOTS, EVAL_STARTS)
        print(f"pool_size={len(pool)}  full_pool_heldout_acc={full_acc:.3f}  "
              f"({time.time()-t0:.1f}s)")
        for C in (20, 40, 60, 80, 120, 200, 100_000):
            Ce = min(C, len(pool))
            g = evaluate(_as_Q(_gated(pool, weight, Ce)), held, SLOTS, EVAL_STARTS)
            a = evaluate(_as_Q(_append_all(pool, Ce, Random(zlib.crc32(f"ap|{C}".encode())))),
                         held, SLOTS, EVAL_STARTS)
            r = evaluate(_as_Q(_recency(pool, order, Ce)), held, SLOTS, EVAL_STARTS)
            print(f"  C={C:<7} gated={g:.3f}  append_all={a:.3f}  recency={r:.3f}  "
                  f"| gated-append={g-a:+.3f}  gated-recency={g-r:+.3f}")
        print(f"total {time.time()-t0:.1f}s")

    else:
        # quick single-seed confirmatory-family check
        conditions, primary = memory_policy()
        for c in conditions:
            v = c.run(Random(0))
            print(f"{c.name:<20} delta={v:+.3f}")
        print(json.dumps(MEM_LOG, indent=1))
        print(f"total {time.time()-t0:.1f}s")
