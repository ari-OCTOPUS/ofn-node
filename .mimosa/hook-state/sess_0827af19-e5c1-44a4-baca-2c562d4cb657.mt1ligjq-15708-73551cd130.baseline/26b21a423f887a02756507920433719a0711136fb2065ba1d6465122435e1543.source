"""
REAL experiment for specs/causal_selfmodel.yaml — H-OWN-07 / EXP-007.

Claim under test (raw corpus, self-model ladder): a GENUINE self-model must
PREDICT its own error/failure states from CAUSAL access to its own internal
computation, not merely DESCRIBE the situation from the outside. Operationalized
here with zero LLM, fully deterministic, reusing gridworld_wm verbatim
(improve-not-rewrite).

Setup: train one tabular Q agent on the deterministic grid-world family using
the abstract minimal-sufficient representation (MINIMAL_SUFFICIENT, K=6 — a
FIXED 6-slot state keying, the same relational statistic ADR-001 froze; it is
NOT learned or selected in this experiment). On a heldout task family the agent has
a genuine, mixed failure rate. For each heldout EPISODE (task x start) we ask a
SELF-MODEL to predict, from START-STATE features only (no outcome peeking),
whether the agent will FAIL that episode (fail=1: reach the wrong object or time
out; success=0: reach the cue-matching target). Two self-models, same classifier,
same episodes, same split:

  status_auc  (verbal/description): predicts failure from a COARSE, EXTERNAL
              account of the SITUATION — BFS distance to target, BFS distance to
              the distractor/loser, their difference, local wall count, Manhattan
              geometry. A genuinely competitive difficulty model that DESCRIBES
              the world but never introspects the agent's learned state. NOT a
              strawman: task geometry is strongly predictive of success.
  causal_auc  (self-model): predicts failure from the agent's OWN internal
              computation — value confidence at the start key (max-Q, Q-gap),
              whether the start key and its neighbours were ever seen in training
              (representational-bin coverage), the local value landscape, and a
              short IMAGINED greedy rollout (the agent simulates itself H steps
              through its own Q + transition model, WITHOUT peeking at the
              outcome) measuring novelty/low-confidence ahead.

Primary metric = causal_advantage = AUC(causal self-model) - AUC(status
self-model) on the heldout TEST split (paired: identical agent, identical
episodes, identical classifier per seed). This is genuinely FALSIFIABLE: it is
<= 0 whenever the agent's internal signals add nothing beyond a purely
descriptive account of task difficulty. It is NOT trivially clearable — the bar
is beating a real geometric difficulty model, not a constant. Direction is
higher_is_better.

Control (per prompt): shuffled_causal_auc — the causal features with their
train-split labels PERMUTED before fitting, evaluated on the real test labels.
This collapses to ~0.5 (chance), confirming the causal AUC reflects genuine
information in the internal signals rather than classifier/feature-count
artefacts. Because both self-models are FIT on one split of heldout tasks and
SCORED on a DISJOINT split, feature count cannot buy test-set AUC (noise
features test at ~0.5), so the causal-vs-status comparison is fair despite the
causal vector being wider (7 causal features vs the status model's 5).

Determinism: agent training RNG, task suites, episode starts, and the shuffle
permutation are all derived from fixed seeds. No LLM anywhere.

SCOPE: C0/C1 functional self-prediction in a tabular grid-world only. The metric
is prediction skill about the agent's OWN task failures. Forbidden
interpretation: introspection-as-experience, self-awareness, qualia. Permitted:
functional access of a controller to its own computational state.

Pilot family 984500 (disjoint), used only to set the honest decision bands, then
FROZEN. Confirmatory conditions use family 984000 (disjoint from pilot and from
gridworld 991000/987000, gain 994000, homeostasis 996000/995500,
consolidation 998000, drake 997000, geometry 993000).
"""
from __future__ import annotations

import math
import zlib
from collections import deque
from operator import itemgetter
from random import Random
from typing import Dict, List, Sequence, Tuple

from spec_compiler.harness import Condition

from .gridworld_wm import (
    EVAL_EPS, EVAL_STARTS, GRID, MAX_STEPS, MINIMAL_SUFFICIENT, MOVES, N_TRAIN,
    _step, build_suite, train,
)

# ---------------------------------------------------------------- constants
CAUSAL_BASE_SEED = 984_000        # CONFIRMATORY family (disjoint from pilot)
PILOT_BASE_SEED = 984_500         # pilot family (bands set here, then FROZEN)
AGENT_EPISODES = 80_000           # modest budget: abstract K=6 agent, mixed fail rate
SELF_FIT_TASKS = 30               # heldout[:30] fits the self-model classifier,
                                  # heldout[30:] is the untouched self-model TEST set
IMAGINE_H = 6                     # imagined-rollout horizon (self-simulation)
LOGREG_ITERS = 300
LOGREG_LR = 0.3
LOGREG_L2 = 1e-3

_KEY = itemgetter(*MINIMAL_SUFFICIENT)   # 6-slot abstract state key

CAUSAL_LOG: dict = {}
_CACHE: Dict[int, dict] = {}


# ---------------------------------------------------------------- geometry
def _bfs(passable: set, source) -> Dict[Tuple[int, int], int]:
    dist = {source: 0}
    dq = deque([source])
    while dq:
        c = dq.popleft()
        for dx, dy in MOVES:
            n = (c[0] + dx, c[1] + dy)
            if n in passable and n not in dist:
                dist[n] = dist[c] + 1
                dq.append(n)
    return dist


# ---------------------------------------------------------------- internal probes
def _qstats(Q: dict, key) -> Tuple[float, float, int]:
    """(max_Q, Q_gap, seen) for a state key; unseen -> (0,0,0)."""
    q = Q.get(key)
    if q is None:
        return 0.0, 0.0, 0
    m = max(q)
    second = sorted(q)[-2]
    return m, m - second, 1


def _neighbors(task, pos) -> List[Tuple[int, int]]:
    out = []
    for dx, dy in MOVES:
        n = (pos[0] + dx, pos[1] + dy)
        if n in task.feats:          # passable (feats defined for all walkable cells)
            out.append(n)
    return out


def _imagine(Q: dict, task, start, horizon: int) -> Tuple[float, float]:
    """The agent simulates ITSELF: follow greedy Q for `horizon` steps using the
    real transition model (walls respected) but treating target/loser as ordinary
    cells (it never peeks at the outcome). Returns (novelty_ahead, min_gap_ahead):
    fraction of imagined states whose key is UNSEEN in training, and the smallest
    Q-gap encountered (0.0 if any unseen). No RNG — pure self-forward-model."""
    pos = start
    unseen = 0
    steps = 0
    min_gap = math.inf
    saw_seen = False
    for _ in range(horizon):
        key = _KEY(task.feats[pos])
        q = Q.get(key)
        steps += 1
        if q is None:
            unseen += 1
            a = 0
            min_gap = 0.0
        else:
            m = max(q)
            a = q.index(m)
            min_gap = min(min_gap, m - sorted(q)[-2])
            saw_seen = True
        dx, dy = MOVES[a]
        n = (pos[0] + dx, pos[1] + dy)
        if n not in task.feats:      # wall / out of bounds -> stay
            n = pos
        pos = n
    nov = unseen / steps if steps else 1.0
    return nov, (min_gap if saw_seen else 0.0)


# ---------------------------------------------------------------- feature vectors
def _status_feats(task, start, dist_t, dist_l) -> List[float]:
    """External, descriptive account of the SITUATION (no introspection)."""
    dt = dist_t.get(start, 2 * GRID)
    dl = dist_l.get(start, 2 * GRID)
    wc = bin(task.feats[start][10]).count("1")     # local wall count (0..4)
    tx, ty = task.target
    man = abs(tx - start[0]) + abs(ty - start[1])
    return [dt / GRID, dl / GRID, (dl - dt) / GRID, wc / 4.0, man / (2.0 * GRID)]


def _causal_feats(Q: dict, task, start) -> List[float]:
    """The agent's OWN internal computation at the start state (causal access)."""
    m, gap, seen = _qstats(Q, _KEY(task.feats[start]))
    nbrs = _neighbors(task, start)
    seen_cnt = 0
    qsum = 0.0
    for nb in nbrs:
        nm, _g, ns = _qstats(Q, _KEY(task.feats[nb]))
        seen_cnt += ns
        qsum += nm
    nb_frac = seen_cnt / len(nbrs) if nbrs else 0.0
    nb_meanq = qsum / len(nbrs) if nbrs else 0.0
    nov, min_gap = _imagine(Q, task, start, IMAGINE_H)
    return [m, gap, float(seen), nb_frac, nb_meanq, nov, min_gap]


# ---------------------------------------------------------------- labels
def _rollout_fail(Q: dict, task, start) -> int:
    """Run the learned eps-greedy eval policy (identical regime to gridworld's
    evaluate) from `start`. Returns 1 if the agent FAILS (reaches the loser or
    times out), 0 if it reaches the cue-matching target. Deterministic via a
    per-episode CRC-seeded RNG."""
    fb = Random(zlib.crc32(f"{task.uid}|{start}".encode()))
    pos = start
    for _ in range(MAX_STEPS):
        q = Q.get(_KEY(task.feats[pos]))
        if q is None:
            a = fb.randrange(4)
        elif fb.random() < EVAL_EPS:
            a = fb.randrange(4)
        else:
            a = q.index(max(q))
        pos, _r, done, win = _step(task, pos, a)
        if done:
            return 0 if win else 1
    return 1


def _dataset(Q: dict, tasks) -> Tuple[List[List[float]], List[List[float]], List[int]]:
    Xs: List[List[float]] = []
    Xc: List[List[float]] = []
    y: List[int] = []
    for task in tasks:
        passable = set(task.feats)
        dist_t = _bfs(passable, task.target)
        dist_l = _bfs(passable, task.loser)
        n = len(task.free)
        starts = [task.free[(j * n) // EVAL_STARTS] for j in range(EVAL_STARTS)]
        for start in starts:
            y.append(_rollout_fail(Q, task, start))
            Xs.append(_status_feats(task, start, dist_t, dist_l))
            Xc.append(_causal_feats(Q, task, start))
    return Xs, Xc, y


# ---------------------------------------------------------------- classifier
def _standardize(Xfit, Xtest):
    d = len(Xfit[0])
    nf = len(Xfit)
    means = [sum(row[j] for row in Xfit) / nf for j in range(d)]
    stds = []
    for j in range(d):
        var = sum((row[j] - means[j]) ** 2 for row in Xfit) / nf
        stds.append(math.sqrt(var) if var > 1e-12 else 1.0)

    def z(X):
        return [[(row[j] - means[j]) / stds[j] for j in range(d)] for row in X]

    return z(Xfit), z(Xtest)


def _sigmoid(z: float) -> float:
    if z < -30:
        return 0.0
    if z > 30:
        return 1.0
    return 1.0 / (1.0 + math.exp(-z))


def _fit_logreg(X, y, iters=LOGREG_ITERS, lr=LOGREG_LR, l2=LOGREG_L2):
    n = len(X)
    d = len(X[0])
    w = [0.0] * d
    b = 0.0
    for _ in range(iters):
        gw = [0.0] * d
        gb = 0.0
        for i in range(n):
            p = _sigmoid(b + sum(w[j] * X[i][j] for j in range(d)))
            e = p - y[i]
            for j in range(d):
                gw[j] += e * X[i][j]
            gb += e
        for j in range(d):
            w[j] -= lr * (gw[j] / n + l2 * w[j])
        b -= lr * (gb / n)
    return w, b


def _predict(w, b, X):
    return [_sigmoid(b + sum(w[j] * X[i][j] for j in range(len(w)))) for i in range(len(X))]


def _auc(scores, y) -> float:
    """Mann-Whitney AUC for predicting fail (label 1). 0.5 if a class is empty."""
    pos = [s for s, l in zip(scores, y) if l == 1]
    neg = [s for s, l in zip(scores, y) if l == 0]
    if not pos or not neg:
        return 0.5
    c = 0.0
    for p in pos:
        for q in neg:
            if p > q:
                c += 1.0
            elif p == q:
                c += 0.5
    return c / (len(pos) * len(neg))


# ---------------------------------------------------------------- pipeline
def _run_pipeline(base: int, i: int) -> dict:
    """Train one agent, build the heldout self-model dataset, fit + score the
    status, causal and shuffled-causal self-models. Fully deterministic."""
    suite = build_suite(base + i)
    Q: dict = {}
    train(Q, suite[:N_TRAIN], MINIMAL_SUFFICIENT, AGENT_EPISODES,
          Random(base * 7 + i))
    held = suite[N_TRAIN:]
    fit_tasks = held[:SELF_FIT_TASKS]
    test_tasks = held[SELF_FIT_TASKS:]

    Xs_fit, Xc_fit, y_fit = _dataset(Q, fit_tasks)
    Xs_te, Xc_te, y_te = _dataset(Q, test_tasks)

    # status self-model
    Xs_fit_z, Xs_te_z = _standardize(Xs_fit, Xs_te)
    ws, bs = _fit_logreg(Xs_fit_z, y_fit)
    auc_status = _auc(_predict(ws, bs, Xs_te_z), y_te)

    # causal self-model
    Xc_fit_z, Xc_te_z = _standardize(Xc_fit, Xc_te)
    wc, bc = _fit_logreg(Xc_fit_z, y_fit)
    auc_causal = _auc(_predict(wc, bc, Xc_te_z), y_te)

    # shuffled control: causal features, permuted fit labels -> ~chance
    perm = list(range(len(y_fit)))
    Random(base * 13 + i + 1).shuffle(perm)
    y_shuf = [y_fit[p] for p in perm]
    wsh, bsh = _fit_logreg(Xc_fit_z, y_shuf)
    auc_shuf = _auc(_predict(wsh, bsh, Xc_te_z), y_te)

    return {
        "status": auc_status,
        "causal": auc_causal,
        "shuffled": auc_shuf,
        "advantage": auc_causal - auc_status,
        "fit_fail_rate": sum(y_fit) / len(y_fit),
        "test_fail_rate": sum(y_te) / len(y_te),
        "n_test": len(y_te),
    }


def _compute(i: int) -> dict:
    if i not in _CACHE:
        _CACHE[i] = _run_pipeline(CAUSAL_BASE_SEED, i)
    return _CACHE[i]


# ---------------------------------------------------------------- conditions
def _make(name: str, key: str) -> Condition:
    counter = {"i": 0}

    def run(_rng: Random) -> float:
        i = counter["i"]
        counter["i"] += 1
        r = _compute(i)
        CAUSAL_LOG.setdefault(name, []).append(
            {"seed_index": i, **{k: round(v, 4) for k, v in r.items()}})
        return r[key]

    return Condition(name, run, name)


def causal_selfmodel() -> Tuple[List[Condition], str]:
    """REAL H-OWN-07. Baseline (descriptive) first, PRIMARY (causal advantage)
    last. Conditions share a per-seed-index cache so every one sees the identical
    agent + episodes for seed i (proper pairing)."""
    conditions = [
        _make("status_auc", "status"),                 # descriptive baseline
        _make("causal_auc", "causal"),                 # self-model
        _make("shuffled_causal_auc", "shuffled"),      # null control (~chance)
        _make("causal_advantage", "advantage"),        # PRIMARY: causal - status
    ]
    return conditions, "causal_advantage"


REGISTRY_REAL = {"causal_selfmodel": causal_selfmodel}


# ---------------------------------------------------------------- smoke / pilot
if __name__ == "__main__":
    import json
    import os
    import sys
    import time

    t0 = time.time()

    if "--report" in sys.argv:
        # Confirmatory path: validate -> run_spec -> format_run (no registry edit).
        _root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        sys.path.insert(0, _root)
        from spec_compiler.model import load_spec
        from spec_compiler.validator import validate, format_report
        from spec_compiler.harness import run_spec, format_run

        spec = load_spec(os.path.join(_root, "specs", "causal_selfmodel.yaml"))
        rep = validate(spec)
        if not rep.ok:
            print(format_report(rep, title="causal_selfmodel.yaml"))
            raise SystemExit(1)
        conditions, primary = causal_selfmodel()
        result = run_spec(spec, conditions, primary=primary)
        print(format_run(result, spec, title="causal_selfmodel",
                         provenance="[REAL run — gridworld self-failure prediction]"))
        print("\n# per-condition seed values")
        for c in result.conditions:
            print(f"  {c.name:<22}{['%.3f' % v for v in c.values]}")
        print("\n# per-seed log")
        print(json.dumps(CAUSAL_LOG, indent=1))
        print(f"\ntotal {time.time()-t0:.1f}s")

    else:
        # PILOT (family 984500, disjoint from confirmatory) — set bands, then FREEZE.
        seeds = int(sys.argv[sys.argv.index("--seeds") + 1]) if "--seeds" in sys.argv else 3
        rows = [_run_pipeline(PILOT_BASE_SEED, i) for i in range(seeds)]
        for i, r in enumerate(rows):
            print(f"seed {i}: status={r['status']:.3f} causal={r['causal']:.3f} "
                  f"shuffled={r['shuffled']:.3f} adv={r['advantage']:+.3f} "
                  f"(test_fail_rate={r['test_fail_rate']:.2f}, n={r['n_test']})")
        adv = [r["advantage"] for r in rows]
        st = [r["status"] for r in rows]
        ca = [r["causal"] for r in rows]
        sh = [r["shuffled"] for r in rows]
        mean = lambda v: sum(v) / len(v)
        print(f"\nMEAN  status={mean(st):.3f} causal={mean(ca):.3f} "
              f"shuffled={mean(sh):.3f} advantage={mean(adv):+.3f}")
        print(f"advantage range [{min(adv):+.3f}, {max(adv):+.3f}]")
        print(f"total {time.time()-t0:.1f}s")
