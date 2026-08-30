"""
REAL experiment for specs/homeostasis.yaml — EXP-003 / H-OWN (homeostasis).

Geometrizes the homeostatic deviation D_t = Σ_i w_i·|s_i − s_i*| [N F3; O F9]
as a potential over an internal-state space (GEOMETRY.md §3), and tests the
raw files' H1 [N L833]: an agent with an anticipatory self-model of its
internal state beats a reactive (−D_t-greedy) agent SPECIFICALLY under OOD
perturbation, not everywhere.

Environment (new, deterministic, no LLM): a 7×7 world with D=3 needs
(energy, temperature, integrity), one depot per need. Each step all needs
decay; stepping on depot k refills need k to the setpoint 1.0; if any need
hits 0 the agent "dies" (remaining steps counted at max deviation). This is
the smallest world in which reactive vs anticipatory control can dissociate.

Two deterministic policies (NO learning; the manipulation is control STRATEGY,
matching the file's reward-matched + self-model-ablation controls):
  reactive       (= self-model ablated) go to the depot of the currently
                 lowest need — myopic, distance-blind descent on current D_t.
                 [N L822 forbids the agent from *only* doing this; it is the
                 baseline]
  anticipatory   (= predictive self-model / allostasis) model-predictive
                 control: it OWNS a forward model of depletion and, at each
                 step, simulates "head to depot c, then act reactively" for a
                 horizon H for each candidate c, and takes one step toward the
                 c with least predicted deviation. Because c = the reactive
                 choice is always among the candidates, the planner can never
                 do worse than reactive in simulation; its edge is that it also
                 weighs travel distance and foresees deaths. Under slow decay
                 reactive is already near-optimal so the edge is ~0; under fast
                 decay, distance-aware planning matters more.
                 Declared cost [N wants this stated]: the planner spends more
                 compute per step than reactive.

GATED vs REPORTED (per adversarial review — keep these straight): the
preregistered, machine-gated quantity is advantage_ood (spec failure_condition
and decision_rule both operate on it). The OOD-SPECIFICITY claim ("helps MORE
under OOD than in-distribution", the premium = advantage_ood −
advantage_indist) is a REPORTED SECONDARY OBSERVATION only — the verdict would
be identical even if the premium were zero. A follow-up spec must gate the
premium itself if OOD-specificity is to be a preregistered claim.

Primary metric (faithful to the raw file's H1, N L833 — "self-model gives
INCREMENTAL performance under OOD"): advantage_OOD = mean_reactive_deviation −
mean_anticipatory_deviation under the OOD (fast-decay) perturbation. The
in-distribution advantage is reported as a control, and a reactive-vs-reactive
null pins the zero-point (exactly 0). If advantage_OOD ≈ 0 the self-model adds
no regulation value → DISCARD. Pilot (family 995500) showed advantage_OOD ≈
0.02-0.04 with a small positive OOD premium; parameters were then FROZEN and
the confirmatory run uses a fresh seed family (996000+). Fully deterministic
given the task batch.

SCOPE: C3-flavored (self-maintenance / valenced agency in the file's ladder),
but the metric is functional regulation ONLY. Forbidden interpretation:
pain/pleasure/affect. Permitted: functional valuation [N L867-871].
"""
from __future__ import annotations

from collections import deque
from random import Random
from typing import Dict, List, Sequence, Tuple

from spec_compiler.harness import Condition

GRID = 7
N_NEEDS = 3
WALL_P = 0.10
T_STEPS = 120
N_TASKS = 60
DECAY_INDIST = (0.030, 0.035, 0.040)
OOD_FACTOR = 1.8                         # OOD perturbation: faster depletion (FROZEN)
SETPOINT = 1.0
WEIGHTS = (1.0, 1.0, 1.0)
MPC_HORIZON = 40                        # planning lookahead; MUST exceed max
                                        # time-to-live (~1/min_decay ≈ 33) so the
                                        # planner can see neglect-deaths (FROZEN)
HOMEO_BASE_SEED = 996_000               # CONFIRMATORY family (disjoint from all
                                        # others); pilot/sweep used 995_500
MOVES = ((0, -1), (1, 0), (0, 1), (-1, 0), (0, 0))   # 4-dir + stay

HOMEO_LOG: dict = {}


# ---------------------------------------------------------------- environment
class HomeoTask:
    __slots__ = ("walls", "depots", "start", "dists")

    def __init__(self, walls, depots, start, dists):
        self.walls = walls          # frozenset of wall cells
        self.depots = depots        # tuple of D depot cells
        self.start = start          # start cell
        self.dists = dists          # list[D] of {cell: dist-to-depot_k}


def _connected(cells: set) -> bool:
    start = next(iter(cells))
    seen, stack = {start}, [start]
    while stack:
        x, y = stack.pop()
        for dx, dy in MOVES[:4]:
            n = (x + dx, y + dy)
            if n in cells and n not in seen:
                seen.add(n)
                stack.append(n)
    return seen == cells


def _bfs_dist(passable: set, source) -> Dict[Tuple[int, int], int]:
    dist = {source: 0}
    dq = deque([source])
    while dq:
        c = dq.popleft()
        for dx, dy in MOVES[:4]:
            n = (c[0] + dx, c[1] + dy)
            if n in passable and n not in dist:
                dist[n] = dist[c] + 1
                dq.append(n)
    return dist


def make_task(rng: Random) -> HomeoTask:
    while True:
        walls = {(x, y) for x in range(GRID) for y in range(GRID)
                 if rng.random() < WALL_P}
        cells = {(x, y) for x in range(GRID) for y in range(GRID)} - walls
        if len(cells) < 16 or not _connected(cells):
            continue
        spots = sorted(cells)
        picks = rng.sample(spots, N_NEEDS + 1)
        depots, start = tuple(picks[:N_NEEDS]), picks[N_NEEDS]
        dists = [_bfs_dist(cells, d) for d in depots]
        # every cell must be able to reach every depot
        if not all(all(c in dm for c in cells) for dm in dists):
            continue
        return HomeoTask(frozenset(walls), depots, start, dists)


def build_batch(seed: int) -> List[HomeoTask]:
    return [make_task(Random(seed * 100_003 + i * 7919)) for i in range(N_TASKS)]


# ---------------------------------------------------------------- rollout
def _step_toward(task: HomeoTask, pos, depot_idx):
    """One greedy BFS step from pos toward depots[depot_idx]. Ties -> lowest
    move index. Returns next cell (never a wall)."""
    dm = task.dists[depot_idx]
    here = dm[pos]
    if here == 0:
        return pos
    best_move, best_d = 4, here          # index 4 = stay
    for a, (dx, dy) in enumerate(MOVES[:4]):
        n = (pos[0] + dx, pos[1] + dy)
        d = dm.get(n)
        if d is not None and d < best_d:
            best_move, best_d = a, d
    dx, dy = MOVES[best_move]
    return (pos[0] + dx, pos[1] + dy)


def _advance(task, s, pos, target, decay):
    """Apply one step of the true dynamics heading toward `target` depot.
    Returns (new_s, new_pos, dead, step_deviation_normalized)."""
    npos = _step_toward(task, pos, target)
    ns = [s[k] - decay[k] for k in range(N_NEEDS)]
    for k, d in enumerate(task.depots):
        if npos == d:
            ns[k] = SETPOINT
    dead = any(v <= 0.0 for v in ns)
    dev = sum(WEIGHTS[k] * abs(SETPOINT - ns[k]) for k in range(N_NEEDS)) / N_NEEDS
    return ns, npos, dead, dev


def _reactive_target(s):
    return min(range(N_NEEDS), key=lambda k: (s[k], k))


def _sim_cost(task, s, pos, decay, first_target, horizon):
    """Simulate 'head to depot first_target until reached, then act reactively'
    for `horizon` steps; return cumulative normalized deviation (death fills the
    remainder at max 1.0)."""
    sim_s, sim_pos, cost = list(s), pos, 0.0
    committed = first_target
    for h in range(horizon):
        if committed is not None and sim_pos != task.depots[committed]:
            tgt = committed
        else:
            committed = None
            tgt = _reactive_target(sim_s)
        sim_s, sim_pos, dead, dev = _advance(task, sim_s, sim_pos, tgt, decay)
        if dead:
            return cost + (horizon - h) * 1.0
        cost += dev
    return cost


def _plan_target(task, s, pos, decay, horizon):
    """MPC: pick the first-target depot minimizing predicted horizon cost.
    Reactive's own choice is among the candidates, so the plan is never worse
    than reactive in simulation; its edge is weighing travel distance and
    foreseeing neglect-deaths. Tie -> lowest need index."""
    best_c, best_cost = 0, float("inf")
    for c in range(N_NEEDS):
        cost = _sim_cost(task, s, pos, decay, c, horizon)
        if cost < best_cost:
            best_c, best_cost = c, cost
    return best_c


def rollout(task: HomeoTask, decay: Sequence[float], policy: str) -> float:
    """Return mean per-step normalized deviation over T_STEPS (death fills the
    rest at max deviation 1.0). Lower = better regulation."""
    s = [SETPOINT] * N_NEEDS
    pos = task.start
    total = 0.0
    for t in range(T_STEPS):
        if policy == "anticipatory":
            best_c = _plan_target(task, s, pos, decay, MPC_HORIZON)
            # mirror the sim's first action: once the planned depot is reached,
            # the plan continues reactively — so must the executor, else it
            # sits on a full depot forever while other needs deplete.
            target = _reactive_target(s) if pos == task.depots[best_c] else best_c
        else:
            target = _reactive_target(s)
        s, pos, dead, dev = _advance(task, s, pos, target, decay)
        if dead:
            total += (T_STEPS - t) * 1.0
            return total / T_STEPS
        total += dev
    return total / T_STEPS


def _mean_dev(batch, decay, policy) -> float:
    return sum(rollout(t, decay, policy) for t in batch) / len(batch)


# ---------------------------------------------------------------- conditions
def _make(name: str, kind: str) -> Condition:
    counter = {"i": 0}
    ood = tuple(d * OOD_FACTOR for d in DECAY_INDIST)

    def run(_rng: Random) -> float:
        i = counter["i"]
        counter["i"] += 1
        batch = build_batch(HOMEO_BASE_SEED + i)
        r_ind = _mean_dev(batch, DECAY_INDIST, "reactive")
        a_ind = _mean_dev(batch, DECAY_INDIST, "anticipatory")
        r_ood = _mean_dev(batch, ood, "reactive")
        a_ood = _mean_dev(batch, ood, "anticipatory")
        HOMEO_LOG.setdefault(name, []).append(
            {"seed_index": i,
             "reactive_indist": round(r_ind, 4), "anticip_indist": round(a_ind, 4),
             "reactive_ood": round(r_ood, 4), "anticip_ood": round(a_ood, 4),
             "advantage_indist": round(r_ind - a_ind, 4),
             "advantage_ood": round(r_ood - a_ood, 4),
             "premium": round((r_ood - a_ood) - (r_ind - a_ind), 4)})
        if kind == "null":
            return r_ood - r_ood            # reactive vs reactive: exactly 0 (zero-point)
        if kind == "indist_advantage":
            return r_ind - a_ind            # control: advantage in-distribution
        return r_ood - a_ood                # ood_advantage (PRIMARY)

    return Condition(name, run, name)


def homeostasis() -> Tuple[List[Condition], str]:
    conditions = [
        _make("null_control", "null"),               # zero-point (reactive vs reactive)
        _make("indist_advantage", "indist_advantage"),  # control: advantage in-distribution
        _make("ood_advantage", "ood_advantage"),     # PRIMARY: advantage under OOD
    ]
    return conditions, "ood_advantage"


# ---------------------------------------------------------------- smoke
if __name__ == "__main__":
    import json
    import time
    t0 = time.time()
    batch = build_batch(HOMEO_BASE_SEED)
    ood = tuple(d * OOD_FACTOR for d in DECAY_INDIST)
    r_ind = _mean_dev(batch, DECAY_INDIST, "reactive")
    a_ind = _mean_dev(batch, DECAY_INDIST, "anticipatory")
    r_ood = _mean_dev(batch, ood, "reactive")
    a_ood = _mean_dev(batch, ood, "anticipatory")
    print(json.dumps({
        "reactive_indist": round(r_ind, 4), "anticip_indist": round(a_ind, 4),
        "advantage_indist": round(r_ind - a_ind, 4),
        "reactive_ood": round(r_ood, 4), "anticip_ood": round(a_ood, 4),
        "advantage_ood": round(r_ood - a_ood, 4),
        "premium": round((r_ood - a_ood) - (r_ind - a_ind), 4),
    }, indent=1))
    print(f"total {time.time()-t0:.1f}s")
