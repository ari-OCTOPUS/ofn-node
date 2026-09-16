"""
REAL experiment for specs/retrieve_compute.yaml — EXP-005 (retrieve-vs-compute).

Tests a kernel-level control claim: WHEN to reuse a cached answer versus recompute
it from scratch is a resource-rational DECISION, not a fixed policy. A learned
per-state scheduler that RETRIEVES a cached policy (cheap, but wrong on drifted
states) or COMPUTES fresh (expensive, but correct) should achieve lower
regret-under-compute-budget than EITHER pure strategy — but only when the
staleness signal it reads is actually informative about which cached answers
have gone stale.

Design lineage: a small deterministic contextual env in the exact spirit of
experiments/control_signals.py (contextual-choice universe, CRC-seeded, full
determinism, no LLM) and experiments/homeostasis.py (an explicit COMPUTE cost is
named and paid). Nothing here reuses gridworld_wm — a cache/compute study needs a
drift dimension gridworld's fixed task family does not expose — but it follows the
same discipline: one shared universe per seed-index, conditions differ ONLY in the
independent variable, pilot->freeze->confirmatory on a disjoint seed family.

Environment (deterministic, no LLM). A universe is N contextual decision STATES.
For each state x:
  * val_old[x][.]  A arm-values at cache-build time; cache(x)=argmax(val_old[x]).
  * m(x) ~ U(0,1)  the state's TRUE drift magnitude since the cache was built.
  * val_new[x][.] = val_old[x][.] + m(x)*DRIFT_SCALE*N(0,1)   (drift_on universes)
                  = val_old[x][.]                             (no-drift null)
  * a*(x) = argmax(val_new[x]); regret_retrieve(x) = val_new[x][a*] −
    val_new[x][cache(x)] >= 0  (0 if the cached arm is still optimal).
  * z(x) = m(x) + N(0,SIGMA)   a NOISY, observable staleness proxy. The scheduler
    sees z ONLY — never m, never the values, never regret. z is correlated with
    drift, hence only *partially* with regret (a state can drift a lot yet leave
    the cached arm near-optimal), so even a perfect threshold on z is imperfect at
    predicting regret — this is what keeps the primary genuinely falsifiable.

Objective (a cost; LOWER is better) — retrieval AND compute costs both in it:
    J(choice, x) = decision_regret(choice, x) + PRICE * compute_cost(choice)
  with compute_cost(retrieve)=C_RETRIEVE (cheap), compute_cost(compute)=C_COMPUTE
  (expensive), regret(compute)=0 (fresh compute is correct), regret(retrieve)=
  regret_retrieve(x). PRICE is the shadow price of a unit of compute — the
  Lagrangian form of "minimize regret at a fixed compute budget". PRICE, SIGMA,
  DRIFT_SCALE and the costs are FROZEN from the pilot family (see __main__
  --calibrate); the confirmatory family is disjoint and never piloted.

Strategies (evaluated on the SAME heldout states; threshold learned on train ONLY):
  always_retrieve   compute nothing.            J = mean(regret) + PRICE*C_RETRIEVE
  always_compute    compute everything.         J = PRICE*C_COMPUTE
  learned_scheduler compute iff z(x) >= tau, tau = the threshold minimizing TRAIN J
                    (empirical-risk 1-parameter classifier; tie -> higher tau =
                    less compute). Evaluated on the disjoint heldout split.

PRIMARY metric (the mechanism-specific, non-strawman quantity — the failure mode
ADR-008 caught was gating an inflated quantity a pure strategy could clear):
    scheduler_advantage = min(J_always_retrieve, J_always_compute) − J_learned
                          on HELDOUT states.
Advantage over the BETTER of the two pure baselines, so the scheduler must beat
whichever pure strategy is already best at the frozen operating point — it cannot
be cleared by "just always compute" or "just always retrieve". Falsifiable: it can
be <= 0 (uninformative signal collapses the learned threshold to a pure endpoint;
a train-fit threshold can fail to generalize to heldout; a PRICE regime where one
pure strategy is already near-optimal leaves no room). Higher is better.

Controls (null + discriminating, per the non-strawman rule):
  no_drift_null    same pipeline on a DRIFT-OFF universe (val_new==val_old, every
                   cache still optimal, all regret 0). Retrieve is optimal and
                   there is nothing to schedule -> advantage is EXACTLY 0. Proves
                   the advantage is CAUSED by cache drift, not by the mechanism.
                   (Analogous to memory_policy.null_unbounded / homeostasis in-dist.)
  shuffled_signal  drift-on universe, but z is PERMUTED across the pooled states
                   before the identical learn-tau/eval pipeline runs. The signal
                   now carries no information about which caches are stale, so a
                   random compute-subset lies on the line between the two pure
                   endpoints and CANNOT beat their min -> advantage ~0. Proves the
                   win comes from the signal being INFORMATIVE, not from merely
                   spending an intermediate compute budget (rebuts "any mixing beats
                   the endpoints"). This is the discriminating control the spec
                   names.

Determinism: for seed-index i every condition builds its universe from a fixed
function of (CONF_BASE_SEED+i); drift-on conditions (shuffled_signal, primary)
share the bit-identical universe and differ ONLY in the z-permutation. The harness
RNG is ignored for universe construction (its seed differs by condition name); all
internal randomness is CRC-seeded from i. Pilot family 962000-962004 set and FROZE
the bands; confirmatory family 962500-962504 was never piloted. Zero LLM.

SCOPE: C0-C3 (functional compute-allocation control). "staleness" and "regret" are
DEFINED SCALARS (a drift proxy; a value gap), NOT phenomenal states. Forbidden
interpretation: felt effort, felt confidence. Permitted: functional cost control.
"""
from __future__ import annotations

import zlib
from random import Random
from typing import List, Sequence, Tuple

from spec_compiler.harness import Condition

# ---------------------------------------------------------------- constants (FROZEN)
A_ARMS = 4
N_STATES = 240
N_TRAIN = 140                 # states 0..139 learn tau; 140..239 are heldout eval
DRIFT_SCALE = 0.60            # per-state drift injected into arm values (FROZEN)
SIGMA = 0.15                  # staleness-signal observation noise (FROZEN)
C_RETRIEVE = 1.0             # cheap: reuse the cached policy
C_COMPUTE = 8.0             # expensive: recompute fresh
PRICE = 0.020                # shadow price of one unit of compute (FROZEN)
CONF_BASE_SEED = 962_500     # CONFIRMATORY family (disjoint); pilot used 962000-962004
RC_LOG: dict = {}


# ---------------------------------------------------------------- environment
def build_universe(seed: int, drift_on: bool = True
                   ) -> Tuple[List[float], List[float]]:
    """Deterministic cache/compute universe. Returns (regret, signal), each an
    N_STATES-long list. regret[x] = value lost by RETRIEVING the cached arm on the
    (possibly drifted) current values (>=0). signal[x] = the noisy observable
    staleness proxy z(x) the scheduler is allowed to read.

    The draw order is fixed so drift-on universes are bit-identical across the
    shuffled_signal and primary conditions for the same seed."""
    rng = Random(seed)
    regret: List[float] = []
    signal: List[float] = []
    for _x in range(N_STATES):
        val_old = [rng.uniform(-0.5, 0.5) for _ in range(A_ARMS)]
        cache = max(range(A_ARMS), key=lambda a: val_old[a])
        m = rng.random()                              # true drift magnitude
        if drift_on:
            val_new = [val_old[a] + m * DRIFT_SCALE * rng.gauss(0.0, 1.0)
                       for a in range(A_ARMS)]
        else:
            # consume the SAME number of RNG draws so the stream stays aligned,
            # then discard them: no drift -> cache stays optimal, regret 0.
            for _a in range(A_ARMS):
                rng.gauss(0.0, 1.0)
            val_new = list(val_old)
        astar = max(range(A_ARMS), key=lambda a: val_new[a])
        regret.append(val_new[astar] - val_new[cache])
        signal.append(m + rng.gauss(0.0, SIGMA))
    return regret, signal


# ---------------------------------------------------------------- scheduler
def _J(regret: Sequence[float], signal: Sequence[float], idx: Sequence[int],
       tau: float, price: float) -> float:
    """Mean objective over states `idx`: compute iff signal>=tau (pay C_COMPUTE,
    0 regret), else retrieve (pay C_RETRIEVE, eat that state's retrieve-regret)."""
    total = 0.0
    for x in idx:
        if signal[x] >= tau:
            total += price * C_COMPUTE
        else:
            total += regret[x] + price * C_RETRIEVE
    return total / len(idx)


def learn_tau(regret: Sequence[float], signal: Sequence[float],
              train_idx: Sequence[int], price: float) -> float:
    """Empirical-risk 1-parameter scheduler: pick the staleness threshold tau
    minimizing TRAIN objective. Candidates = every distinct train signal value
    (compute iff z>=tau) plus the two pure endpoints (-inf = compute-all,
    +inf = retrieve-all). Tie -> highest tau (compute least). Heldout untouched."""
    zs = sorted({signal[x] for x in train_idx})
    cands = [float("-inf")] + zs + [float("inf")]
    scored = [(_J(regret, signal, train_idx, tau, price), tau) for tau in cands]
    best_J = min(j for j, _ in scored)
    # tie-break toward higher tau (less compute) for determinism + parsimony
    return max(tau for j, tau in scored if j <= best_J + 1e-12)


def _advantage(regret: Sequence[float], signal: Sequence[float], price: float
               ) -> Tuple[float, dict]:
    """min(J_retrieve, J_compute) − J_learned on heldout; tau learned on train."""
    train_idx = list(range(N_TRAIN))
    held_idx = list(range(N_TRAIN, N_STATES))
    tau = learn_tau(regret, signal, train_idx, price)
    j_learned = _J(regret, signal, held_idx, tau, price)
    j_retrieve = _J(regret, signal, held_idx, float("inf"), price)   # retrieve all
    j_compute = _J(regret, signal, held_idx, float("-inf"), price)   # compute all
    best_pure = min(j_retrieve, j_compute)
    n_compute = sum(1 for x in held_idx if signal[x] >= tau)
    meta = {"tau": round(tau, 3), "j_retrieve": round(j_retrieve, 4),
            "j_compute": round(j_compute, 4), "j_learned": round(j_learned, 4),
            "best_pure": round(best_pure, 4),
            "heldout_compute_frac": round(n_compute / len(held_idx), 3)}
    return best_pure - j_learned, meta


def _shuffle_signal(signal: Sequence[float], seed: int) -> List[float]:
    """Permute z across ALL pooled states, breaking the z<->regret coupling while
    preserving the marginal z-distribution."""
    perm = list(signal)
    Random(zlib.crc32(f"shuf|{seed}".encode())).shuffle(perm)
    return perm


# ---------------------------------------------------------------- conditions
def _make(name: str, kind: str) -> Condition:
    counter = {"i": 0}

    def run(_rng: Random) -> float:
        i = counter["i"]
        counter["i"] += 1
        seed = CONF_BASE_SEED + i
        if kind == "no_drift":
            regret, signal = build_universe(seed, drift_on=False)
            adv, meta = _advantage(regret, signal, PRICE)
        elif kind == "shuffled":
            regret, signal = build_universe(seed, drift_on=True)
            adv, meta = _advantage(regret, _shuffle_signal(signal, seed), PRICE)
        else:                                     # scheduler_advantage (PRIMARY)
            regret, signal = build_universe(seed, drift_on=True)
            adv, meta = _advantage(regret, signal, PRICE)
        RC_LOG.setdefault(name, []).append({"seed_index": i, "advantage": round(adv, 4), **meta})
        return adv

    return Condition(name, run, name)


def retrieve_compute() -> Tuple[List[Condition], str]:
    conditions = [
        _make("no_drift_null", "no_drift"),        # null: no drift -> advantage exactly 0
        _make("shuffled_signal", "shuffled"),      # discriminating control: signal ~0
        _make("scheduler_advantage", "primary"),   # PRIMARY: learned scheduler vs best pure
    ]
    return conditions, "scheduler_advantage"


REGISTRY_REAL = {"retrieve_compute": retrieve_compute}


# ---------------------------------------------------------------- smoke / pilot / report
if __name__ == "__main__":
    import json
    import os
    import sys
    import time

    t0 = time.time()

    if "--calibrate" in sys.argv:
        # PILOT: family 962000-962004 (DISJOINT from the 962500+ confirmatory family).
        # Sweep PRICE/SIGMA to find an honest operating point where the learned
        # scheduler beats the best pure baseline while both controls sit ~0, then
        # FREEZE. Reports per-seed so the bands are set from real dispersion.
        PILOT = list(range(962_000, 962_005))
        print("# pilot sweep (family 962000-962004) — advantage = best_pure - J_learned")
        for sigma_try in (0.10, 0.15, 0.25, 0.40):
            for price_try in (0.010, 0.015, 0.020, 0.030):
                # temporarily override module constants for the sweep
                g = globals()
                g["SIGMA"], g["PRICE"] = sigma_try, price_try
                prim, ctrl_shuf, ctrl_nod = [], [], []
                for s in PILOT:
                    reg, sig = build_universe(s, drift_on=True)
                    a_p, _ = _advantage(reg, sig, price_try)
                    a_s, _ = _advantage(reg, _shuffle_signal(sig, s), price_try)
                    reg0, sig0 = build_universe(s, drift_on=False)
                    a_n, _ = _advantage(reg0, sig0, price_try)
                    prim.append(a_p); ctrl_shuf.append(a_s); ctrl_nod.append(a_n)
                n = len(prim)
                mp = sum(prim) / n
                sp = (sum((x - mp) ** 2 for x in prim) / n) ** 0.5
                print(f" SIGMA={sigma_try:<5} PRICE={price_try:<6} "
                      f"primary={mp:+.4f}±{sp:.4f}  shuffled={sum(ctrl_shuf)/n:+.4f}  "
                      f"no_drift={sum(ctrl_nod)/n:+.4f}")
        print(f"total {time.time()-t0:.1f}s")

    elif "--report" in sys.argv:
        # Confirmatory run through the EXACT rsc.py path (validate -> run_spec ->
        # format_run), plus per-seed diagnostics the generic CLI does not print.
        _root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        sys.path.insert(0, _root)
        from spec_compiler.model import load_spec
        from spec_compiler.validator import validate, format_report
        from spec_compiler.harness import run_spec, format_run

        spec = load_spec(os.path.join(_root, "specs", "retrieve_compute.yaml"))
        rep = validate(spec)
        if not rep.ok:
            print(format_report(rep, title="retrieve_compute.yaml"))
            raise SystemExit(1)
        conditions, primary = retrieve_compute()
        result = run_spec(spec, conditions, primary=primary)
        print(format_run(result, spec, title="retrieve_compute",
                         provenance="[REAL run — cache-drift-contextual]"))
        print("\n# per-condition seed values")
        for c in result.conditions:
            print(f"  {c.name:<22}{['%.4f' % v for v in c.values]}")
        print("\n# per-seed log")
        print(json.dumps(RC_LOG, indent=1, ensure_ascii=False))
        print(f"\ntotal {time.time()-t0:.1f}s")

    else:
        # quick single-seed confirmatory-family check
        conditions, primary = retrieve_compute()
        for c in conditions:
            v = c.run(Random(0))
            print(f"{c.name:<22} advantage={v:+.4f}")
        print(json.dumps(RC_LOG, indent=1, ensure_ascii=False))
        print(f"total {time.time()-t0:.1f}s")
