"""
REAL experiment for specs/comparison_metacog.yaml — H-OWN-02.

Hypothesis (comparison-driven metacognition): repeatedly comparing a PREDICTED
self-success-probability against an OBSERVED other-agent's outcomes improves an
agent's calibration of its OWN capability on heldout tasks. No LLM anywhere;
fully deterministic given the universe seed.

Generative model (a Rasch / item-response world — the smallest world in which
"is this task hard for everyone" is confounded with "am I bad at this"):
  * each task CATEGORY c has a latent difficulty d_c ~ Normal(0, DIFF_SD).
  * an agent with skill theta on a category of difficulty d succeeds with
    probability p = sigmoid(theta - d).
  * SELF has skill THETA_S; OTHER (the reference agent it compares against)
    has skill THETA_O and attempts the SAME tasks, so its outcomes carry the
    shared difficulty term d_c.

The estimation task: predict SELF's per-category success probability on HELDOUT
categories, where SELF has only N_S_HELD direct attempts (noisy) but OTHER has
N_O_HELD observed attempts. Calibration is scored by squared error of the
predicted probability against the true p (the reducible / reliability component
of the Brier score — the irreducible aleatoric term p(1-p) is identical across
predictors on the same categories and cancels in every reported DIFFERENCE, so
these gains ARE expected-Brier reductions; see __main__ for the empirical check).

Three predictors, all sharing the SAME direct self-experience + the same
base-rate prior (so the baseline is NOT a strawman — it already uses its own
limited direct evidence with proper Bayesian shrinkage):

  baseline (no_comparison)  posterior mean of SELF's N_S_HELD heldout draws
                            under a Beta prior of strength KAPPA centred on the
                            self base rate p_bar (estimated on TRAIN).
  comparison                baseline + MCMP pseudo-observations at the
                            comparison-derived estimate: take OTHER's observed
                            heldout logit and shift it by the estimated skill
                            gap delta_hat (learned on TRAIN, where SELF saw BOTH
                            its own and OTHER's outcomes on shared tasks; the
                            per-category difficulty cancels in the logit
                            difference). This is the metacognitive comparison:
                            "given how OTHER did here and how we differ in
                            general, how should I expect to do".
  shuffled (null control)   IDENTICAL machinery, but OTHER's heldout rates are
                            PERMUTED across categories before the shift — same
                            marginal values, difficulty alignment destroyed. If
                            the *content* of the comparison (not merely the act
                            of adding pseudo-observations) is what calibrates,
                            this collapses to ~0 gain (and can go negative).

Primary metric = brier_reduction = err_base - err_comparison on heldout, i.e.
the calibration-error reduction the comparison agent buys over the no-comparison
baseline. FALSIFIABLE: it can be <= 0 (biased skill-gap estimate, too-few OTHER
samples, or low difficulty variance all erase or reverse the gain).

Non-strawman controls (per ADR discipline):
  * shuffled_gain — discriminating control that isolates comparison CONTENT from
    the mere presence of the fusion mechanism (analogous to gridworld's
    oracle_no_taskid). Must be ~0.
  * null_control  — err_base - err_base = exactly 0 (plumbing zero-point).

Confirmed caveats (adversarial review, 2026-07-14 — recorded in adr/ADR-010):
  * MECHANISM ATTRIBUTION: shuffled_gain isolates comparison CONTENT (difficulty
    alignment), NOT the skill-gap term delta_hat. A delta_hat:=0 aligned-fusion
    variant (fuse OTHER's category-aligned heldout rate with no skill-gap shift)
    already recovers +0.014 of the +0.019 gain [FACT: probe, confirmatory seeds
    981000-981004]; the skill-gap correction itself contributes only ~+0.005, and
    no verdict-level condition isolates delta_hat. The mechanism is real (baseline
    exactly 0, shuffled negative) but is NOT wholly the skill-gap correction.
  * SAMPLE ASYMMETRY: OTHER has 5x SELF's heldout samples (N_O_HELD=15 vs
    N_S_HELD=3), which is part of why the social signal helps. The shuffled null
    holds this asymmetry FIXED and still goes negative (-0.032), so the gain is
    the comparison's difficulty-aligned content, not merely more observations.
  * DECISION n: the verdict is the mean over seeds=5 universes (evaluation.seeds),
    not 80 -- 80 is the heldout-category scoring set WITHIN each universe.

Determinism: everything derives from the per-seed-index universe seed
(COMPARISON_BASE_SEED + i), so all three conditions see the identical universe
for seed i (paired). The shuffle permutation uses a separate CRC-derived seed.
Confirmatory family 981000+ is disjoint from the pilot family (980500+), which
was used only to set the decision bands and then FROZEN.

SCOPE: C0/C1 functional calibration only. "Metacognition" here means a
capability ESTIMATE, not any phenomenal self-awareness. Forbidden
interpretation: introspective experience / qualia. Permitted: functional
self-performance estimation.
"""
from __future__ import annotations

import math
import zlib
from random import Random
from typing import Dict, List, Tuple

from spec_compiler.harness import Condition

# ---------------------------------------------------------------- constants (FROZEN after pilot 980500)
THETA_S = 0.0          # self skill (latent logit reference)
THETA_O = 0.7          # other skill: better than self, gap must be learnable
DIFF_SD = 1.2          # spread of category difficulty (creates the confound)
C_TRAIN = 60           # train categories (skill-gap + base-rate estimation)
C_HELDOUT = 80         # heldout categories (the calibration target)
N_S_TRAIN = 12         # self attempts per train category
N_O_TRAIN = 12         # other attempts per train category
N_S_HELD = 3           # self's LIMITED direct heldout experience (noisy)
N_O_HELD = 15          # other's observed heldout attempts (the social signal)
KAPPA = 4.0            # Beta-prior pseudo-count toward the self base rate
MCMP = 8.0             # pseudo-count weight of the comparison-derived estimate

COMPARISON_BASE_SEED = 981_000   # CONFIRMATORY family (disjoint from all others);
                                 # pilot/sweep used 980_500 (see spec + self-check).

CMP_LOG: dict = {}


# ---------------------------------------------------------------- numerics
def _sigmoid(x: float) -> float:
    if x >= 0.0:
        return 1.0 / (1.0 + math.exp(-x))
    z = math.exp(x)
    return z / (1.0 + z)


def _logit(p: float) -> float:
    p = min(1.0 - 1e-9, max(1e-9, p))
    return math.log(p / (1.0 - p))


def _rate(wins: int, n: int) -> float:
    """add-half smoothed empirical rate (keeps logits finite)."""
    return (wins + 0.5) / (n + 1.0)


def _draws(rng: Random, p: float, n: int) -> int:
    return sum(1 for _ in range(n) if rng.random() < p)


# ---------------------------------------------------------------- one universe
def universe_result(seed: int) -> Dict[str, float]:
    """Fully deterministic. Draw train + heldout outcomes, estimate the skill
    gap, and score baseline / comparison / shuffled calibration on heldout."""
    rng = Random(seed)
    train_d = [rng.gauss(0.0, DIFF_SD) for _ in range(C_TRAIN)]
    held_d = [rng.gauss(0.0, DIFF_SD) for _ in range(C_HELDOUT)]

    # --- TRAIN: estimate skill gap delta_hat (difficulty cancels in the logit
    #     difference) and the pooled self base rate p_bar.
    deltas: List[float] = []
    self_train_wins = 0
    for d in train_d:
        ws = _draws(rng, _sigmoid(THETA_S - d), N_S_TRAIN)
        wo = _draws(rng, _sigmoid(THETA_O - d), N_O_TRAIN)
        self_train_wins += ws
        deltas.append(_logit(_rate(ws, N_S_TRAIN)) - _logit(_rate(wo, N_O_TRAIN)))
    delta_hat = sum(deltas) / len(deltas)
    p_bar = _rate(self_train_wins, C_TRAIN * N_S_TRAIN)

    # --- HELDOUT: draw SELF's limited direct evidence + OTHER's observations.
    p_true: List[float] = []
    self_wins: List[int] = []
    other_rate: List[float] = []
    for d in held_d:
        p_s = _sigmoid(THETA_S - d)
        p_true.append(p_s)
        self_wins.append(_draws(rng, p_s, N_S_HELD))
        other_rate.append(_rate(_draws(rng, _sigmoid(THETA_O - d), N_O_HELD), N_O_HELD))

    # comparison-derived per-category self estimate: OTHER's logit + skill gap.
    cmp_aligned = [_sigmoid(_logit(orr) + delta_hat) for orr in other_rate]
    # shuffled control: same values, difficulty alignment destroyed.
    perm = list(range(C_HELDOUT))
    Random(zlib.crc32(f"shuf|{seed}".encode())).shuffle(perm)
    cmp_shuf = [_sigmoid(_logit(other_rate[perm[c]]) + delta_hat) for c in range(C_HELDOUT)]

    def predict(cmp_vals) -> List[float]:
        preds = []
        for c in range(C_HELDOUT):
            num = self_wins[c] + KAPPA * p_bar
            den = N_S_HELD + KAPPA
            if cmp_vals is not None:
                num += MCMP * cmp_vals[c]
                den += MCMP
            preds.append(num / den)
        return preds

    def calib_err(preds) -> float:
        return sum((preds[c] - p_true[c]) ** 2 for c in range(C_HELDOUT)) / C_HELDOUT

    e_base = calib_err(predict(None))
    e_cmp = calib_err(predict(cmp_aligned))
    e_shuf = calib_err(predict(cmp_shuf))
    return {
        "delta_hat": delta_hat, "p_bar": p_bar,
        "err_base": e_base, "err_cmp": e_cmp, "err_shuf": e_shuf,
        "gain_cmp": e_base - e_cmp, "gain_shuf": e_base - e_shuf,
    }


# ---------------------------------------------------------------- conditions
def _make(name: str, kind: str) -> Condition:
    counter = {"i": 0}

    def run(_rng: Random) -> float:
        i = counter["i"]
        counter["i"] += 1
        r = universe_result(COMPARISON_BASE_SEED + i)
        CMP_LOG.setdefault(name, []).append(
            {"seed_index": i,
             "delta_hat": round(r["delta_hat"], 3), "p_bar": round(r["p_bar"], 3),
             "err_base": round(r["err_base"], 4), "err_cmp": round(r["err_cmp"], 4),
             "err_shuf": round(r["err_shuf"], 4),
             "gain_cmp": round(r["gain_cmp"], 4), "gain_shuf": round(r["gain_shuf"], 4)})
        if kind == "null":
            return r["err_base"] - r["err_base"]     # exactly 0 (plumbing zero-point)
        if kind == "shuffled":
            return r["gain_shuf"]                     # discriminating null control
        return r["gain_cmp"]                          # PRIMARY: comparison calibration gain

    return Condition(name, run, name)


def comparison_metacog() -> Tuple[List[Condition], str]:
    conditions = [
        _make("null_control", "null"),          # zero-point (base vs base)
        _make("shuffled_gain", "shuffled"),     # discriminating control (~0)
        _make("comparison_gain", "comparison"),  # PRIMARY: calibration-error reduction
    ]
    return conditions, "comparison_gain"


REGISTRY_REAL = {"comparison_metacog": comparison_metacog}


# ---------------------------------------------------------------- smoke / pilot
if __name__ == "__main__":
    import json
    import sys
    import time

    t0 = time.time()

    if "--pilot" in sys.argv:
        # DISJOINT pilot family (980500+); used only to set honest bands, then
        # parameters FROZEN. Reports mean/std of both gains + a discriminating
        # empirical-Brier cross-check on a single universe.
        PILOT_BASE = 980_500
        n = 10
        gc, gs = [], []
        for i in range(n):
            r = universe_result(PILOT_BASE + i)
            gc.append(r["gain_cmp"])
            gs.append(r["gain_shuf"])

        def _ms(xs):
            m = sum(xs) / len(xs)
            v = sum((x - m) ** 2 for x in xs) / len(xs)
            return m, v ** 0.5
        mc, sc = _ms(gc)
        ms, ss = _ms(gs)
        print(f"PILOT family {PILOT_BASE}..{PILOT_BASE + n - 1}  (n={n})")
        print(f"  comparison_gain : mean {mc:+.4f}  std {sc:.4f}  "
              f"min {min(gc):+.4f}  max {max(gc):+.4f}")
        print(f"  shuffled_gain   : mean {ms:+.4f}  std {ss:.4f}  "
              f"min {min(gs):+.4f}  max {max(gs):+.4f}")

        # empirical-Brier cross-check on one universe: confirm gain_cmp (analytic
        # reducible-MSE reduction) matches the Brier reduction on fresh outcomes.
        seed = PILOT_BASE
        rng = Random(seed)
        train_d = [rng.gauss(0.0, DIFF_SD) for _ in range(C_TRAIN)]
        held_d = [rng.gauss(0.0, DIFF_SD) for _ in range(C_HELDOUT)]
        for d in train_d:                       # advance rng exactly as universe_result
            _draws(rng, _sigmoid(THETA_S - d), N_S_TRAIN)
            _draws(rng, _sigmoid(THETA_O - d), N_O_TRAIN)
        r = universe_result(seed)
        # rebuild predictions to score against fresh eval outcomes
        rng2 = Random(seed)
        _t = [rng2.gauss(0.0, DIFF_SD) for _ in range(C_TRAIN)]
        _h = [rng2.gauss(0.0, DIFF_SD) for _ in range(C_HELDOUT)]
        eval_rng = Random(zlib.crc32(f"eval|{seed}".encode()))
        n_eval = 400
        bb = bc = 0.0
        # reconstruct predictions deterministically
        # (re-run the estimator body compactly)
        rng3 = Random(seed)
        td = [rng3.gauss(0.0, DIFF_SD) for _ in range(C_TRAIN)]
        hd = [rng3.gauss(0.0, DIFF_SD) for _ in range(C_HELDOUT)]
        deltas = []
        stw = 0
        for d in td:
            ws = _draws(rng3, _sigmoid(THETA_S - d), N_S_TRAIN)
            wo = _draws(rng3, _sigmoid(THETA_O - d), N_O_TRAIN)
            stw += ws
            deltas.append(_logit(_rate(ws, N_S_TRAIN)) - _logit(_rate(wo, N_O_TRAIN)))
        dh = sum(deltas) / len(deltas)
        pb = _rate(stw, C_TRAIN * N_S_TRAIN)
        sw, orr, ptrue = [], [], []
        for d in hd:
            ps = _sigmoid(THETA_S - d)
            ptrue.append(ps)
            sw.append(_draws(rng3, ps, N_S_HELD))
            orr.append(_rate(_draws(rng3, _sigmoid(THETA_O - d), N_O_HELD), N_O_HELD))
        cmpv = [_sigmoid(_logit(x) + dh) for x in orr]
        for c in range(C_HELDOUT):
            pbase = (sw[c] + KAPPA * pb) / (N_S_HELD + KAPPA)
            pcmp = (sw[c] + KAPPA * pb + MCMP * cmpv[c]) / (N_S_HELD + KAPPA + MCMP)
            for _ in range(n_eval):
                y = 1.0 if eval_rng.random() < ptrue[c] else 0.0
                bb += (pbase - y) ** 2
                bc += (pcmp - y) ** 2
        denom = C_HELDOUT * n_eval
        print(f"  empirical Brier  : base {bb / denom:.4f}  cmp {bc / denom:.4f}  "
              f"reduction {(bb - bc) / denom:+.4f}   (analytic gain_cmp {r['gain_cmp']:+.4f})")
        print(f"total {time.time() - t0:.2f}s")

    else:
        r = universe_result(COMPARISON_BASE_SEED)
        print(json.dumps({k: round(v, 4) for k, v in r.items()}, indent=1))
        print(f"total {time.time() - t0:.2f}s")
