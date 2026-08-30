"""
REAL experiment for H-OWN-03 / EXP-001 (spec: specs/wm_abstraction.yaml).

Deterministic grid-world task family + tabular Q-learning. No LLM anywhere.
The working-memory manipulation is the ONLY difference between conditions:

  unlimited_memory   Q-table keyed on the FULL 18-feature observation tuple
                     (raw unlimited state buffer -> nothing forces abstraction).
  limited_wm         Q-table keyed on K feature slots. WHICH features occupy
                     the slots is learned (gating = greedy forward selection +
                     swap refinement, scored on a validation split *inside* the
                     training family; heldout is never touched before final eval).
  oracle_no_taskid   discriminating control: unlimited capacity, task-ID
                     features excluded by fiat (no capacity pressure involved).

Scope (declared): gating here operates at representation level (which features
enter WM), not per-timestep write dynamics; and "abstraction discovery" is
instantiated as SELECTION of a derived relational predicate from a fixed
vocabulary that contains it, its raw ingredients, and decoys. Heldout tasks
are new i.i.d. draws of the same family: the metric measures within-family
generalization, not distribution-shift robustness (see adr/ADR-001).

Controls (per spec protocol):
  - both conditions share the same task suite per seed (paired suites),
  - the same TOTAL episode budget (selection episodes are paid out of the
    limited agent's budget),
  - the same learner, hyperparameters, reward, and eval procedure,
  - the same feature vocabulary (the bottleneck selects, it does not add).

Primary capacity K=6 is fixed A PRIORI as the size of the minimal sufficient
relational statistic in this vocabulary (5 object-relational features + 1
local wall context), documented in adr/ADR-001. It is not tuned on results.

Determinism: task suites derive from fixed suite seeds (paired across
conditions); agent exploration uses the RNG injected by the harness; eval
fallback actions for unseen states use per-episode CRC-seeded RNGs.
"""
from __future__ import annotations

import zlib
from dataclasses import dataclass, field
from operator import itemgetter
from random import Random
from typing import Dict, List, Optional, Sequence, Tuple

from spec_compiler.harness import Condition

# ---------------------------------------------------------------- constants
GRID = 7
WALL_P = 0.12
N_TASKS = 200                 # spec: experiment.n = 200
N_TRAIN = 140
N_HELDOUT = 60
SELECTION_FIT = 40            # train[:40] used to fit proxy Q during gating
SELECTION_VAL = (100, 140)    # train[100:140] scores candidates (still train!)
EVAL_STARTS = 5
VAL_STARTS = 5
MAX_STEPS = 50
TOTAL_EPISODE_BUDGET = 1_000_000
PROXY_EPISODES_NOMINAL = 3_000
EVAL_EPS = 0.10   # identical slight stochasticity for BOTH conditions:
                  # breaks deterministic loops caused by state aliasing
ALPHA = 0.25
GAMMA = 0.95
EPS_HI, EPS_LO = 0.30, 0.05
STEP_REWARD = -0.01
WIN_REWARD = 1.0
LOSE_REWARD = -1.0
SUITE_BASE_SEED = 991_000     # paired suites: suite s is identical across conditions.
                              # 991_000+ are CONFIRMATORY suites, never piloted;
                              # pilot/smoke runs used 987_000 (see ADR-001).

# actions: 0=up 1=right 2=down 3=left
MOVES = ((0, -1), (1, 0), (0, 1), (-1, 0))

N_FEATURES = 18
FEATURE_NAMES = [
    "agent_x",          # 0  absolute
    "agent_y",          # 1  absolute
    "layout_id",        # 2  task-specific (hash bucket of the wall set)
    "cue_type",         # 3  raw task context (informative only via composition)
    "cue_value",        # 4  raw task context
    "A_matches_cue",    # 5  derived relational predicate (computed from cue +
                        #    object attributes; the candidate abstraction)
    "dxA_sign",         # 6  relational key
    "dyA_sign",         # 7  relational key
    "dxB_sign",         # 8  relational key
    "dyB_sign",         # 9  relational key
    "wall_bits",        # 10 local context
    "distA_bucket",     # 11 helpful
    "distB_bucket",     # 12 helpful
    "parity",           # 13 decoy
    "colorA",           # 14 raw object attribute (alternative to the predicate)
    "shapeA",           # 15 raw object attribute
    "colorB",           # 16 raw object attribute
    "shapeB",           # 17 raw object attribute
]
# non-task-identifying vocabulary (everything except absolute coords + layout id)
NON_TASKID = tuple(i for i in range(N_FEATURES) if i not in (0, 1, 2))
# minimal sufficient relational set -> a-priori primary K
MINIMAL_SUFFICIENT = (5, 6, 7, 8, 9, 10)
PRIMARY_K = len(MINIMAL_SUFFICIENT)  # = 6


# ---------------------------------------------------------------- environment
@dataclass
class Task:
    uid: int
    walls: frozenset
    obj_a: Tuple[int, int]
    obj_b: Tuple[int, int]
    target: Tuple[int, int]          # the object that matches the cue
    loser: Tuple[int, int]
    free: List[Tuple[int, int]]      # free non-object cells (start candidates)
    feats: Dict[Tuple[int, int], tuple] = field(default_factory=dict)


def _sign(v: int) -> int:
    return (v > 0) - (v < 0)


def _bucket(d: int) -> int:
    if d == 0:
        return 0
    if d <= 2:
        return 1
    if d <= 5:
        return 2
    return 3


def _connected(cells: set) -> bool:
    if not cells:
        return False
    start = next(iter(cells))
    seen = {start}
    stack = [start]
    while stack:
        x, y = stack.pop()
        for dx, dy in MOVES:
            n = (x + dx, y + dy)
            if n in cells and n not in seen:
                seen.add(n)
                stack.append(n)
    return seen == cells


def make_task(uid: int, rng: Random, wall_p: float = WALL_P) -> Task:
    while True:
        walls = {(x, y) for x in range(GRID) for y in range(GRID)
                 if rng.random() < wall_p}
        cells = {(x, y) for x in range(GRID) for y in range(GRID)} - walls
        if len(cells) < 12 or not _connected(cells):
            continue
        spots = sorted(cells)
        obj_a, obj_b = rng.sample(spots, 2)
        # REAL cue semantics: objects carry (color, shape) attributes; the cue
        # names one attribute dimension + value; the target IS the object whose
        # attribute matches the cue. Rejection-sample until exactly one matches.
        while True:
            attrs_a = (rng.randrange(3), rng.randrange(3))
            attrs_b = (rng.randrange(3), rng.randrange(3))
            cue_type = rng.randrange(2)       # 0=color 1=shape
            cue_value = rng.randrange(3)
            a_matches = attrs_a[cue_type] == cue_value
            b_matches = attrs_b[cue_type] == cue_value
            if a_matches != b_matches:
                break
        target, loser = (obj_a, obj_b) if a_matches else (obj_b, obj_a)
        free = [c for c in spots if c not in (obj_a, obj_b)]
        if len(free) < EVAL_STARTS:
            continue
        layout_id = zlib.crc32(repr(sorted(walls)).encode()) % 64
        t = Task(uid=uid, walls=frozenset(walls), obj_a=obj_a, obj_b=obj_b,
                 target=target, loser=loser, free=free)
        # precompute the full feature tuple for every walkable cell
        for (x, y) in spots:
            wb = 0
            for i, (dx, dy) in enumerate(MOVES):
                n = (x + dx, y + dy)
                if not (0 <= n[0] < GRID and 0 <= n[1] < GRID) or n in walls:
                    wb |= 1 << i
            da = abs(obj_a[0] - x) + abs(obj_a[1] - y)
            db = abs(obj_b[0] - x) + abs(obj_b[1] - y)
            t.feats[(x, y)] = (
                x, y, layout_id, cue_type, cue_value,
                1 if a_matches else 0,
                _sign(obj_a[0] - x), _sign(obj_a[1] - y),
                _sign(obj_b[0] - x), _sign(obj_b[1] - y),
                wb, _bucket(da), _bucket(db), (x + y) % 2,
                attrs_a[0], attrs_a[1], attrs_b[0], attrs_b[1],
            )
        return t


def build_suite(suite_seed: int, wall_p: float = WALL_P) -> List[Task]:
    return [make_task(suite_seed * 1000 + i,
                      Random(suite_seed * 100_003 + i * 7919), wall_p)
            for i in range(N_TASKS)]


# ---------------------------------------------------------------- learner
def _step(task: Task, pos: Tuple[int, int], action: int):
    dx, dy = MOVES[action]
    n = (pos[0] + dx, pos[1] + dy)
    if not (0 <= n[0] < GRID and 0 <= n[1] < GRID) or n in task.walls:
        n = pos
    if n == task.target:
        return n, WIN_REWARD, True, True
    if n == task.loser:
        return n, LOSE_REWARD, True, False
    return n, STEP_REWARD, False, False


def train(Q: dict, tasks: Sequence[Task], slots: Sequence[int],
          episodes: int, rng: Random,
          eps_hi: float = EPS_HI, eps_lo: float = EPS_LO) -> None:
    """Shared-Q tabular Q-learning over a task family. Mutates Q in place.
    eps_hi/eps_lo default to the standard anneal; pass eps_hi=eps_lo=<low> for a
    low-exploration REFINEMENT pass over an already-trained Q (used by
    consolidation's raw-replay arm, so replay is refinement, not a fresh
    high-exploration restart)."""
    key_of = itemgetter(*slots) if len(slots) > 1 else lambda f, _i=slots[0]: (f[_i],)
    for ep in range(episodes):
        task = tasks[ep % len(tasks)]
        eps = eps_hi + (eps_lo - eps_hi) * (ep / max(1, episodes - 1))
        pos = task.free[rng.randrange(len(task.free))]
        for _ in range(MAX_STEPS):
            k = key_of(task.feats[pos])
            q = Q.get(k)
            if q is None:
                q = [0.0, 0.0, 0.0, 0.0]
                Q[k] = q
            if rng.random() < eps:
                a = rng.randrange(4)
            else:
                m = max(q)
                a = q.index(m)
            npos, r, done, _win = _step(task, pos, a)
            nk = key_of(task.feats[npos])
            nq = Q.get(nk)
            best_next = 0.0 if (done or nq is None) else max(nq)
            q[a] += ALPHA * (r + GAMMA * best_next - q[a])
            pos = npos
            if done:
                break


def evaluate(Q: dict, tasks: Sequence[Task], slots: Sequence[int],
             starts_per_task: int, unseen_fail: bool = False) -> float:
    """eps-greedy policy (EVAL_EPS) with per-episode CRC-seeded RNG; unseen
    state -> random action from the same RNG. The slight stochasticity breaks
    deterministic loops caused by state aliasing and is applied identically to
    every condition. Fully deterministic given (Q, tasks, slots).

    unseen_fail=True is used ONLY inside gating selection scoring: an unseen
    key ends the episode as a failure. Without it, the random fallback acts as
    a 'reset to random policy' escape hatch, so greedy selection can game the
    score by adding a high-cardinality task-specific feature (all val keys
    become unseen -> pure random walk), instead of selecting features that
    COVER the validation states. The final transfer metric never uses it."""
    key_of = itemgetter(*slots) if len(slots) > 1 else lambda f, _i=slots[0]: (f[_i],)
    wins = total = 0
    for task in tasks:
        n = len(task.free)
        starts = [task.free[(j * n) // starts_per_task] for j in range(starts_per_task)]
        for si, start in enumerate(starts):
            fb = Random(zlib.crc32(f"{task.uid}|{si}".encode()))
            pos = start
            for _ in range(MAX_STEPS):
                q = Q.get(key_of(task.feats[pos]))
                if q is None:
                    if unseen_fail:
                        break
                    a = fb.randrange(4)
                elif fb.random() < EVAL_EPS:
                    a = fb.randrange(4)
                else:
                    m = max(q)
                    a = q.index(m)
                pos, _r, done, win = _step(task, pos, a)
                if done:
                    wins += 1 if win else 0
                    break
            total += 1
    return wins / total


# ---------------------------------------------------------------- gating
def select_slots(suite: Sequence[Task], k: int, rng: Random) -> Tuple[List[int], int]:
    """Learned gating: greedy forward feature selection + one swap-refinement
    pass (repairs forward-selection myopia), under a shared budget. Fit on
    train[:SELECTION_FIT], score on train[SELECTION_VAL] (still train — the
    heldout tasks are never touched). Returns (slots, episodes_spent)."""
    fit = suite[:SELECTION_FIT]
    val = suite[SELECTION_VAL[0]:SELECTION_VAL[1]]
    n_forward = sum(N_FEATURES - i for i in range(k))
    n_swap = k * (N_FEATURES - k)
    proxy_ep = max(50, min(PROXY_EPISODES_NOMINAL,
                           (TOTAL_EPISODE_BUDGET // 2) // (n_forward + n_swap)))
    spent = 0

    def score_set(cand: List[int]) -> float:
        nonlocal spent
        Q: dict = {}
        train(Q, fit, sorted(cand), proxy_ep, rng)
        spent += proxy_ep
        return evaluate(Q, val, sorted(cand), VAL_STARTS, unseen_fail=True)

    selected: List[int] = []
    remaining = list(range(N_FEATURES))
    cur_score = -1.0
    for _round in range(k):
        best_f, best_score = None, -1.0
        for f in remaining:
            s = score_set(selected + [f])
            if s > best_score:   # tie -> keep earlier (lower-index) feature
                best_f, best_score = f, s
        selected.append(best_f)
        remaining.remove(best_f)
        cur_score = best_score

    # swap refinement: try replacing each slot with each unselected feature
    for i in range(k):
        best_f, best_score = None, cur_score
        for f in remaining:
            s = score_set([x for j, x in enumerate(selected) if j != i] + [f])
            if s > best_score:
                best_f, best_score = f, s
        if best_f is not None:
            remaining.append(selected[i])
            selected[i] = best_f
            remaining.remove(best_f)
            cur_score = best_score

    return sorted(selected), spent


# ---------------------------------------------------------------- conditions
def _run_agent(suite: List[Task], slots: Sequence[int],
               episodes: int, rng: Random) -> float:
    Q: dict = {}
    train(Q, suite[:N_TRAIN], slots, episodes, rng)
    return evaluate(Q, suite[N_TRAIN:], slots, EVAL_STARTS)


def _make_condition(name: str, desc: str, kind: str, k: int = PRIMARY_K,
                    log: Optional[dict] = None) -> Condition:
    """kind: 'unlimited' | 'oracle_no_taskid' | 'gated' | 'no_gating'.
    Paired suites: the i-th call uses suite seed SUITE_BASE_SEED+i, so every
    condition sees the identical task suite for seed i.

    WARNING: the pairing relies on a per-condition call counter, so conditions
    must be freshly built (call the registry function again) for every
    run_spec invocation. Reusing a conditions list across two run_spec calls
    would silently shift every suite index."""
    counter = {"i": 0}

    def run(rng: Random) -> float:
        i = counter["i"]
        counter["i"] += 1
        suite = build_suite(SUITE_BASE_SEED + i)
        if kind == "unlimited":
            slots: Sequence[int] = tuple(range(N_FEATURES))
            budget = TOTAL_EPISODE_BUDGET
        elif kind == "oracle_no_taskid":
            # discriminating control (added after adversarial review): full
            # capacity but task-identifying features excluded BY FIAT. If
            # limited_wm merely matches this, capacity pressure adds nothing
            # beyond dropping task-ID features.
            slots = NON_TASKID
            budget = TOTAL_EPISODE_BUDGET
        elif kind == "no_gating":
            # write-without-selectivity: a per-seed random K-subset (a fixed
            # arrival order would predetermine this ablation's outcome)
            slots = tuple(sorted(rng.sample(range(N_FEATURES), k)))
            budget = TOTAL_EPISODE_BUDGET
        else:                                 # gated: selection cost is paid
            slots, spent = select_slots(suite, k, rng)
            budget = TOTAL_EPISODE_BUDGET - spent
        if log is not None:
            log.setdefault(name, []).append(
                {"seed_index": i, "slots": [FEATURE_NAMES[s] for s in slots],
                 "training_episodes": budget})
        return _run_agent(suite, slots, budget, rng)

    return Condition(name, run, desc)


SELECTION_LOG: dict = {}


def wm_abstraction() -> Tuple[List[Condition], str]:
    """REAL replacement for the synthetic wm_abstraction mock.
    Order matters: first condition is the ablation baseline."""
    conditions = [
        _make_condition("unlimited_memory",
                        f"raw unlimited state buffer (all {N_FEATURES} features)",
                        "unlimited", log=SELECTION_LOG),
        _make_condition("limited_wm",
                        f"K={PRIMARY_K} slots + learned gating", "gated",
                        k=PRIMARY_K, log=SELECTION_LOG),
        _make_condition("limited_wm_k2", "ablation: K=2 slots + gating", "gated",
                        k=2, log=SELECTION_LOG),
        _make_condition("limited_wm_k4", "ablation: K=4 slots + gating", "gated",
                        k=4, log=SELECTION_LOG),
        _make_condition("limited_wm_k8", "ablation: K=8 slots + gating", "gated",
                        k=8, log=SELECTION_LOG),
        _make_condition("limited_wm_no_gating",
                        f"ablation: K={PRIMARY_K} random slots, no selection",
                        "no_gating", k=PRIMARY_K, log=SELECTION_LOG),
        _make_condition("oracle_no_taskid",
                        "control: unlimited capacity, task-ID features "
                        "excluded by fiat", "oracle_no_taskid",
                        log=SELECTION_LOG),
    ]
    return conditions, "limited_wm"


REGISTRY_REAL = {"wm_abstraction": wm_abstraction}


# ---------------------------------------------------------------- smoke / report
if __name__ == "__main__":
    import json
    import os
    import sys
    import time

    PILOT_SEED = 987_000   # smoke/pilot suites stay away from confirmatory ones
    t0 = time.time()

    if "--quick" in sys.argv:
        suite = build_suite(PILOT_SEED)
        print(f"suite: {len(suite)} tasks  ({time.time()-t0:.1f}s)")
        rng = Random(0)
        slots, spent = select_slots(suite, PRIMARY_K, rng)
        print("gating picked:", [FEATURE_NAMES[s] for s in slots],
              f"(spent {spent} episodes)")
        acc_l = _run_agent(suite, slots, TOTAL_EPISODE_BUDGET - spent, rng)
        acc_u = _run_agent(suite, tuple(range(N_FEATURES)),
                           TOTAL_EPISODE_BUDGET, Random(0))
        print(json.dumps({"limited_wm": acc_l, "unlimited_memory": acc_u}))
        print(f"total {time.time()-t0:.1f}s")

    elif "--report" in sys.argv:
        # Confirmatory run through the exact same code path as `rsc.py run`
        # (validate -> registry -> run_spec -> format_run), plus diagnostics
        # the generic CLI does not print: per-seed selection log, per-condition
        # raw values, the spec's relative-hypothesis check, and a single-seed
        # OOD probe (exploratory, OUTSIDE the machine verdict).
        _root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        sys.path.insert(0, _root)
        from spec_compiler.model import load_spec
        from spec_compiler.validator import validate, format_report
        from spec_compiler.harness import run_spec, format_run

        spec = load_spec(os.path.join(_root, "specs", "wm_abstraction.yaml"))
        rep = validate(spec)
        if not rep.ok:
            print(format_report(rep, title="wm_abstraction.yaml"))
            raise SystemExit(1)
        conditions, primary = wm_abstraction()
        result = run_spec(spec, conditions, primary=primary)
        print(format_run(result, spec, title="wm_abstraction",
                         provenance="[REAL run — gridworld-heldout-tasks]"))
        print("\n# per-condition seed values")
        for c in result.conditions:
            print(f"  {c.name:<24}{['%.3f' % v for v in c.values]}")
        print("\n# gating selection log (slots per seed)")
        print(json.dumps(SELECTION_LOG, indent=1, ensure_ascii=False))

        by = {c.name: c.mean for c in result.conditions}
        delta = by["limited_wm"] - by["unlimited_memory"]
        print("\n# secondary check — spec's RELATIVE hypothesis (>= +0.10 over baseline)")
        print(f"  limited_wm - unlimited_memory = {delta:+.3f} -> "
              f"{'supported' if delta >= 0.10 else 'not supported'} "
              "(NOT the machine verdict; decision_rule above is the GO/NO-GO)")

        print("\n# exploratory OOD probe (single seed, wall_p 0.12 -> 0.20; outside verdict)")
        suite = build_suite(SUITE_BASE_SEED)
        ood = build_suite(995_000, wall_p=0.20)[N_TRAIN:]
        rng = Random(12345)
        slots, spent = select_slots(suite, PRIMARY_K, rng)
        Q: dict = {}
        train(Q, suite[:N_TRAIN], slots, TOTAL_EPISODE_BUDGET - spent, rng)
        print(f"  limited_wm  slots={[FEATURE_NAMES[s] for s in slots]}")
        print(f"  in-family heldout = {evaluate(Q, suite[N_TRAIN:], slots, EVAL_STARTS):.3f}")
        print(f"  OOD heldout       = {evaluate(Q, ood, slots, EVAL_STARTS):.3f}")
        Qu: dict = {}
        allf = tuple(range(N_FEATURES))
        train(Qu, suite[:N_TRAIN], allf, TOTAL_EPISODE_BUDGET, Random(12345))
        print(f"  unlimited in-family = {evaluate(Qu, suite[N_TRAIN:], allf, EVAL_STARTS):.3f}"
              f"   unlimited OOD = {evaluate(Qu, ood, allf, EVAL_STARTS):.3f}")
        print(f"\ntotal {time.time()-t0:.1f}s")
