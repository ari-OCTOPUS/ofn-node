"""
REAL experiment for specs/social_mirror.yaml — H-OWN-01 / Social Mirror Self-Model.

Tests the hypothesis: an agent develops a MORE TRANSFERABLE self/other model when
its goal can only be resolved by DISTINGUISHING its own goal from another agent's,
rather than from a purely self-referential cue.

Environment (grid-world-shaped; REUSES gridworld_wm.{_step, train, evaluate}
verbatim — improve-not-rewrite). A deterministic 7x7 world with two objects
(A, B). Exactly one object is the learner's self-goal (reward +1); stepping on the
other object is a mistake (-1). Two per-task binary signals disambiguate the goal:

  cue_bit          a SELF-referential marker (e.g. "the object with my colour").
  other_heading_A  a SOCIAL signal: which object the OTHER agent is heading to.

Two conditions differ ONLY in which goal-signal enters the tabular-Q key (both
keys have IDENTICAL cardinality = 1 goal-signal + 4 object-direction signs + 1
wall-context, so there is NO extra-feature / state-space confound between them):

  self_only     key = (cue_bit, dxA_sign, dyA_sign, dxB_sign, dyB_sign, wall_bits)
                -> ignores the other agent; reads its own marker.
  social_mirror key = (other_heading_A, dxA_sign, dyA_sign, dxB_sign, dyB_sign,
                wall_bits) -> observes the other and must infer its own goal by
                distinguishing self from other (self-goal = the object the other
                is NOT heading to).

Two task FAMILIES (the manipulation that makes the social signal relevant or not):

  social   self-goal is ALWAYS the complement of the other's target, so
           other_heading_A reliably identifies the self-goal. The cue_bit is a
           redundant reliable marker during TRAINING.
  control  self-goal is the cue_bit object; the other's target is INDEPENDENT of
           the goal, so other_heading_A is IRRELEVANT ("other present but
           irrelevant"). The cue_bit is a reliable marker during TRAINING.

Two PHASES:
  train      cue_bit reliably indicates the self-goal.
  confusion  (heldout) cue_bit is RANDOMISED -> self-referential marker is
             uninformative; the ONLY residual goal signal is social (and only in
             the social family). Object placements are fresh i.i.d. draws.

So on heldout confusion tasks, self_only (reads the now-random cue) collapses to
chance in BOTH families; social_mirror (reads the other's heading) transfers in
the social family (heading still reliable) but collapses to chance in the control
family (heading irrelevant). Neither condition SELECTS among signals at run time:
each is a FIXED matched-cardinality keying (self_only always keys on the cue slot;
social_mirror always keys on the other's-heading slot). There is no learned
signal-gate; "what transfers" is simply the Q-table that each fixed keying fills
during training, and the DiD contrasts those two hardwired keyings across families.

Primary metric — social_specific_advantage (a difference-in-differences):

  gain_social   = acc(social_mirror | social heldout)  - acc(self_only | social heldout)
  gain_control  = acc(social_mirror | control heldout)  - acc(self_only | control heldout)
  social_specific_advantage = gain_social - gain_control

The DiD nets out any generic effect of the social feature (cardinality is matched
and the self_only baseline behaves identically across families), so it isolates
"the gain from NEEDING to distinguish self from other, not from extra features"
[the required non-strawman control]. FALSIFIABILITY: the quantity is <= 0 whenever
the social-mirror representation fails to form or fails to transfer — a broken
learner, insufficient exploration, or a social signal the tabular agent cannot
generalise all drive it to 0. A trivial agent that ignores the other agent scores
exactly 0. The gated content is the MAGNITUDE clearing a pilot-set SESOI.

Controls reported alongside the primary:
  null_control          self_only vs an INDEPENDENT self_only on social heldout
                        -> pins the training-variance zero-point (~0).
  irrelevant_other_gain gain_control -> the "other present but irrelevant" control;
                        must be ~0 or the social feature helps for non-social
                        reasons (extra feature / spurious structure).
  social_gain           gain_social -> reported for interpretability.

Determinism: task suites derive from fixed suite seeds (paired across conditions
by seed index); agent exploration uses the RNG injected by the harness; eval
fall-back actions use gridworld's per-episode CRC-seeded RNGs. Fully reproducible.

SCOPE: C0-level tabular agents in this grid-world family. "self/other model" is
instantiated as WHICH goal-signal the value table conditions on; "observing the
other" is abstracted to a single heading feature (the keying is FIXED per
condition, not selected by the agent; the social-vs-cue contrast is drawn BETWEEN
conditions/families by the DiD, not learned inside an agent). No claim about
phenomenal self-awareness. Pilot family 979000 set the bands; the confirmatory
run uses a DISJOINT family (980000+, per the assigned seed family).
"""
from __future__ import annotations

import zlib
from dataclasses import dataclass, field
from random import Random
from typing import Dict, List, Tuple

from spec_compiler.harness import Condition

from .gridworld_wm import (
    GRID, MOVES, WALL_P, _connected, _sign, _step, evaluate, train,
)

# ---------------------------------------------------------------- constants
N_TRAIN = 80
N_HELDOUT = 40
EVAL_STARTS = 5
MIN_CELLS = 16
SOCIAL_BUDGET = 60_000           # episodes per Q-table (modest; see ADR note)
SOCIAL_BASE_SEED = 980_000       # CONFIRMATORY family (assigned seed family);
                                 # pilot/calibration used 979_000 (disjoint).

# feature tuple layout (per walkable cell)
#   0 dxA_sign  1 dyA_sign  2 dxB_sign  3 dyB_sign  4 wall_bits
#   5 cue_bit (self-marker)  6 other_heading_A (social signal)
SELF_ONLY_SLOTS = (5, 0, 1, 2, 3, 4)      # reads own cue, ignores the other
SOCIAL_SLOTS = (6, 0, 1, 2, 3, 4)         # reads the other's heading
# both length 6 -> matched key cardinality, no extra-feature confound.

SOCIAL_LOG: dict = {}


# ---------------------------------------------------------------- environment
@dataclass
class Task:
    uid: int
    walls: frozenset
    target: Tuple[int, int]          # the self-goal object (+1)
    loser: Tuple[int, int]           # the other object (-1)
    free: List[Tuple[int, int]]      # free non-object cells (start candidates)
    feats: Dict[Tuple[int, int], tuple] = field(default_factory=dict)


def make_task(uid: int, rng: Random, family: str, phase: str) -> Task:
    """family in {'social','control'}; phase in {'train','confusion'}."""
    allcells = {(x, y) for x in range(GRID) for y in range(GRID)}
    while True:
        walls = {c for c in allcells if rng.random() < WALL_P}
        cells = allcells - walls
        if len(cells) < MIN_CELLS or not _connected(cells):
            continue
        spots = sorted(cells)
        obj_a, obj_b = rng.sample(spots, 2)
        free = [c for c in spots if c not in (obj_a, obj_b)]
        if len(free) < EVAL_STARTS:
            continue

        goal_side = rng.randrange(2)                 # 0 -> A is self-goal, 1 -> B
        if family == "social":
            other_side = 1 - goal_side               # other pursues the complement
        else:                                        # control: other is independent
            other_side = rng.randrange(2)
        other_heading_a = 1 if other_side == 0 else 0
        cue_bit = goal_side if phase == "train" else rng.randrange(2)

        target = obj_a if goal_side == 0 else obj_b
        loser = obj_b if goal_side == 0 else obj_a

        feats: Dict[Tuple[int, int], tuple] = {}
        for (x, y) in spots:
            wb = 0
            for i, (dx, dy) in enumerate(MOVES):
                n = (x + dx, y + dy)
                if not (0 <= n[0] < GRID and 0 <= n[1] < GRID) or n in walls:
                    wb |= 1 << i
            feats[(x, y)] = (
                _sign(obj_a[0] - x), _sign(obj_a[1] - y),
                _sign(obj_b[0] - x), _sign(obj_b[1] - y),
                wb, cue_bit, other_heading_a,
            )
        return Task(uid, frozenset(walls), target, loser, free, feats)


def build_suite(suite_seed: int, family: str, phase: str, n: int) -> List[Task]:
    tasks = []
    for j in range(n):
        uid = zlib.crc32(f"{suite_seed}|{family}|{phase}|{j}".encode())
        rng = Random(uid ^ 0x5DEECE66)
        tasks.append(make_task(uid, rng, family, phase))
    return tasks


# ---------------------------------------------------------------- one arm
def _acc(train_suite, held_suite, slots, budget: int, rng: Random) -> float:
    """Train a fresh tabular Q on train_suite (given slots), return heldout
    accuracy. Reuses gridworld_wm.train / evaluate verbatim."""
    Q: dict = {}
    train(Q, train_suite, slots, budget, rng)
    return evaluate(Q, held_suite, slots, EVAL_STARTS)


def _suites(i: int, family: str):
    base = SOCIAL_BASE_SEED + i
    tr = build_suite(base, family, "train", N_TRAIN)
    hd = build_suite(base, family, "confusion", N_HELDOUT)
    return tr, hd


# ---------------------------------------------------------------- conditions
def _make(name: str, kind: str, log: dict) -> Condition:
    counter = {"i": 0}

    def run(rng: Random) -> float:
        i = counter["i"]
        counter["i"] += 1
        rec = {"seed_index": i}

        if kind == "null":
            tr, hd = _suites(i, "social")
            a1 = _acc(tr, hd, SELF_ONLY_SLOTS, SOCIAL_BUDGET, rng)
            rng2 = Random(zlib.crc32(f"null2|{i}".encode()))
            a2 = _acc(tr, hd, SELF_ONLY_SLOTS, SOCIAL_BUDGET, rng2)
            val = a1 - a2
            rec.update(self_only_a=round(a1, 4), self_only_b=round(a2, 4),
                       value=round(val, 4))
        elif kind == "control":
            tr, hd = _suites(i, "control")
            so = _acc(tr, hd, SELF_ONLY_SLOTS, SOCIAL_BUDGET, rng)
            sm = _acc(tr, hd, SOCIAL_SLOTS, SOCIAL_BUDGET, rng)
            val = sm - so
            rec.update(control_self_only=round(so, 4), control_social=round(sm, 4),
                       value=round(val, 4))
        elif kind == "social":
            tr, hd = _suites(i, "social")
            so = _acc(tr, hd, SELF_ONLY_SLOTS, SOCIAL_BUDGET, rng)
            sm = _acc(tr, hd, SOCIAL_SLOTS, SOCIAL_BUDGET, rng)
            val = sm - so
            rec.update(social_self_only=round(so, 4), social_social=round(sm, 4),
                       value=round(val, 4))
        else:                                        # did (PRIMARY)
            trs, hds = _suites(i, "social")
            trc, hdc = _suites(i, "control")
            so_s = _acc(trs, hds, SELF_ONLY_SLOTS, SOCIAL_BUDGET, rng)
            sm_s = _acc(trs, hds, SOCIAL_SLOTS, SOCIAL_BUDGET, rng)
            so_c = _acc(trc, hdc, SELF_ONLY_SLOTS, SOCIAL_BUDGET, rng)
            sm_c = _acc(trc, hdc, SOCIAL_SLOTS, SOCIAL_BUDGET, rng)
            gain_social = sm_s - so_s
            gain_control = sm_c - so_c
            val = gain_social - gain_control
            rec.update(
                social_self_only=round(so_s, 4), social_social=round(sm_s, 4),
                control_self_only=round(so_c, 4), control_social=round(sm_c, 4),
                gain_social=round(gain_social, 4),
                gain_control=round(gain_control, 4),
                value=round(val, 4))

        log.setdefault(name, []).append(rec)
        return val

    return Condition(name, run, name)


def social_mirror() -> Tuple[List[Condition], str]:
    """H-OWN-01 Social Mirror. Order: null/controls first, PRIMARY last."""
    conditions = [
        _make("null_control", "null", SOCIAL_LOG),                 # ~0 zero-point
        _make("irrelevant_other_gain", "control", SOCIAL_LOG),     # ~0 control
        _make("social_gain", "social", SOCIAL_LOG),                # reported
        _make("social_specific_advantage", "did", SOCIAL_LOG),     # PRIMARY (DiD)
    ]
    return conditions, "social_specific_advantage"


REGISTRY_REAL = {"social_mirror": social_mirror}


# ---------------------------------------------------------------- smoke / pilot
if __name__ == "__main__":
    import json
    import sys
    import time

    seeds = 3
    base = 979_000                      # PILOT family (disjoint from confirmatory)
    if "--confirm" in sys.argv:
        base = SOCIAL_BASE_SEED
    t0 = time.time()

    rows = []
    for i in range(seeds):
        # temporarily point the module at the requested base by index
        gi = base + i
        trs = build_suite(gi, "social", "train", N_TRAIN)
        hds = build_suite(gi, "social", "confusion", N_HELDOUT)
        trc = build_suite(gi, "control", "train", N_TRAIN)
        hdc = build_suite(gi, "control", "confusion", N_HELDOUT)
        rng = Random(1000 + i)
        so_s = _acc(trs, hds, SELF_ONLY_SLOTS, SOCIAL_BUDGET, rng)
        sm_s = _acc(trs, hds, SOCIAL_SLOTS, SOCIAL_BUDGET, rng)
        so_c = _acc(trc, hdc, SELF_ONLY_SLOTS, SOCIAL_BUDGET, rng)
        sm_c = _acc(trc, hdc, SOCIAL_SLOTS, SOCIAL_BUDGET, rng)
        gs = sm_s - so_s
        gc = sm_c - so_c
        did = gs - gc
        rows.append(dict(seed=gi, so_s=round(so_s, 3), sm_s=round(sm_s, 3),
                         so_c=round(so_c, 3), sm_c=round(sm_c, 3),
                         gain_social=round(gs, 3), gain_control=round(gc, 3),
                         DiD=round(did, 3)))
        print(json.dumps(rows[-1]))

    n = len(rows)
    mean = lambda k: sum(r[k] for r in rows) / n
    print("\n# means over", n, "pilot seeds (base", base, ")")
    for k in ("so_s", "sm_s", "so_c", "sm_c", "gain_social", "gain_control", "DiD"):
        print(f"  {k:<13}{mean(k):+.3f}")
    print(f"\ntotal {time.time()-t0:.1f}s")
