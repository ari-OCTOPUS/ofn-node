"""
REAL experiment for specs/comparison_metacog_v2.yaml — H-OWN-02b.

DECLARED FOLLOW-UP to adr/ADR-010 (comparison-driven metacognition). v1
(`experiments/comparison_metacog.py`) verdicted INTEGRATE (+0.019) but its gate
never isolated the mechanism the architecture is NAMED for: the skill-gap
correction delta_hat. An out-of-verdict probe showed a delta_hat:=0
aligned-fusion variant already recovers ~+0.014 of the +0.019, leaving only
~+0.005 to the correction itself [FACT: ADR-010 §Confirmed caveats 1].
v1 is left UNTOUCHED (no retro-edit); v2 is a fresh preregistration on a fresh
disjoint seed family whose PRIMARY GATED metric IS the mechanism-specific
increment:

  delta_gain = brier_reduction(FULL mechanism, WITH delta_hat)
             - brier_reduction(ALIGNED fusion,  WITHOUT delta_hat)
             = err_aligned - err_full        (same universe, paired per seed)

i.e. the v2 baseline is NOT self-only shrinkage (v1's baseline) but the
strongest mechanism-light variant: fuse OTHER's difficulty-ALIGNED heldout
rate with NO skill-gap shift. Whatever survives that subtraction is what the
skill-gap correction ITSELF buys. FALSIFIABLE: delta_gain can be <= 0 — a
noisy or biased delta_hat shifts OTHER's logit in a wrong direction/magnitude
and HURTS calibration relative to no shift at all (v1's own probe showed the
whole gain REVERSES at theta_o=3/n_o=2). Given v1's probe (~+0.005) this may
honestly land DISCARD or OPTIMIZE; the point of v2 is the attribution, not a
foregone INTEGRATE.

Generative world: bit-identical REUSE of v1's Rasch/IRT universe — constants
and primitives are imported from `.comparison_metacog`, the RNG consumption
order is replicated exactly, and every universe is CROSS-CHECKED at runtime
against v1's `universe_result` (err_base / err_cmp / delta_hat must agree to
1e-12) so "same data, new gate" is enforced, not merely claimed.

Conditions (all paired on the identical universe per seed index):

  null_control          err_aligned - err_aligned = exactly 0 (same-vs-same
                        plumbing zero-point on the v2 baseline predictor).
  shuffled_delta_gain   discriminating control — identical machinery, but
                        delta_hat is re-estimated under an EXCHANGEABILITY
                        NULL: per train category the SELF/OTHER roles are
                        coin-flip swapped (N_S_TRAIN == N_O_TRAIN, so a swap
                        is an exact sign flip of that category's logit
                        difference). The null gap carries no skill information
                        (E[delta_hat_shuf] ~ 0, residual noise only), so the
                        increment over aligned fusion must be ~0 or slightly
                        NEGATIVE (any noisy nonzero shift is applied in an
                        arbitrary direction). If shuffled_delta_gain tracked
                        delta_gain, the "learned gap" would be doing nothing.
  aligned_gain          context, NOT gated — br(aligned fusion) over v1's
                        self-only baseline, the mechanism-light share of v1's
                        effect on this fresh family (reported for attribution
                        accounting; expected ~+0.014).
  delta_gain            PRIMARY — the mechanism-specific increment defined
                        above.

Seed discipline: pilot family 946000+ (n=10) was used ONLY to set the bands
and then FROZEN; the module default is the CONFIRMATORY family 946500+,
disjoint from the pilot and from every v1 family (980500+ pilot, 981000+
confirmatory) and every other experiment family in this repo.

Post-run precision note (ADR-020 — prose only, no gating field changed): the
gate decides on the MEAN over the 5 confirmatory universes. Two frozen-band
prose claims mixed the per-universe and mean scales and are restated in
ADR-020 s.Confirmed caveats: (a) "DISCARD is live" was argued from the pilot
PER-UNIVERSE min (+0.0027) against the mean gate (apples/oranges — on the
mean scale the kill line sat ~6 SE below the pilot mean, reachable via a
wrong-direction delta_hat, not sampling noise); (b) the +0.002 SESOI was
motivated by the PER-UNIVERSE null +2sigma (~+0.0027) while the mean-scale
null band is tighter (upper edge ~+0.0006), making the line conservative on
the scale that decides. Verdict [FACT, 2026-07-14]: OPTIMIZE, delta_gain
+0.005 (per-universe +0.0029..+0.0073, all positive; shuffled mean -0.001).

Determinism: everything derives from the per-seed-index universe seed
(V2_CONFIRM_BASE_SEED + i); all conditions see the identical universe for seed
index i (paired). The exchangeability swap uses a separate CRC-derived seed so
it never perturbs the world draw. No LLM anywhere.

SCOPE: C0/C1 functional calibration only. "Metacognition" here means a
capability ESTIMATE, not any phenomenal self-awareness. Forbidden
interpretation: introspective experience / qualia. Permitted: functional
self-performance estimation.
"""
from __future__ import annotations

import zlib
from random import Random
from typing import Dict, List, Tuple

from spec_compiler.harness import Condition

from .comparison_metacog import (
    C_HELDOUT, C_TRAIN, DIFF_SD, KAPPA, MCMP, N_O_HELD, N_O_TRAIN, N_S_HELD,
    N_S_TRAIN, THETA_O, THETA_S, _draws, _logit, _rate, _sigmoid,
    universe_result,
)

# ---------------------------------------------------------------- seed families (FROZEN after pilot 946000)
V2_PILOT_BASE_SEED = 946_000     # pilot family: bands set here, then FROZEN
V2_CONFIRM_BASE_SEED = 946_500   # CONFIRMATORY family (module default);
                                 # disjoint from pilot AND from v1's 980500/981000+

CMP2_LOG: dict = {}

# the exchangeability swap below is an exact sign flip ONLY because the two
# agents attempt the same number of train tasks per category.
assert N_S_TRAIN == N_O_TRAIN, "swap-null requires equal train attempt counts"


# ---------------------------------------------------------------- one universe
def universe_result_v2(seed: int) -> Dict[str, float]:
    """Fully deterministic. Redraws v1's universe bit-identically (RNG order
    replicated; cross-checked against v1's universe_result), then scores four
    predictors on heldout: self-only baseline, aligned fusion (delta_hat:=0),
    full mechanism (with delta_hat), and shuffled-delta (exchangeability-null
    delta_hat)."""
    rng = Random(seed)
    train_d = [rng.gauss(0.0, DIFF_SD) for _ in range(C_TRAIN)]
    held_d = [rng.gauss(0.0, DIFF_SD) for _ in range(C_HELDOUT)]

    # --- TRAIN: skill gap delta_hat + pooled self base rate (exactly as v1).
    deltas: List[float] = []
    self_train_wins = 0
    for d in train_d:
        ws = _draws(rng, _sigmoid(THETA_S - d), N_S_TRAIN)
        wo = _draws(rng, _sigmoid(THETA_O - d), N_O_TRAIN)
        self_train_wins += ws
        deltas.append(_logit(_rate(ws, N_S_TRAIN)) - _logit(_rate(wo, N_O_TRAIN)))
    delta_hat = sum(deltas) / len(deltas)
    p_bar = _rate(self_train_wins, C_TRAIN * N_S_TRAIN)

    # exchangeability-null gap: coin-flip swap of SELF/OTHER roles per train
    # category (equal n, so a swap == sign flip of that category's delta).
    swap_rng = Random(zlib.crc32(f"swapdelta|{seed}".encode()))
    delta_hat_shuf = sum(
        -dl if swap_rng.random() < 0.5 else dl for dl in deltas) / len(deltas)

    # --- HELDOUT: SELF's limited direct evidence + OTHER's observations
    #     (exactly as v1 — same rng, same order).
    p_true: List[float] = []
    self_wins: List[int] = []
    other_rate: List[float] = []
    for d in held_d:
        p_s = _sigmoid(THETA_S - d)
        p_true.append(p_s)
        self_wins.append(_draws(rng, p_s, N_S_HELD))
        other_rate.append(_rate(_draws(rng, _sigmoid(THETA_O - d), N_O_HELD), N_O_HELD))

    # the three comparison-derived per-category estimates (identical machinery,
    # only the shift differs):
    cmp_full = [_sigmoid(_logit(orr) + delta_hat) for orr in other_rate]
    cmp_aligned = [_sigmoid(_logit(orr)) for orr in other_rate]          # delta_hat := 0
    cmp_shufdelta = [_sigmoid(_logit(orr) + delta_hat_shuf) for orr in other_rate]

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
    e_full = calib_err(predict(cmp_full))
    e_align = calib_err(predict(cmp_aligned))
    e_shuf = calib_err(predict(cmp_shufdelta))

    # --- integrity cross-check: SAME world & estimator as v1, bit-identical.
    r1 = universe_result(seed)
    assert abs(r1["err_base"] - e_base) < 1e-12, "v2 diverged from v1 world (err_base)"
    assert abs(r1["err_cmp"] - e_full) < 1e-12, "v2 diverged from v1 world (err_cmp)"
    assert abs(r1["delta_hat"] - delta_hat) < 1e-12, "v2 diverged from v1 world (delta_hat)"

    return {
        "delta_hat": delta_hat, "delta_hat_shuf": delta_hat_shuf, "p_bar": p_bar,
        "err_base": e_base, "err_align": e_align, "err_full": e_full,
        "err_shufdelta": e_shuf,
        # PRIMARY: mechanism-specific increment of the skill-gap correction.
        "delta_gain": e_align - e_full,
        # discriminating control: same machinery, information-free gap.
        "shufdelta_gain": e_align - e_shuf,
        # context (not gated): the mechanism-light share, and v1's full gain.
        "aligned_gain": e_base - e_align,
        "full_gain": e_base - e_full,
    }


# ---------------------------------------------------------------- conditions
def _make(name: str, kind: str) -> Condition:
    counter = {"i": 0}

    def run(_rng: Random) -> float:
        i = counter["i"]
        counter["i"] += 1
        r = universe_result_v2(V2_CONFIRM_BASE_SEED + i)
        CMP2_LOG.setdefault(name, []).append(
            {"seed_index": i,
             "delta_hat": round(r["delta_hat"], 3),
             "delta_hat_shuf": round(r["delta_hat_shuf"], 3),
             "err_align": round(r["err_align"], 4), "err_full": round(r["err_full"], 4),
             "delta_gain": round(r["delta_gain"], 4),
             "shufdelta_gain": round(r["shufdelta_gain"], 4),
             "aligned_gain": round(r["aligned_gain"], 4)})
        if kind == "null":
            return r["err_align"] - r["err_align"]   # exactly 0 (same-vs-same)
        if kind == "shufdelta":
            return r["shufdelta_gain"]               # discriminating control
        if kind == "aligned":
            return r["aligned_gain"]                 # context, NOT gated
        return r["delta_gain"]                       # PRIMARY: delta_hat's own increment

    return Condition(name, run, name)


def comparison_metacog_v2() -> Tuple[List[Condition], str]:
    conditions = [
        _make("null_control", "null"),                # zero-point (aligned vs aligned)
        _make("shuffled_delta_gain", "shufdelta"),    # exchangeability-null gap (~0 / negative)
        _make("aligned_gain", "aligned"),             # mechanism-light share (context)
        _make("delta_gain", "delta"),                 # PRIMARY: skill-gap-correction increment
    ]
    return conditions, "delta_gain"


REGISTRY_REAL = {"comparison_metacog_v2": comparison_metacog_v2}


# ---------------------------------------------------------------- smoke / pilot
if __name__ == "__main__":
    import json
    import sys
    import time

    t0 = time.time()

    if "--pilot" in sys.argv:
        # DISJOINT pilot family (946000+); used ONLY to set honest bands, then
        # FROZEN. Reports mean/std of the primary + both controls, checks the
        # exact decomposition full_gain == aligned_gain + delta_gain, and
        # reproduces ADR-010's attribution probe on v1's confirmatory seeds.
        n = 10
        dg, sg, ag, fg = [], [], [], []
        for i in range(n):
            r = universe_result_v2(V2_PILOT_BASE_SEED + i)
            dg.append(r["delta_gain"])
            sg.append(r["shufdelta_gain"])
            ag.append(r["aligned_gain"])
            fg.append(r["full_gain"])
            # exact decomposition (both sides share err_base):
            assert abs(r["full_gain"] - (r["aligned_gain"] + r["delta_gain"])) < 1e-15

        def _ms(xs):
            m = sum(xs) / len(xs)
            v = sum((x - m) ** 2 for x in xs) / len(xs)
            return m, v ** 0.5

        md, sd = _ms(dg)
        ms_, ss_ = _ms(sg)
        ma, sa = _ms(ag)
        mf, sf = _ms(fg)
        print(f"PILOT family {V2_PILOT_BASE_SEED}..{V2_PILOT_BASE_SEED + n - 1}  (n={n})")
        print(f"  delta_gain          : mean {md:+.4f}  std {sd:.4f}  "
              f"min {min(dg):+.4f}  max {max(dg):+.4f}   <- PRIMARY")
        print(f"  shuffled_delta_gain : mean {ms_:+.4f}  std {ss_:.4f}  "
              f"min {min(sg):+.4f}  max {max(sg):+.4f}")
        print(f"  aligned_gain        : mean {ma:+.4f}  std {sa:.4f}   (context)")
        print(f"  full_gain (v1 metric): mean {mf:+.4f}  std {sf:.4f}   "
              f"(= aligned + delta, exact)")

        # integrity probe: reproduce ADR-010's attribution numbers on v1's
        # CONFIRMATORY seeds 981000-981004 (aligned ~ +0.014, delta ~ +0.005).
        pa, pd = [], []
        for i in range(5):
            r = universe_result_v2(981_000 + i)
            pa.append(r["aligned_gain"])
            pd.append(r["delta_gain"])
        print(f"  ADR-010 probe check (v1 seeds 981000-981004): "
              f"aligned {sum(pa) / 5:+.4f}  delta {sum(pd) / 5:+.4f}")
        print(f"total {time.time() - t0:.2f}s")

    else:
        r = universe_result_v2(V2_CONFIRM_BASE_SEED)
        print(json.dumps({k: round(v, 4) for k, v in r.items()}, indent=1))
        print(f"total {time.time() - t0:.2f}s")
