"""
REAL experiment for specs/control_signals.yaml — H-OWN-08 / EXP-008.

Tests the raw files' claim that a SOCIAL-EMOTION ANALOGUE used as a mathematically
defined CONTROL SIGNAL (NOT a feeling) improves decisions. The analogue here is
REGRET, defined strictly as a scalar:

    regret(a_t) = value(a_t) - max_{b != a_t} value(b)          [O F* / N control-signal note]

i.e. the difference between the value the agent achieved and the value of the
best *alternative* it could have taken. This is a control input, not an affect:
no valence, no phenomenology (SCOPE below).

Hypothesis (H-OWN-08): an agent that assigns credit with the REGRET signal makes
better decisions than an agent that assigns credit with the RAW REWARD signal,
SPECIFICALLY under distribution shift — because regret (achieved minus
best-alternative) is INVARIANT to an additive shift in the reward level, whereas
raw reward is not.

Environment (new, deterministic, no LLM): a contextual multi-armed choice task.
C=40 contexts, A=4 arms. Each context x has zero-centred base qualities
base(x,·) with a unique best arm a*(x) separated by a gap. The agent learns
per-context arm preferences online over T pulls with softmax exploration and
FULL-INFORMATION feedback (it observes every arm's value each pull — this is
identical for both agents, so information is NOT the manipulation). The ONLY
difference between the two agents is the scalar credit signal applied to the
chosen arm:
  reward_only  pref[x][a_t] += alpha * value(a_t)                    (raw reward)
  regret_sig   pref[x][a_t] += alpha * (value(a_t) - max_{b!=a_t} value(b))

Distribution shift (OOD): each context gets a large, ZERO-MEAN additive
level offset off(x) applied to ALL its arms. Because it is common to every arm
in the context, off(x) does NOT change a*(x) — the decision problem is
unchanged — but it contaminates raw-reward credit assignment (positive-offset
contexts reinforce whatever arm was tried first -> lock-in on the wrong arm).
The regret signal cancels off(x) exactly (it subtracts a same-context
counterfactual), so it is immune.

Controls (this is what makes the primary non-strawman and non-trivial):
  regret_advantage_indist   the SAME regret-vs-reward advantage with NO shift
                            (off_scale=0). If reward_only is only broken by the
                            specific shift, this is ~0 -> reward_only is a fair
                            baseline, not a globally broken strawman.
  shuffled_null_ood         regret computed from SHUFFLED counterfactuals: the
                            best-alternative is taken from a MISMATCHED context
                            (its own zero-mean offset), so the cancellation is
                            destroyed and the signal carries no shift-specific
                            information. Advantage ~0 -> it is the TRUE
                            counterfactual structure, not generic subtraction,
                            that helps.
Both share the identical env, learner, alpha, temperature, exploration schedule,
full-info feedback and greedy-eval procedure; the credit signal is the sole IV.

GATED vs REPORTED (keep straight): the preregistered, machine-gated quantity is
`regret_advantage_ood` (spec failure_condition + decision_rule operate on it).
The OOD-SPECIFICITY premium (advantage_ood - advantage_indist) and the shuffled
null are REPORTED discriminating controls; the verdict does not read them.

Primary metric = regret_advantage_ood = decision_quality(regret) −
decision_quality(reward) under OOD, where decision_quality = fraction of
contexts whose final greedy arm equals a*(x). Falsifiable: the advantage can be
<= 0 (small offset, or heavy exploration, makes reward_only fine and the signal
adds nothing). Pilot (family 985000-985004, 5 seeds) gave advantage_ood ≈
+0.33 with shuffled ≈ −0.12 and in-distribution ≈ +0.06; parameters were then
FROZEN and the confirmatory run uses a DISJOINT seed family (985500+). Fully
deterministic given the universe seeds.

SCOPE: C0-C3 in the file's ladder (functional decision control). The signal is a
DEFINED MATHEMATICAL QUANTITY (a difference of values), explicitly NOT an
emotion/feeling. Forbidden interpretation: regret-as-affect, valence, phenomenal
"disappointment". Permitted: regret as a functional control/credit signal.
"""
from __future__ import annotations

import math
import zlib
from random import Random
from typing import Dict, List, Sequence, Tuple

from spec_compiler.harness import Condition

# ---------------------------------------------------------------- constants (FROZEN)
C_CONTEXTS = 40
A_ARMS = 4
GAP = 0.12                 # min separation of best arm from 2nd best per context
T_PULLS = 3000             # online pulls per agent run
ALPHA = 0.30               # preference learning rate
TEMP = 0.50                # softmax exploration temperature
NOISE = 0.20               # per-pull Gaussian observation noise (both agents)
OFF_SCALE = 1.5            # OOD additive level-offset magnitude (zero-mean)
CONF_BASE_SEED = 985_500   # CONFIRMATORY family (disjoint); pilot used 985000-985007
CS_LOG: dict = {}


# ---------------------------------------------------------------- environment
def build_universe(seed: int) -> Tuple[List[List[float]], List[int], List[float]]:
    """Deterministic contextual-choice universe. Returns (base, astar, offset).
    base[x][a] zero-centred per context with a clear best; offset[x] zero-mean
    across contexts (the OOD level shift, scaled by OFF_SCALE at run time)."""
    rng = Random(seed)
    base = [[rng.uniform(-0.5, 0.5) for _ in range(A_ARMS)] for _ in range(C_CONTEXTS)]
    astar: List[int] = []
    for x in range(C_CONTEXTS):
        a = max(range(A_ARMS), key=lambda i: base[x][i])
        others = sorted(base[x][i] for i in range(A_ARMS) if i != a)
        base[x][a] = max(base[x][a], others[-1] + GAP)   # unambiguous best
        mu = sum(base[x]) / A_ARMS                        # zero-centre the context
        for i in range(A_ARMS):
            base[x][i] -= mu
        astar.append(max(range(A_ARMS), key=lambda i: base[x][i]))
    offset = [rng.uniform(-1.0, 1.0) for _ in range(C_CONTEXTS)]
    return base, astar, offset


# ---------------------------------------------------------------- online learner
def run_agent(seed: int, base: Sequence[Sequence[float]], astar: Sequence[int],
              offset: Sequence[float], off_scale: float, signal: str) -> float:
    """Online contextual-bandit learner with softmax exploration + full-info
    feedback. `signal` selects the credit rule for the chosen arm:
      'reward'   -> value(a_t)                       (raw reward)
      'regret'   -> value(a_t) - max_{b!=a_t} value(b)   (true regret)
      'shuffled' -> value(a_t) - max_{b!=a_t} value_mismatch(b)  (shuffled null)
    Returns decision quality = fraction of contexts whose final greedy arm is
    a*(x). Fully deterministic given `seed` (CRC-seeded internal RNG)."""
    rng = Random(zlib.crc32(f"{signal}|{off_scale}|{seed}".encode()))
    pref = [[0.0] * A_ARMS for _ in range(C_CONTEXTS)]

    def pick(x: int) -> int:
        m = max(pref[x])
        ws = [math.exp((pref[x][a] - m) / TEMP) for a in range(A_ARMS)]
        z = sum(ws)
        r = rng.random() * z
        c = 0.0
        for a in range(A_ARMS):
            c += ws[a]
            if r < c:
                return a
        return A_ARMS - 1

    for _ in range(T_PULLS):
        x = rng.randrange(C_CONTEXTS)
        a = pick(x)
        off = off_scale * offset[x]
        val = [base[x][b] + off + rng.gauss(0.0, NOISE) for b in range(A_ARMS)]
        if signal == "reward":
            g = val[a]
        elif signal == "regret":
            g = val[a] - max(val[b] for b in range(A_ARMS) if b != a)
        else:  # shuffled: best-alternative from a MISMATCHED context
            xp = rng.randrange(C_CONTEXTS)
            valp = [base[xp][b] + off_scale * offset[xp] + rng.gauss(0.0, NOISE)
                    for b in range(A_ARMS)]
            g = val[a] - max(valp[b] for b in range(A_ARMS) if b != a)
        pref[x][a] += ALPHA * g

    correct = sum(1 for x in range(C_CONTEXTS)
                  if max(range(A_ARMS), key=lambda i: pref[x][i]) == astar[x])
    return correct / C_CONTEXTS


# ---------------------------------------------------------------- conditions
def _make(name: str, kind: str) -> Condition:
    counter = {"i": 0}

    def run(_rng: Random) -> float:
        i = counter["i"]
        counter["i"] += 1
        seed = CONF_BASE_SEED + i
        base, astar, offset = build_universe(seed)
        # quality under OOD (offset on) and in-distribution (offset off)
        q_reward_ood = run_agent(seed, base, astar, offset, OFF_SCALE, "reward")
        q_regret_ood = run_agent(seed, base, astar, offset, OFF_SCALE, "regret")
        q_shuf_ood = run_agent(seed, base, astar, offset, OFF_SCALE, "shuffled")
        q_reward_ind = run_agent(seed, base, astar, offset, 0.0, "reward")
        q_regret_ind = run_agent(seed, base, astar, offset, 0.0, "regret")
        adv_ood = q_regret_ood - q_reward_ood
        adv_ind = q_regret_ind - q_reward_ind
        adv_shuf = q_shuf_ood - q_reward_ood
        CS_LOG.setdefault(name, []).append(
            {"seed_index": i,
             "reward_ood": round(q_reward_ood, 3), "regret_ood": round(q_regret_ood, 3),
             "shuffled_ood": round(q_shuf_ood, 3),
             "reward_indist": round(q_reward_ind, 3), "regret_indist": round(q_regret_ind, 3),
             "advantage_ood": round(adv_ood, 3), "advantage_indist": round(adv_ind, 3),
             "advantage_shuffled": round(adv_shuf, 3),
             "premium": round(adv_ood - adv_ind, 3)})
        if kind == "shuffled_null":
            return adv_shuf            # control: shuffled counterfactuals (~0)
        if kind == "indist":
            return adv_ind             # control: advantage without the shift (~0)
        return adv_ood                 # PRIMARY: regret advantage under OOD

    return Condition(name, run, name)


def control_signals() -> Tuple[List[Condition], str]:
    conditions = [
        _make("shuffled_null_ood", "shuffled_null"),        # control: ~0 (shuffled cf)
        _make("regret_advantage_indist", "indist"),         # control: ~0 (no shift)
        _make("regret_advantage_ood", "ood"),               # PRIMARY: regret adv under OOD
    ]
    return conditions, "regret_advantage_ood"


REGISTRY_REAL = {"control_signals": control_signals}


# ---------------------------------------------------------------- smoke / report
if __name__ == "__main__":
    import json
    import os
    import sys
    import time
    t0 = time.time()

    if "--report" in sys.argv:
        # Confirmatory run through the exact same path as `rsc.py run`.
        _root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        sys.path.insert(0, _root)
        from spec_compiler.model import load_spec
        from spec_compiler.validator import validate, format_report
        from spec_compiler.harness import run_spec, format_run

        spec = load_spec(os.path.join(_root, "specs", "control_signals.yaml"))
        rep = validate(spec)
        if not rep.ok:
            print(format_report(rep, title="control_signals.yaml"))
            raise SystemExit(1)
        conditions, primary = control_signals()
        result = run_spec(spec, conditions, primary=primary)
        print(format_run(result, spec, title="control_signals",
                         provenance="[REAL run — contextual-choice-ood]"))
        print("\n# per-condition seed values")
        for c in result.conditions:
            print(f"  {c.name:<26}{['%.3f' % v for v in c.values]}")
        print("\n# per-universe log")
        print(json.dumps(CS_LOG, indent=1, ensure_ascii=False))
        print(f"\ntotal {time.time()-t0:.1f}s")
    else:
        # PILOT smoke on the pilot family (985000-985004), disjoint from confirmatory.
        advs, shufs, inds = [], [], []
        for s in range(985_000, 985_005):
            base, astar, offset = build_universe(s)
            ro = run_agent(s, base, astar, offset, OFF_SCALE, "reward")
            rg = run_agent(s, base, astar, offset, OFF_SCALE, "regret")
            sh = run_agent(s, base, astar, offset, OFF_SCALE, "shuffled")
            ri = run_agent(s, base, astar, offset, 0.0, "reward")
            gi = run_agent(s, base, astar, offset, 0.0, "regret")
            advs.append(rg - ro); shufs.append(sh - ro); inds.append(gi - ri)
        n = len(advs); ma = sum(advs) / n
        sd = (sum((x - ma) ** 2 for x in advs) / n) ** 0.5
        print(json.dumps({
            "advantage_ood_mean": round(ma, 3), "advantage_ood_std": round(sd, 3),
            "advantage_shuffled_mean": round(sum(shufs) / n, 3),
            "advantage_indist_mean": round(sum(inds) / n, 3),
            "per_universe_adv_ood": [round(x, 3) for x in advs],
        }, indent=1))
        print(f"total {time.time()-t0:.1f}s")
