"""
REAL experiment for specs/multimetric_memory.yaml — SUBSTRATE for GEOMETRY.md §4.

اصل ۸ [P L667] says memory must index episodes by MORE than semantic similarity:
time, causality, provenance and outcome. GEOMETRY.md §4 formalizes this as a
MULTI-METRIC memory space `d_mem = (d_semantic, d_time, d_causal, d_provenance,
d_outcome)` and marks it [SPEC]. This module moves that object to [RUN]: a
deterministic episodic-retrieval experiment in which SEMANTIC-ONLY retrieval is
GENUINELY insufficient, because the stream contains semantic DUPLICATES that
differ only in recency / provenance-reliability / outcome.

Design (memory_policy.py lineage — full reuse of gridworld_wm, improve-not-rewrite):

  The episode stream is the agent's OWN experience history over three phases of
  its life, rolled out on the train tasks of a grid-world universe:

    phase 1 (EARLY, stale):      greedy rollouts of an under-trained Q snapshot
                                 (B_WEAK episodes of training) — old timestamps,
                                 low measured source-reliability, mostly losing.
    phase 2 (MID, trusted):      greedy rollouts of the converged Q — reliable
                                 source, mostly winning outcomes.
    phase 3 (LATE, poisoned):    greedy rollouts of a DIFFERENT under-trained
                                 snapshot — the MOST RECENT entries, yet
                                 unreliable and mostly losing. (This breaks the
                                 recency==quality shortcut: the newest memories
                                 are NOT the best ones.)

  Every episode contributes, once per distinct semantic key visited, an entry
  (semantic key, action, timestamp, source, outcome). Semantic key = the same
  6-slot minimal-sufficient abstract representation the sibling experiments use
  (MINIMAL_SUFFICIENT), so semantic duplicates are exact key collisions across
  phases: same situation, conflicting advice.

  Retrieval-as-policy on the SAME heldout tasks (evaluate() verbatim, miss ->
  CRC-seeded random fallback):

    semantic_only   nearest-neighbour in d_semantic alone: all entries with the
                    matching key are equidistant, so retrieval = plain majority
                    vote over ALL entries (frequency-weighted kNN — the natural,
                    NON-crippled semantic rule: it uses every datum, it just
                    cannot see time/provenance/outcome).
    multimetric     same semantic match, but among semantic ties each entry
                    votes with weight
                       w = W_REC*recency + W_PROV*reliability(source) + W_OUT*outcome
                    (equal thirds, FROZEN a priori; recency = normalized
                    timestamp in [0,1]; reliability = the source's MEASURED
                    train win-rate; outcome = did that episode win). This is the
                    weighted multi-metric combination of GEOMETRY.md §4.

PRIMARY metric = retrieval_advantage
              = success(multimetric) − success(semantic_only)  on heldout tasks.

Controls / non-strawman guards:
  - null_same_vs_same: success(semantic_only) − success(semantic_only), both
    sides recomputing the retrieval rule + evaluation over the SHARED memoized
    universe (the universe/stream build runs once per (family, i), not twice)
    -> must be EXACTLY 0 (determinism + no hidden asymmetry in the
    retrieval/eval path).
  - clean_stream_control (DISCRIMINATING): the same contrast on a CLEAN stream
    (phase-2 trusted rollouts only, re-timestamped as its own timeline). With no
    duplicates/poison the extra metrics have nothing to disambiguate ->
    multimetric must give ~0. Proves the advantage is CAUSED by the corrupted
    duplicates, not by the weighting machinery per se.
  - recency_only_gain (reported ablation, outside the verdict): semantic +
    recency alone. Phase 3 makes the newest entries poisoned, so recency-only
    must recover LESS than the full multimetric — the provenance/outcome axes
    JOINTLY carry non-redundant signal (they are not ablated separately; see
    disclosures).
  - Genuine falsifiability: the advantage is a difference of trajectory-level
    success rates and CAN come out <= 0 — e.g. down-weighting early experience
    also discards its correct votes at keys the converged policy rarely visits,
    and phase-1/3 coverage helps BOTH rules equally (identical key sets), so
    multimetric enjoys no coverage edge, only vote-ordering differences.

Honest disclosures:
  - d_causal is NOT instantiated: this substrate runs 4 of the 5 axes of
    GEOMETRY.md §4 (semantic, time, provenance, outcome). Causality needs an
    intervention structure the stream does not have; left [SPEC].
  - The three extra axes are CORRELATED by construction in phase 1 (old AND
    unreliable AND losing); phase 3 exists precisely to decorrelate recency
    from quality, and recency_only_gain quantifies the residual redundancy.
  - reliability(source) is MEASURED from the stream's own outcomes (win-rate),
    so the provenance axis is an outcome-derived prior at source granularity,
    not an independent oracle label.
  - NO per-axis ablation of provenance vs outcome: recency_only_gain switches
    BOTH off at once, and no provenance-only or outcome-only arm runs, so the
    result attributes the advantage to the provenance+outcome PAIR, not to
    either axis individually (ADR-018 confirmed caveat).

Determinism: EVERYTHING (suite, all Q training, all rollouts) is seeded from
CRCs of (family, seed-index i), NOT from the harness RNG, so for index i every
condition sees the identical universe and stream; conditions differ ONLY in the
retrieval rule. The universe is memoized per (family, i). Seed discipline
(ADR-001 style): pilot family 942_000 calibrated B_WEAK + stream volumes and
set the FROZEN bands — pilot gave retrieval_advantage +0.112 mean (min +0.067,
max +0.150), clean_delta exactly 0.000 on all 5 seeds, recency_only_gain
-0.033 [FACT: pilot log 2026-07-14]; the CONFIRMATORY family 942_500+ is
disjoint and was never piloted. Modest budget (~15 s per family on a laptop),
zero LLM, stdlib only.

SCOPE: C0/C1 — functional retrieval policy over an episodic store. No claim
about phenomenal memory. C0–C3 ⇏ C4 firewall respected.
"""
from __future__ import annotations

import zlib
from operator import itemgetter
from random import Random
from typing import Dict, List, Sequence, Tuple

from spec_compiler.harness import Condition

from .gridworld_wm import (
    EVAL_STARTS, MAX_STEPS, MINIMAL_SUFFICIENT, N_TRAIN, _step,
    build_suite, evaluate, train,
)
from .memory_policy import _as_Q  # memory {key->action} -> one-hot Q (reuse)

# ---------------------------------------------------------------- constants
MM_CONFIRM_FAMILY = 942_500   # CONFIRMATORY family (disjoint, never piloted)
MM_PILOT_FAMILY = 942_000     # pilot/calibration only — never confirmatory

SLOTS = MINIMAL_SUFFICIENT    # shared 6-slot semantic key (same as siblings)
B_STRONG = 80_000             # converged-policy training episodes (FROZEN)
B_WEAK = 400                  # under-trained snapshot episodes (FROZEN, pilot 942000)
ROLL_EARLY = 14_000           # phase-1 stale rollouts        (FROZEN, pilot 942000)
ROLL_STRONG = 8_000           # phase-2 trusted rollouts      (FROZEN, pilot 942000)
ROLL_LATE = 10_000            # phase-3 poisoned rollouts     (FROZEN, pilot 942000)
W_REC = W_PROV = W_OUT = 1.0 / 3.0   # equal thirds, fixed A PRIORI (not tuned)

SRC_EARLY, SRC_STRONG, SRC_LATE = 0, 1, 2

MM_LOG: dict = {}
_UNIVERSE_CACHE: dict = {}    # (family, i) -> universe tuple


def _key_of(slots: Sequence[int]):
    return itemgetter(*slots) if len(slots) > 1 else (lambda f, _i=slots[0]: (f[_i],))


# ---------------------------------------------------------------- stream
def _roll_into(stats: Dict, Q: dict, tasks, episodes: int, rng: Random,
               tick0: int, total_ticks: int, src: int) -> int:
    """Greedy rollouts of Q over tasks; accumulate the episode stream into
    stats[key][action] = [n_votes, sum_recency, n_wins, [n_early, n_mid, n_late]].
    Each episode contributes each distinct semantic key ONCE (its first (key,
    action) pair): a looping policy may burn all MAX_STEPS revisiting the same
    few keys, and letting it mass-vote would be a stream artifact, not memory
    content. Returns the number of winning episodes (for the measured
    source-reliability)."""
    key_of = _key_of(SLOTS)
    wins = 0
    for ep in range(episodes):
        rec = (tick0 + ep) / max(1, total_ticks - 1)
        task = tasks[ep % len(tasks)]
        pos = task.free[rng.randrange(len(task.free))]
        seen: Dict[tuple, int] = {}
        won = False
        for _ in range(MAX_STEPS):
            k = key_of(task.feats[pos])
            q = Q.get(k)
            a = rng.randrange(4) if q is None else q.index(max(q))
            if k not in seen:
                seen[k] = a
            pos, _r, done, win = _step(task, pos, a)
            if done:
                won = win
                break
        o = 1 if won else 0
        wins += o
        for k, a in seen.items():
            st = stats.setdefault(k, {}).setdefault(a, [0, 0.0, 0, [0, 0, 0]])
            st[0] += 1
            st[1] += rec
            st[2] += o
            st[3][src] += 1
    return wins


# ---------------------------------------------------------------- retrieval rules
def _mem_semantic(stats: Dict) -> Dict[tuple, int]:
    """d_semantic only: majority vote over all entries with the matching key
    (tie -> lowest action index)."""
    mem: Dict[tuple, int] = {}
    for k, acts in stats.items():
        best_a, best_v = None, -1.0
        for a in sorted(acts):
            v = float(acts[a][0])
            if v > best_v:
                best_a, best_v = a, v
        mem[k] = best_a
    return mem


def _mem_weighted(stats: Dict, rel: Sequence[float],
                  use_rec: bool = True, use_prov: bool = True,
                  use_out: bool = True) -> Dict[tuple, int]:
    """Weighted multi-metric vote among semantic ties (GEOMETRY.md §4):
    each entry's weight = W_REC*recency + W_PROV*rel(source) + W_OUT*outcome.
    Flags switch axes off for the ablation rules (tie -> lowest action)."""
    mem: Dict[tuple, int] = {}
    for k, acts in stats.items():
        best_a, best_v = None, -1.0
        for a in sorted(acts):
            n, sum_rec, n_win, per_src = acts[a]
            v = 0.0
            if use_rec:
                v += W_REC * sum_rec
            if use_prov:
                v += W_PROV * (per_src[0] * rel[0] + per_src[1] * rel[1]
                               + per_src[2] * rel[2])
            if use_out:
                v += W_OUT * n_win
            if v > best_v:
                best_a, best_v = a, v
        mem[k] = best_a
    return mem


# ---------------------------------------------------------------- universe
def _universe(i: int, family: int = MM_CONFIRM_FAMILY):
    """Deterministically build one universe for seed-index i:
    (held, stats_poisoned, stats_clean, rel, diag). Memoized per (family, i) so
    all conditions share one build. The clean stream REPLAYS the identical
    phase-2 rollouts (same CRC seed) re-timestamped as its own timeline."""
    ck = (family, i)
    if ck in _UNIVERSE_CACHE:
        return _UNIVERSE_CACHE[ck]
    suite = build_suite(family + i)
    train_tasks, held = suite[:N_TRAIN], suite[N_TRAIN:]

    def _crc(tag: str) -> Random:
        return Random(zlib.crc32(f"{tag}|{family}|{i}".encode()))

    Q_strong: dict = {}
    train(Q_strong, train_tasks, SLOTS, B_STRONG, _crc("strong"))
    Q_early: dict = {}
    train(Q_early, train_tasks, SLOTS, B_WEAK, _crc("early"))
    Q_late: dict = {}
    train(Q_late, train_tasks, SLOTS, B_WEAK, _crc("late"))

    total = ROLL_EARLY + ROLL_STRONG + ROLL_LATE
    stats: Dict = {}
    w_e = _roll_into(stats, Q_early, train_tasks, ROLL_EARLY, _crc("roll_early"),
                     0, total, SRC_EARLY)
    w_s = _roll_into(stats, Q_strong, train_tasks, ROLL_STRONG, _crc("roll_mid"),
                     ROLL_EARLY, total, SRC_STRONG)
    w_l = _roll_into(stats, Q_late, train_tasks, ROLL_LATE, _crc("roll_late"),
                     ROLL_EARLY + ROLL_STRONG, total, SRC_LATE)
    # CLEAN stream: identical trusted rollouts, own timeline, no duplicates/poison
    stats_clean: Dict = {}
    _roll_into(stats_clean, Q_strong, train_tasks, ROLL_STRONG, _crc("roll_mid"),
               0, ROLL_STRONG, SRC_STRONG)

    rel = (w_e / ROLL_EARLY, w_s / ROLL_STRONG, w_l / ROLL_LATE)
    diag = {"rel_early": round(rel[0], 3), "rel_mid": round(rel[1], 3),
            "rel_late": round(rel[2], 3), "keys": len(stats),
            "keys_clean": len(stats_clean)}
    out = (held, stats, stats_clean, rel, diag)
    _UNIVERSE_CACHE[ck] = out
    return out


def _acc(mem: Dict[tuple, int], held) -> float:
    return evaluate(_as_Q(mem), held, SLOTS, EVAL_STARTS)


# ---------------------------------------------------------------- conditions
def _make(name: str, kind: str, family: int = MM_CONFIRM_FAMILY) -> Condition:
    counter = {"i": 0}

    def run(_rng: Random) -> float:
        i = counter["i"]
        counter["i"] += 1
        held, stats, stats_clean, rel, diag = _universe(i, family)
        if kind == "null":
            a1 = _acc(_mem_semantic(stats), held)
            a2 = _acc(_mem_semantic(stats), held)     # second retrieval+eval pass (universe memoized)
            acc_b, acc_a, delta = a1, a2, a1 - a2
        elif kind == "clean":
            acc_a = _acc(_mem_semantic(stats_clean), held)
            acc_b = _acc(_mem_weighted(stats_clean, rel), held)
            delta = acc_b - acc_a
        elif kind == "recency":
            acc_a = _acc(_mem_semantic(stats), held)
            acc_b = _acc(_mem_weighted(stats, rel, use_prov=False,
                                       use_out=False), held)
            delta = acc_b - acc_a
        else:                                          # PRIMARY: multimetric
            acc_a = _acc(_mem_semantic(stats), held)
            acc_b = _acc(_mem_weighted(stats, rel), held)
            delta = acc_b - acc_a
        MM_LOG.setdefault(name, []).append(
            {"seed_index": i, "mech": round(acc_b, 3), "semantic": round(acc_a, 3),
             "delta": round(delta, 3), **diag})
        return delta

    return Condition(name, run, name)


def multimetric_memory() -> Tuple[List[Condition], str]:
    conditions = [
        _make("null_same_vs_same", "null"),      # null: exactly 0
        _make("clean_stream_control", "clean"),  # discriminating: no poison -> ~0
        _make("recency_only_gain", "recency"),   # ablation: time axis alone
        _make("retrieval_advantage", "multi"),   # PRIMARY: full multimetric
    ]
    return conditions, "retrieval_advantage"


REGISTRY_REAL = {"multimetric_memory": multimetric_memory}


# ---------------------------------------------------------------- smoke / pilot
if __name__ == "__main__":
    import json
    import sys
    import time

    t0 = time.time()

    if "--calibrate" in sys.argv:
        # PILOT: family 942000 (DISJOINT from confirmatory 942500+). Used ONLY
        # to calibrate stream volumes and set honest frozen bands.
        seeds = 5
        rows = []
        for i in range(seeds):
            held, stats, stats_clean, rel, diag = _universe(i, MM_PILOT_FAMILY)
            sem = _mem_semantic(stats)
            multi = _mem_weighted(stats, rel)
            recm = _mem_weighted(stats, rel, use_prov=False, use_out=False)
            sem_c = _mem_semantic(stats_clean)
            multi_c = _mem_weighted(stats_clean, rel)
            contested = sum(1 for k in sem if sem[k] != multi[k])
            r = {"i": i,
                 "acc_semantic": round(_acc(sem, held), 3),
                 "acc_multimetric": round(_acc(multi, held), 3),
                 "acc_recency_only": round(_acc(recm, held), 3),
                 "acc_clean_semantic": round(_acc(sem_c, held), 3),
                 "acc_clean_multimetric": round(_acc(multi_c, held), 3),
                 "contested_keys": contested, **diag}
            r["retrieval_advantage"] = round(
                r["acc_multimetric"] - r["acc_semantic"], 3)
            r["clean_delta"] = round(
                r["acc_clean_multimetric"] - r["acc_clean_semantic"], 3)
            r["recency_only_gain"] = round(
                r["acc_recency_only"] - r["acc_semantic"], 3)
            rows.append(r)
            print(json.dumps(r), flush=True)
        for m in ("retrieval_advantage", "clean_delta", "recency_only_gain",
                  "acc_semantic", "acc_multimetric"):
            vals = [r[m] for r in rows]
            print(f"  {m:<22} mean={sum(vals)/len(vals):+.3f}  "
                  f"min={min(vals):+.3f}  max={max(vals):+.3f}")
        print(f"total {time.time()-t0:.1f}s  [PILOT family {MM_PILOT_FAMILY}]")

    else:
        # quick single-seed confirmatory-family smoke
        conditions, primary = multimetric_memory()
        for c in conditions:
            v = c.run(Random(0))
            print(f"{c.name:<24} delta={v:+.3f}")
        print(json.dumps(MM_LOG, indent=1))
        print(f"total {time.time()-t0:.1f}s")
