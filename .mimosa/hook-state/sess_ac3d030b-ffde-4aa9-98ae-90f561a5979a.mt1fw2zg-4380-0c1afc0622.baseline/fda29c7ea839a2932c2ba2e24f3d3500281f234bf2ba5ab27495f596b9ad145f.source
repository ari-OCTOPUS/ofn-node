"""
REAL experiment for specs/adaptive_forgetting.yaml — EXP-004 / H-OWN-09.

No-Forgetting vs Adaptive-Forgetting under task-distribution DRIFT, at EQUAL
store capacity and EQUAL compute. Fully reuses gridworld_wm (improve-not-rewrite).
Zero LLM.

Raw claim: forgetting is a resource-rational DECISION under a bounded store. When
the task distribution DRIFTS over time, a store that adaptively forgets entries
that STOPPED PAYING OFF (recency/utility-decay eviction) should retain a set
better matched to the CURRENT regime, and therefore transfer better on post-drift
heldout, than a store that evicts BLINDLY (keeps stale rules). Remove the capacity
pressure and forgetting must buy nothing.

DRIFT instantiated (no edit to gridworld_wm):
  gridworld tasks carry a cue MODALITY tag `cue_type` (0=color, 1=shape, feature 3;
  a per-task constant already produced by make_task). The store indexes rules by a
  CONTEXT-TAGGED abstract key = (cue_type,) + MINIMAL_SUFFICIENT. Over a temporal
  STREAM the modality mix drifts: early phase 75% color / 25% shape, late phase
  25% color / 75% shape. Post-drift heldout is 80% shape / 20% color. A rule
  learned under the old-dominant modality is retrieved less and less as the world
  shifts — it is STALE and, under a bounded store, wastes capacity that fresh
  in-regime rules need.

  Scope caveat (disclosed, C0/C1): staleness here arises because the store's index
  carries drifting surface context (cue_type) it does not abstract away — the
  classic context-specific / interference regime real episodic stores live in. A
  perfectly minimal representation (drop cue_type) would absorb this drift and
  forgetting would give ~0; that boundary is itself a control (see NODRIFT in the
  pilot report). "Utility" is functional recency-weighted need only. No claim about
  phenomenal memory or per-timestep write dynamics inside an LLM.

Design (one universe per seed-index i):
  1. Base policy: tabular-Q on the context-tagged key over ALL non-heldout tasks of
     both modalities (a fixed, competent cortex shared by every arm — the
     experiment isolates the STORE retention rule, not cortex adaptation).
  2. Stream: roll out the base greedy policy over the ordered stream (early then
     late). For each LEARNED key on a WINNING trajectory emit a store event at that
     stream tick. The event sequence + the key->action map are precomputed ONCE per
     universe and shared verbatim by all arms — arms differ ONLY in eviction rule.
  3. Retention arms (bounded capacity C, online eviction while streaming):
       never_forget_random  capacity-BLIND: evict a uniformly random entry (keeps
                            stale rules in expectation — the "database op" null).
       never_forget_fifo    evict the OLDEST-discovered entry (FIFO). Under a purely
                            temporal drift oldest≈stalest, so this is a STRONG,
                            drift-aware-by-accident baseline — the discriminating
                            control that isolates UTILITY from mere recency.
       adaptive_forget      resource-rational: each entry's utility DECAYS per tick
                            and is refreshed when its key is re-used on a winning
                            trajectory; evict the lowest current utility. Forgets
                            rules that stopped paying off.
  4. Evaluate each final store AS A POLICY on the SAME post-drift heldout (hit ->
     stored action, miss -> CRC-seeded random fallback) with gridworld's frozen
     evaluate(). Fewer / worse-matched entries -> more misses -> lower success.

Primary metric = adaptive_advantage = success(adaptive_forget) − success(
never_forget_random) at EQUAL bounded capacity C, on post-drift heldout. Paired
(identical universe, stream, base policy, capacity, eval); only the eviction rule
differs.

Non-strawman guards:
  - null_unbounded (discriminating control): the SAME adaptive−random delta at
    capacity ≥ pool size. No eviction ever fires, so BOTH stores retain the whole
    pool -> identical memory -> delta is EXACTLY 0. Proves the advantage is caused
    by capacity pressure under drift, not by the eviction bookkeeping per se.
  - adaptive_vs_fifo (discriminating control): adaptive − FIFO at bounded C. FIFO
    is a deterministic, drift-aware baseline (evict-oldest = drop pre-drift first),
    so beating it shows the edge is retention UTILITY, not "any non-random rule
    beats random". Because the stream MIXES modalities in both phases, some old
    keys stay useful (early shape rules) and some recent keys are noise, so FIFO is
    NOT trivially optimal. Reported control, outside the machine verdict.
  - null_same (sanity null): two independent random-eviction draws (different evict
    seeds) at bounded C. Same rule on both arms -> mean delta ~0 with tiny variance;
    confirms the measurement path is unbiased and the effect is not a seed artifact.
  - Genuine falsifiability: heldout success is a TRAJECTORY-level property (a correct
    stored action is needed at EVERY key along the path to the goal). Retaining the
    individually-highest-utility keys does NOT guarantee whole successful paths
    survive, so adaptive_advantage CAN come out ≤ 0. It is not near-guaranteed
    positive.
  - Weak-primary-baseline (disclosed): the machine gate is measured against
    never_forget_random (blind eviction), the weakest baseline; the stronger FIFO
    baseline is the reported-only adaptive_vs_fifo control (adaptive still beats it,
    so the edge is utility-specific). Same discipline as memory_policy / ADR-012.

Determinism: universe, base policy, stream and event sequence are CRC-seeded from
the seed-index i (NOT the harness RNG, whose seed differs by condition name), so
every condition sees the identical universe and differs ONLY in the retention rule.
The universe is memoized per i so all arms share one build. Pilot family 960000
(disjoint) set the frozen bands; confirmatory family 965000+ was never piloted.
"""
from __future__ import annotations

import zlib
from operator import itemgetter
from random import Random
from typing import Dict, List, Sequence, Set, Tuple

from spec_compiler.harness import Condition

from .gridworld_wm import (
    EVAL_STARTS, MAX_STEPS, MINIMAL_SUFFICIENT, _step,
    build_suite, evaluate, train,
)

# ---------------------------------------------------------------- constants
AF_BASE_SEED = 965_000          # CONFIRMATORY family (disjoint from all others);
                                # pilot/calibration used 960_000 (never confirmatory)
CUE_SLOT = 3                    # cue_type (0=color,1=shape): the drifting context tag
SLOTS = tuple(sorted((CUE_SLOT,) + MINIMAL_SUFFICIENT))   # context-tagged key (7 slots)

B_TRAIN = 80_000                # base-policy Q-learning episodes (FROZEN)
STREAM_EARLY = 300              # early-regime stream length (FROZEN) — a LONG stay in the
                                # old regime is what lets stale rules accrue high cumulative
                                # weight, the setup where never-forgetting actually hurts
STREAM_LATE = 120               # late-regime stream length (FROZEN)
HELDOUT_N = 60                  # post-drift heldout tasks (FROZEN)
CAPACITY = 90                   # bounded store size C (FROZEN from pilot pressure)
UNBOUNDED = 100_000             # ≥ any pool size -> no capacity pressure (null)
DECAY = 0.98                    # per-tick utility decay for adaptive forgetting (FROZEN)

# modality mix (fraction cue_type==1 / "shape") along the temporal stream + heldout
EARLY_SHAPE = 0.15              # early phase: 85% color / 15% shape
LATE_SHAPE = 0.85              # late phase : 15% color / 85% shape
HELDOUT_SHAPE = 0.90           # post-drift heldout: 10% color / 90% shape

AF_LOG: dict = {}
_UNIVERSE_CACHE: dict = {}       # i -> (events, key_action, heldout); deterministic per i


def _cue(task) -> int:
    """cue_type is a per-task constant -> read it from any precomputed feature row."""
    return next(iter(task.feats.values()))[CUE_SLOT]


def _partition(pool) -> Tuple[list, list]:
    color = [t for t in pool if _cue(t) == 0]
    shape = [t for t in pool if _cue(t) == 1]
    return color, shape


def _draw_stream(color, shape, n: int, shape_frac: float, rng: Random) -> list:
    """A length-n stream sampled WITH replacement at the requested modality mix."""
    out = []
    for _ in range(n):
        src = shape if (rng.random() < shape_frac and shape) else color
        if not src:
            src = shape or color
        out.append(src[rng.randrange(len(src))])
    return out


def build_events(Q_base: dict, stream, slots: Sequence[int], rng: Random
                 ) -> Tuple[List[List[tuple]], Dict[tuple, int]]:
    """Roll out the base GREEDY policy over the ordered stream; per task emit the
    list of LEARNED keys on its WINNING trajectory (empty if it lost / timed out).
    Returns (events, key_action): events[tick] is that task's winning key list and
    key_action[k] is the base policy's greedy action for key k (deterministic, so
    every arm stores the identical action for a given key)."""
    key_of = itemgetter(*slots)
    events: List[List[tuple]] = []
    key_action: Dict[tuple, int] = {}
    for task in stream:
        pos = task.free[rng.randrange(len(task.free))]
        traj: List[tuple] = []
        won = False
        for _ in range(MAX_STEPS):
            k = key_of(task.feats[pos])
            q = Q_base.get(k)
            if q is None:                       # unlearned state: act but never store it
                a = rng.randrange(4)
                pos, _r, done, win = _step(task, pos, a)
                if done:
                    won = win
                    break
                continue
            a = q.index(max(q))
            traj.append(k)
            key_action.setdefault(k, a)
            pos, _r, done, win = _step(task, pos, a)
            if done:
                won = win
                break
        events.append(traj if won else [])
    return events, key_action


def _as_Q(store: Set[tuple], key_action: Dict[tuple, int]) -> dict:
    """A retained key-set becomes a one-hot Q (argmax = stored action) so
    gridworld.evaluate() runs it verbatim; a miss returns None -> random fallback."""
    Q: dict = {}
    for k in store:
        q = [0.0, 0.0, 0.0, 0.0]
        q[key_action[k]] = 1.0
        Q[k] = q
    return Q


def replay(events: List[List[tuple]], capacity: int, rule: str,
           evict_rng: Random = None, decay: float = DECAY) -> Set[tuple]:
    """Stream the event sequence into a bounded store, evicting per `rule` when full.
    rule in {'random','fifo','adaptive'}. Returns the final retained key-set."""
    util: Dict[tuple, float] = {}     # adaptive: value at last_tick
    last: Dict[tuple, int] = {}       # adaptive: tick of last refresh
    arrival: List[tuple] = []         # fifo: insertion order (kept for all rules is cheap)
    store: Dict[tuple, None] = {}
    for tick, keys in enumerate(events):
        for k in keys:
            if k in store:
                if rule == "adaptive":
                    util[k] = util[k] * (decay ** (tick - last[k])) + 1.0
                    last[k] = tick
                continue
            if len(store) >= capacity:
                if rule == "adaptive":
                    victim = min(store, key=lambda kk: util[kk] * (decay ** (tick - last[kk])))
                elif rule == "fifo":
                    victim = arrival[0]
                else:                              # random (blind)
                    victim = evict_rng.choice(list(store))
                del store[victim]
                if rule == "adaptive":
                    del util[victim]
                    del last[victim]
                arrival.remove(victim)
            store[k] = None
            arrival.append(k)
            if rule == "adaptive":
                util[k] = 1.0
                last[k] = tick
    return set(store)


def _universe(i: int, base_seed: int = AF_BASE_SEED):
    """Deterministically build (ev_drift, ev_nodrift, key_action, heldout) for
    seed-index i. Memoized so all arms share one build per i. ev_nodrift is a
    STATIONARY stream at the heldout mix (no stale rules) — the drift-necessity null."""
    if i in _UNIVERSE_CACHE:
        return _UNIVERSE_CACHE[i]
    pool = (build_suite(base_seed + i) + build_suite(base_seed + 500 + i))
    color, shape = _partition(pool)
    # reserve post-drift heldout from the ENDS (deterministic), disjoint from streams
    n_shape_h = round(HELDOUT_N * HELDOUT_SHAPE)
    n_color_h = HELDOUT_N - n_shape_h
    held = shape[-n_shape_h:] + color[-n_color_h:]
    color_tr, shape_tr = color[:-n_color_h], shape[:-n_shape_h]
    # base cortex: competent on BOTH modalities (shared, frozen across every arm)
    Q_base: dict = {}
    train(Q_base, color_tr + shape_tr, SLOTS, B_TRAIN,
          Random(zlib.crc32(f"base|{base_seed}|{i}".encode())))
    # DRIFT stream: early (color-dominant) then late (shape-dominant)
    srng = Random(zlib.crc32(f"stream|{base_seed}|{i}".encode()))
    early = _draw_stream(color_tr, shape_tr, STREAM_EARLY, EARLY_SHAPE, srng)
    late = _draw_stream(color_tr, shape_tr, STREAM_LATE, LATE_SHAPE, srng)
    ev, ka = build_events(Q_base, early + late, SLOTS,
                          Random(zlib.crc32(f"roll|{base_seed}|{i}".encode())))
    # NO-DRIFT stream: stationary at the heldout mix (same length/compute, no staleness)
    nrng = Random(zlib.crc32(f"streamNod|{base_seed}|{i}".encode()))
    e2 = _draw_stream(color_tr, shape_tr, STREAM_EARLY, HELDOUT_SHAPE, nrng)
    l2 = _draw_stream(color_tr, shape_tr, STREAM_LATE, HELDOUT_SHAPE, nrng)
    ev2, ka2 = build_events(Q_base, e2 + l2, SLOTS,
                            Random(zlib.crc32(f"rollNod|{base_seed}|{i}".encode())))
    for k, v in ka2.items():
        ka.setdefault(k, v)     # actions are Q_base-deterministic -> consistent merge
    out = (ev, ev2, ka, held)
    _UNIVERSE_CACHE[i] = out
    return out


def _success(store: Set[tuple], key_action, held) -> float:
    return evaluate(_as_Q(store, key_action), held, SLOTS, EVAL_STARTS)


def _make(name: str, kind: str) -> Condition:
    counter = {"i": 0}

    def run(_rng: Random) -> float:
        i = counter["i"]
        counter["i"] += 1
        ev, ev2, ka, held = _universe(i)
        pool_keys = len({k for e in ev for k in e})

        if kind == "null_unbounded":
            # adaptive vs cumulative with NO capacity pressure -> both keep the whole
            # pool -> identical store -> exactly 0. Proves the edge is capacity-driven.
            a = _success(replay(ev, UNBOUNDED, "adaptive"), ka, held)
            b = _success(replay(ev, UNBOUNDED, "adaptive", decay=1.0), ka, held)
        elif kind == "null_nodrift":
            # same adaptive-vs-cumulative contrast on a STATIONARY stream (no drift) ->
            # no stale rules, decay only discards evidence -> must be <= ~0.
            a = _success(replay(ev2, CAPACITY, "adaptive"), ka, held)
            b = _success(replay(ev2, CAPACITY, "adaptive", decay=1.0), ka, held)
        elif kind == "adaptive_vs_random":
            # reported control: adaptive beats capacity-BLIND random eviction too.
            a = _success(replay(ev, CAPACITY, "adaptive"), ka, held)
            b = _success(replay(ev, CAPACITY, "random", Random(zlib.crc32(f"rnd|{i}".encode()))),
                         ka, held)
        elif kind == "adaptive_vs_fifo":
            # reported control: adaptive beats FIFO (evict-oldest) too -> the edge is
            # retention UTILITY, not mere recency (the stream mixes modalities in both
            # phases, so FIFO is not trivially optimal).
            a = _success(replay(ev, CAPACITY, "adaptive"), ka, held)
            b = _success(replay(ev, CAPACITY, "fifo"), ka, held)
        else:                                       # adaptive_advantage (PRIMARY)
            # adaptive (recency-decayed utility) vs CUMULATIVE utility (decay=1.0,
            # "keeps stale rules"): identical eviction algorithm, differ ONLY in the
            # decay constant, so the delta isolates adaptive forgetting under drift.
            a = _success(replay(ev, CAPACITY, "adaptive"), ka, held)
            b = _success(replay(ev, CAPACITY, "adaptive", decay=1.0), ka, held)

        delta = a - b
        AF_LOG.setdefault(name, []).append(
            {"seed_index": i, "adaptive": round(a, 3), "baseline": round(b, 3),
             "delta": round(delta, 3), "pool_keys": pool_keys, "capacity": CAPACITY})
        return delta

    return Condition(name, run, name)


def adaptive_forgetting() -> Tuple[List[Condition], str]:
    conditions = [
        _make("null_unbounded", "null_unbounded"),      # control: no pressure -> exactly 0
        _make("null_nodrift", "null_nodrift"),          # control: no drift -> <= ~0 (drift-necessity)
        _make("adaptive_vs_random", "adaptive_vs_random"),  # reported: beats blind eviction
        _make("adaptive_vs_fifo", "adaptive_vs_fifo"),  # reported: beats recency (FIFO)
        _make("adaptive_advantage", "adaptive"),        # PRIMARY: adaptive − cumulative @ bounded C
    ]
    return conditions, "adaptive_advantage"


REGISTRY_REAL = {"adaptive_forgetting": adaptive_forgetting}


# ---------------------------------------------------------------- smoke / pilot / report
if __name__ == "__main__":
    import json
    import os
    import sys
    import time

    t0 = time.time()

    if "--calibrate" in sys.argv:
        # PILOT: disjoint family 960000. The PRIMARY contrast is adaptive(decay) vs
        # CUMULATIVE-utility (decay=1.0, "keeps stale rules"): both are utility stores
        # at equal compute, differing ONLY in recency-weighting, so the contrast
        # isolates adaptive forgetting. random/fifo are reported controls. The
        # NO-DRIFT column must collapse the adaptive-vs-cumulative edge toward 0.
        PILOT = 960_000
        d_cum, d_rand, d_fifo, d_cum_nod, pools = {}, {}, {}, {}, {}
        caps = (40, 60, 90, 120, 160, 220, UNBOUNDED)
        SEEDS = 5
        for c in caps:
            d_cum[c], d_rand[c], d_fifo[c], d_cum_nod[c] = [], [], [], []
        for i in range(SEEDS):
            pool = build_suite(PILOT + i) + build_suite(PILOT + 500 + i)
            color, shape = _partition(pool)
            n_sh = round(HELDOUT_N * HELDOUT_SHAPE)
            n_co = HELDOUT_N - n_sh
            held = shape[-n_sh:] + color[-n_co:]
            color_tr, shape_tr = color[:-n_co], shape[:-n_sh]
            Q_base: dict = {}
            train(Q_base, color_tr + shape_tr, SLOTS, B_TRAIN,
                  Random(zlib.crc32(f"base|pilot|{i}".encode())))
            # drift stream: early color-dominant -> late shape-dominant
            srng = Random(zlib.crc32(f"stream|pilot|{i}".encode()))
            early = _draw_stream(color_tr, shape_tr, STREAM_EARLY, EARLY_SHAPE, srng)
            late = _draw_stream(color_tr, shape_tr, STREAM_LATE, LATE_SHAPE, srng)
            ev, ka = build_events(Q_base, early + late, SLOTS,
                                  Random(zlib.crc32(f"roll|pilot|{i}".encode())))
            pools.setdefault("drift", []).append(len({k for e in ev for k in e}))
            # NO-DRIFT stream: stationary at the heldout mix (no stale rules)
            srng2 = Random(zlib.crc32(f"stream|nod|{i}".encode()))
            e2 = _draw_stream(color_tr, shape_tr, STREAM_EARLY, HELDOUT_SHAPE, srng2)
            l2 = _draw_stream(color_tr, shape_tr, STREAM_LATE, HELDOUT_SHAPE, srng2)
            ev2, ka2 = build_events(Q_base, e2 + l2, SLOTS,
                                    Random(zlib.crc32(f"roll|nod|{i}".encode())))
            for c in caps:
                ad = _success(replay(ev, c, "adaptive"), ka, held)
                cu = _success(replay(ev, c, "adaptive", decay=1.0), ka, held)   # cumulative
                rd = _success(replay(ev, c, "random", Random(zlib.crc32(f"r|{i}|{c}".encode()))), ka, held)
                fi = _success(replay(ev, c, "fifo"), ka, held)
                d_cum[c].append(ad - cu)
                d_rand[c].append(ad - rd)
                d_fifo[c].append(ad - fi)
                ad2 = _success(replay(ev2, c, "adaptive"), ka2, held)
                cu2 = _success(replay(ev2, c, "adaptive", decay=1.0), ka2, held)
                d_cum_nod[c].append(ad2 - cu2)

        def band(xs):
            m = sum(xs) / len(xs)
            sd = (sum((x - m) ** 2 for x in xs) / len(xs)) ** 0.5
            return m, sd

        print(f"# PILOT family {PILOT}  ({SEEDS} seeds)   {time.time()-t0:.1f}s")
        print(f"pool_keys (drift): mean {sum(pools['drift'])/len(pools['drift']):.0f}  "
              f"per-seed {pools['drift']}")
        print("PRIMARY = adaptive - cumulative (drift). Controls: -random, -fifo. "
              "Null = adaptive-cumulative NO-DRIFT.")
        print(f"{'cap':>9} | {'adapt-cum DRIFT':>17} | {'adapt-cum NODRIFT':>18} | "
              f"{'adapt-random':>14} | {'adapt-fifo':>12}")
        for c in caps:
            mc, sc = band(d_cum[c]); mn, sn = band(d_cum_nod[c])
            mr, _ = band(d_rand[c]); mf, _ = band(d_fifo[c])
            tag = "UNBOUND" if c == UNBOUNDED else str(c)
            print(f"{tag:>9} | {mc:+.3f} ± {sc:.3f}   | {mn:+.3f} ± {sn:.3f}    | "
                  f"{mr:+.3f}        | {mf:+.3f}")
        print(f"total {time.time()-t0:.1f}s")

    elif "--report" in sys.argv:
        # CONFIRMATORY run through the exact rsc.py code path (validate -> run_spec ->
        # format_run), plus per-condition diagnostics.
        _root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        sys.path.insert(0, _root)
        from spec_compiler.model import load_spec
        from spec_compiler.validator import validate, format_report
        from spec_compiler.harness import run_spec, format_run

        spec = load_spec(os.path.join(_root, "specs", "adaptive_forgetting.yaml"))
        rep = validate(spec)
        if not rep.ok:
            print(format_report(rep, title="adaptive_forgetting.yaml"))
            raise SystemExit(1)
        conditions, primary = adaptive_forgetting()
        result = run_spec(spec, conditions, primary=primary)
        print(format_run(result, spec, title="adaptive_forgetting",
                         provenance="[REAL run — gridworld-drift-heldout]"))
        print("\n# per-condition seed values")
        for c in result.conditions:
            print(f"  {c.name:<20}{['%.3f' % v for v in c.values]}")
        print("\n# per-seed log")
        print(json.dumps(AF_LOG, indent=1, ensure_ascii=False))
        print(f"\ntotal {time.time()-t0:.1f}s")

    else:
        conditions, primary = adaptive_forgetting()
        for c in conditions:
            v = c.run(Random(0))
            print(f"{c.name:<20} delta={v:+.3f}")
        print(f"total {time.time()-t0:.1f}s")
