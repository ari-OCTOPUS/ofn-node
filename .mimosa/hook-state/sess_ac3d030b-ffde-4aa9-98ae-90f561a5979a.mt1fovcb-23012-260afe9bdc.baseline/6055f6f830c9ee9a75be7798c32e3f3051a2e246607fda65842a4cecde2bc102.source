"""
REAL experiment for specs/ontology_shift.yaml — H-GEO-02: goal lifting under an
ontology shift. This is GEOMETRY.md §5's Kan-extension [MAP] object
(`U_D ∘ F ≅ U_C`, the commuting triangle) made falsifiable on the running
kernel: the substrate the map was waiting for.

An agent learns a task family under feature ontology C (gridworld_wm's
relational features, the a-priori K=6 slots from ADR-001). Then the
OBSERVATION ONTOLOGY changes to D: an information-equivalent per-dimension
recoding of every feature value (each dimension's alphabet is mapped by a
fixed random bijection onto code indices; fixed per universe). Post-shift,
at EQUAL total episode budget (POST_SHIFT_BUDGET each):

  relearn_from_scratch  arm: fresh Q trained on raw D observations (tabular
                        learning is label-invariant, so this is exactly
                        "learn the task again with zero carry-over").
  lifted_policy         arm: learn the correspondence F: D -> C from a SMALL
                        paired "sensor-overlap" adaptation window
                        (ADAPT_EPISODES random-walk episodes during which both
                        encodings are visible — the calibration overlap of a
                        sensor replacement — PAID out of the same post-shift
                        budget), then REUSE the pre-shift Q through F
                        (utility lifting: U_D = U_C ∘ F) and refine it with
                        the remaining budget.

PRIMARY (falsifiable, gated): lifting_advantage =
  success(lifted_policy) − success(relearn_from_scratch) on heldout tasks in D.
It is <= 0 whenever the correspondence is not learnable from the window, or
lifting misleads (stale utility worse than fresh learning).

Controls (all reported as the same paired difference):
  null_no_shift        D == C. Full lifting machinery (learn F, refine through
                       it) vs plain reuse-and-refine without F, equal budget.
                       Must be ~0: the apparatus alone adds nothing.
  no_mapping_reuse     mechanism ablation: reuse + refine the old Q on RAW D
                       observations (no F), vs relearn. The ONLY difference
                       from lifted_policy is the learned mapping — if this is
                       ~<=0 while the primary is >0, the advantage is
                       attributable to F, not to mere Q reuse. NOTE this is a
                       MEAN-level claim over a noisy ablation, not a
                       per-universe guarantee: one pilot universe was +0.057
                       and one confirmatory universe +0.113 [FACT], while the
                       means stayed <=0 (-0.044 pilot, -0.055 confirmatory).
  unlearnable_shift    discriminating control: the recoding is randomized
                       PER-STATE (no global correspondence exists, so F is
                       unlearnable by construction). The same machinery MUST
                       give ~<=0 here; a positive value would mean the harness,
                       not the mechanism, manufactures the effect. Note this
                       control is LIVE, not structural: the garbage F̂ maps
                       heldout codes into the old Q's keyspace, so lifting can
                       be actively misled below the relearn floor.

Budget accounting (per universe): PRE_SHIFT_EPISODES of pre-shift training
produce Q_C (shared history; the relearn arm discards it — that is the point
of relearning). Then each arm gets exactly POST_SHIFT_BUDGET post-shift
episodes: relearn spends all of them on fresh Q-learning (standard anneal,
the schedule a fresh learner needs); lifted spends ADAPT_EPISODES on the
paired window plus the rest as low-eps refinement (the pass a trained Q
warrants, same convention as consolidation's raw-replay arm);
no_mapping_reuse gets the full budget as refinement (it pays no mapping cost).

Determinism: suites come from gridworld_wm.build_suite and are paired across
conditions by a per-condition call counter (same pattern & warning as
gridworld_wm: conditions must be freshly built per run_spec call). Every RNG
is CRC-derived from the universe seed + arm name, so arms are suite-paired and
condition-independent; the harness rng is intentionally unused. No LLM,
stdlib only, reuses gridworld_wm verbatim (improve-not-rewrite).

Seed families — disjoint from every other experiment's, INCLUDING the nearby
942xxx/942.5k (multimetric_memory), 944xxx/944.5k (attractor_memory),
946xxx/946.5k (comparison_metacog_v2) and 948xxx/948.5k/953xxx
(adaptive_forgetting_v2) families as well as the older 987/991/993/994/995/
997/998k blocks (no collision; enumerated 2026-07-14 — an earlier version of
this comment listed only the 98x/99x blocks, which was stale, not wrong):
  pilot        940_000+  (numbers quoted in the spec come from here)
  confirmatory 945_000+  (the registry path `rsc.py run ontology_shift`;
                          never piloted, never smoked)
  smoke        949_000+  (plumbing/timing AND the POST_SHIFT_BUDGET
                          calibration; the full smoke pass at budget 500 also
                          shows the primary effect, +0.213 [FACT] — a
                          disclosed third-family peek, see ADR-017 caveat 3)
"""
from __future__ import annotations

import zlib
from random import Random
from typing import Dict, List, Sequence, Tuple

from spec_compiler.harness import Condition

from .gridworld_wm import (
    EPS_LO, EVAL_STARTS, MAX_STEPS, MINIMAL_SUFFICIENT, N_FEATURES, N_TRAIN,
    Task, _step, build_suite, evaluate, train,
)

SLOTS = tuple(sorted(MINIMAL_SUFFICIENT))   # a-priori K=6 relational slots (ADR-001)
PRE_SHIFT_EPISODES = 30_000                 # pre-shift life under ontology C
POST_SHIFT_BUDGET = 500                     # EQUAL post-shift budget per arm
                                            # (1.7% of pre-shift life: the shift
                                            # must be answered under scarcity,
                                            # else relearning trivially catches
                                            # up and NO mechanism is being
                                            # tested; set on the smoke family
                                            # BEFORE pilot/confirmatory)
ADAPT_EPISODES = 40                         # paired-overlap window (paid from budget)
PILOT_BASE_SEED = 940_000
CONFIRMATORY_BASE_SEED = 945_000
SMOKE_BASE_SEED = 949_000

# value alphabet of every observation dimension (from gridworld_wm feature docs)
ALPHABETS: Tuple[Tuple[int, ...], ...] = (
    tuple(range(7)),        # 0  agent_x
    tuple(range(7)),        # 1  agent_y
    tuple(range(64)),       # 2  layout_id
    (0, 1),                 # 3  cue_type
    (0, 1, 2),              # 4  cue_value
    (0, 1),                 # 5  A_matches_cue
    (-1, 0, 1),             # 6  dxA_sign
    (-1, 0, 1),             # 7  dyA_sign
    (-1, 0, 1),             # 8  dxB_sign
    (-1, 0, 1),             # 9  dyB_sign
    tuple(range(16)),       # 10 wall_bits
    (0, 1, 2, 3),           # 11 distA_bucket
    (0, 1, 2, 3),           # 12 distB_bucket
    (0, 1),                 # 13 parity
    (0, 1, 2),              # 14 colorA
    (0, 1, 2),              # 15 shapeA
    (0, 1, 2),              # 16 colorB
    (0, 1, 2),              # 17 shapeB
)
assert len(ALPHABETS) == N_FEATURES

ONTOLOGY_LOG: dict = {}


# ---------------------------------------------------------------- rng & recoding
def _rng(tag: str) -> Random:
    """CRC-derived RNG: deterministic, suite-paired, condition-independent."""
    return Random(zlib.crc32(tag.encode()))


def _recode(task: Task, coder) -> Task:
    """Copy a task with its per-cell feature tuples re-encoded (env unchanged:
    same walls/objects/dynamics — ONLY the observation ontology differs)."""
    t = Task(uid=task.uid, walls=task.walls, obj_a=task.obj_a, obj_b=task.obj_b,
             target=task.target, loser=task.loser, free=task.free)
    t.feats = {pos: coder(task, pos, f) for pos, f in task.feats.items()}
    return t


def _shift_perms(universe: int) -> List[Dict[int, int]]:
    """Ontology D: per-dimension bijection alphabet -> code index (a genuinely
    different but information-equivalent encoding), fixed for the universe."""
    rng = _rng(f"shift|{universe}")
    perms: List[Dict[int, int]] = []
    for alpha in ALPHABETS:
        idx = list(range(len(alpha)))
        rng.shuffle(idx)
        perms.append({v: idx[k] for k, v in enumerate(alpha)})
    return perms


def _shift_suite(suite: Sequence[Task], perms: List[Dict[int, int]]) -> List[Task]:
    def coder(_task: Task, _pos, f: tuple) -> tuple:
        return tuple(perms[j][v] for j, v in enumerate(f))
    return [_recode(t, coder) for t in suite]


def _unlearnable_suite(suite: Sequence[Task], universe: int) -> List[Task]:
    """Discriminating control: the recoding is a fresh random bijection PER
    STATE (task, cell) — deterministic given the universe, but with no global
    correspondence, so no F: D -> C exists to learn."""
    def coder(task: Task, pos, f: tuple) -> tuple:
        r = Random(zlib.crc32(f"unl|{universe}|{task.uid}|{pos[0]},{pos[1]}".encode()))
        out = []
        for j, v in enumerate(f):
            alpha = ALPHABETS[j]
            idx = list(range(len(alpha)))
            r.shuffle(idx)
            out.append(idx[alpha.index(v)])
        return tuple(out)
    return [_recode(t, coder) for t in suite]


# ---------------------------------------------------------------- mapping F
def _learn_mapping(d_tasks: Sequence[Task], c_tasks: Sequence[Task],
                   episodes: int, rng: Random) -> List[Dict[int, int]]:
    """Learn F̂: D -> C from the paired sensor-overlap window: random-walk
    episodes on TRAIN tasks while both encodings are visible; per-dimension
    co-occurrence counting -> argmax decode (ties -> smallest C value,
    deterministic). Unseen D codes fall back to identity."""
    co: List[Dict[Tuple[int, int], int]] = [dict() for _ in range(N_FEATURES)]
    n = len(d_tasks)
    for ep in range(episodes):
        td, tc = d_tasks[ep % n], c_tasks[ep % n]
        pos = td.free[rng.randrange(len(td.free))]
        for _ in range(MAX_STEPS):
            fd, fc = td.feats[pos], tc.feats[pos]
            for j in range(N_FEATURES):
                key = (fd[j], fc[j])
                co[j][key] = co[j].get(key, 0) + 1
            pos, _r, done, _w = _step(td, pos, rng.randrange(4))
            if done:
                break
    fmap: List[Dict[int, int]] = []
    for j in range(N_FEATURES):
        best: Dict[int, Tuple[int, int]] = {}
        for (dv, cv), cnt in sorted(co[j].items()):
            cur = best.get(dv)
            if cur is None or cnt > cur[0]:
                best[dv] = (cnt, cv)
        fmap.append({dv: cv for dv, (_cnt, cv) in best.items()})
    return fmap


def _lift_suite(d_tasks: Sequence[Task], fmap: List[Dict[int, int]]) -> List[Task]:
    """The lifted view: observations F̂(D(s)) — old Q's keyspace, new sensors."""
    def coder(_task: Task, _pos, f: tuple) -> tuple:
        return tuple(fmap[j].get(v, v) for j, v in enumerate(f))
    return [_recode(t, coder) for t in d_tasks]


def _mapping_recovery(fmap: List[Dict[int, int]],
                      perms: List[Dict[int, int]]) -> float:
    """Diagnostic (logged, not gated): fraction of slot-dimension alphabet
    values whose true correspondence F̂(sigma(v)) == v was recovered."""
    hits = total = 0
    for j in SLOTS:
        for v in ALPHABETS[j]:
            total += 1
            if fmap[j].get(perms[j][v]) == v:
                hits += 1
    return hits / total


# ---------------------------------------------------------------- arms
def _pretrain(suite: Sequence[Task], universe: int) -> dict:
    Q: dict = {}
    train(Q, suite[:N_TRAIN], SLOTS, PRE_SHIFT_EPISODES, _rng(f"pre|{universe}"))
    return Q


def _copy_q(Q: dict) -> dict:
    return {k: list(v) for k, v in Q.items()}


def _relearn(d_suite: Sequence[Task], universe: int) -> float:
    """relearn_from_scratch arm: fresh Q, full post-shift budget, std anneal."""
    Q: dict = {}
    train(Q, d_suite[:N_TRAIN], SLOTS, POST_SHIFT_BUDGET, _rng(f"relearn|{universe}"))
    return evaluate(Q, d_suite[N_TRAIN:], SLOTS, EVAL_STARTS)


def _reuse_refine(Q: dict, view_suite: Sequence[Task], universe: int,
                  episodes: int) -> float:
    """Reuse-and-refine arm: continue the old Q on a (possibly mapped) view,
    low-eps refinement (a trained Q's schedule, cf. consolidation)."""
    train(Q, view_suite[:N_TRAIN], SLOTS, episodes, _rng(f"refine|{universe}"),
          eps_hi=EPS_LO, eps_lo=EPS_LO)
    return evaluate(Q, view_suite[N_TRAIN:], SLOTS, EVAL_STARTS)


def _lifted(Q: dict, c_suite: Sequence[Task], d_suite: Sequence[Task],
            universe: int) -> Tuple[float, List[Dict[int, int]]]:
    """lifted_policy arm: learn F̂ from the overlap window (cost deducted),
    then U_D = U_C ∘ F̂ — refine + evaluate the OLD Q through the lifted view."""
    fmap = _learn_mapping(d_suite[:N_TRAIN], c_suite[:N_TRAIN],
                          ADAPT_EPISODES, _rng(f"adapt|{universe}"))
    lifted_view = _lift_suite(d_suite, fmap)
    score = _reuse_refine(Q, lifted_view, universe,
                          POST_SHIFT_BUDGET - ADAPT_EPISODES)
    return score, fmap


# ---------------------------------------------------------------- conditions
def _make(name: str, kind: str, desc: str, base_seed: int) -> Condition:
    """kind: 'null' | 'no_mapping' | 'unlearnable' | 'lift'.
    Paired universes: the i-th call uses suite seed base_seed+i, so every
    condition sees the identical universe for seed i. WARNING (as in
    gridworld_wm): the pairing relies on a per-condition call counter, so
    conditions must be freshly built for every run_spec invocation."""
    counter = {"i": 0}

    def run(_harness_rng: Random) -> float:
        i = counter["i"]
        counter["i"] += 1
        universe = base_seed + i
        suite = build_suite(universe)
        Q0 = _pretrain(suite, universe)
        entry = {"universe": universe}

        if kind == "null":
            a, fmap = _lifted(_copy_q(Q0), suite, suite, universe)
            b = _reuse_refine(_copy_q(Q0), suite, universe, POST_SHIFT_BUDGET)
            entry.update(machinery=round(a, 3), plain_reuse=round(b, 3))
        elif kind == "no_mapping":
            d_suite = _shift_suite(suite, _shift_perms(universe))
            a = _reuse_refine(_copy_q(Q0), d_suite, universe, POST_SHIFT_BUDGET)
            b = _relearn(d_suite, universe)
            entry.update(raw_reuse=round(a, 3), relearn=round(b, 3))
        elif kind == "unlearnable":
            d_suite = _unlearnable_suite(suite, universe)
            a, fmap = _lifted(_copy_q(Q0), suite, d_suite, universe)
            b = _relearn(d_suite, universe)
            entry.update(lifted=round(a, 3), relearn=round(b, 3))
        else:                                   # 'lift' — the primary
            perms = _shift_perms(universe)
            d_suite = _shift_suite(suite, perms)
            a, fmap = _lifted(_copy_q(Q0), suite, d_suite, universe)
            b = _relearn(d_suite, universe)
            entry.update(
                lifted=round(a, 3), relearn=round(b, 3),
                mapping_recovery=round(_mapping_recovery(fmap, perms), 3),
                preshift_heldout=round(
                    evaluate(Q0, suite[N_TRAIN:], SLOTS, EVAL_STARTS), 3))

        delta = a - b
        entry["delta"] = round(delta, 3)
        ONTOLOGY_LOG.setdefault(name, []).append(entry)
        return delta

    return Condition(name, run, desc)


def _build(base_seed: int) -> Tuple[List[Condition], str]:
    conditions = [
        _make("null_no_shift", "null",
              "null: D==C; lifting machinery vs plain reuse (must be ~0)",
              base_seed),
        _make("no_mapping_reuse", "no_mapping",
              "mechanism ablation: old Q on raw D without F, vs relearn",
              base_seed),
        _make("unlearnable_shift", "unlearnable",
              "discriminating control: per-state random recoding (F unlearnable)",
              base_seed),
        _make("lifting_advantage", "lift",
              "PRIMARY: lifted (U_C ∘ F̂) minus relearn, equal budget",
              base_seed),
    ]
    return conditions, "lifting_advantage"


def ontology_shift() -> Tuple[List[Condition], str]:
    """Registry entry — CONFIRMATORY seed family (945000+), never piloted."""
    return _build(CONFIRMATORY_BASE_SEED)


# ---------------------------------------------------------------- pilot / smoke
if __name__ == "__main__":
    # run from the repo root:  python -m experiments.ontology_shift --pilot
    import json
    import sys
    import time

    from spec_compiler.harness import run_ablation

    t0 = time.time()
    if "--smoke" in sys.argv:                 # plumbing + timing, 1 universe
        conditions, primary = _build(SMOKE_BASE_SEED)
        results = run_ablation(conditions, seeds=1)
        for r in results:
            print(f"{r.name:<22}{r.mean:+.3f}")
        print(json.dumps(ONTOLOGY_LOG, indent=1))
        print(f"total {time.time()-t0:.1f}s")
    elif "--pilot" in sys.argv:               # 5 universes, family 940000
        conditions, primary = _build(PILOT_BASE_SEED)
        results = run_ablation(conditions, seeds=5)
        print("# PILOT — seed family 940000 (5 universes); confirmatory 945000 untouched")
        print(f"{'condition':<22}{'mean':>8}{'std':>8}  values")
        for r in results:
            print(f"{r.name:<22}{r.mean:>+8.3f}{r.std:>8.3f}  "
                  f"{['%+.3f' % v for v in r.values]}")
        print("\n# per-universe log")
        print(json.dumps(ONTOLOGY_LOG, indent=1))
        print(f"\ntotal {time.time()-t0:.1f}s")
    else:
        print("usage: python -m experiments.ontology_shift --smoke | --pilot")
