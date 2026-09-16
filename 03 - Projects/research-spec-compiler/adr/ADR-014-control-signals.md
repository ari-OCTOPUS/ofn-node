# ADR-014 — Regret as a shift-invariant control signal (a defined math signal, NOT an emotion)

- **Status:** Closed — machine verdict **INTEGRATE** · effect strong and clean on a synthetic environment built to exhibit it
- **Date:** 2026-07-14
- **Spec:** `specs/control_signals.yaml` (H-OWN-08 / EXP-008, PASS 6/6) · `experiments/control_signals.py` · dataset `contextual-choice-ood`
- **Decision rule (GO/NO-GO):** advantage_ood < 0.06 → DISCARD · [0.06, 0.20) → OPTIMIZE · ≥ 0.20 → INTEGRATE — the gate reads the **raw** `regret_advantage_ood`.

## Context — what the raw files claimed

The corpus proposes treating a *social-emotion analogue* as a mathematically
defined **control signal**, not a feeling. This experiment picks the cleanest
such analogue — **regret**, defined strictly as

    regret(a) = value(achieved a) − value(best alternative b ≠ a)

a scalar credit signal with **no valence and no phenomenology**. The falsifiable
claim: an agent that assigns credit with regret makes better decisions than an
identical agent using raw reward, **specifically under distribution shift**,
because regret is invariant to an additive shift in the reward level whereas raw
reward is not.

## Decision — what it tests + mechanism

A deterministic, no-LLM contextual multi-armed choice task
[FACT: source constants]: `C=40` contexts, `A=4` arms, best-arm gap `0.12`,
`T=3000` online pulls, learning rate `0.30`, softmax temp `0.50`, obs noise
`0.20`. Each context `x` has zero-centred base qualities with a unique best arm
`a*(x)`. Two agents are **identical in every respect** — same env, learner,
alpha, temperature, exploration schedule, **full-information** feedback, and
greedy-eval — except the scalar credit rule applied to the chosen arm:

- `reward_only`: `pref[x][a] += α · value(a)` (raw reward)
- `regret_sig`: `pref[x][a] += α · (value(a) − max_{b≠a} value(b))` (regret)

**OOD shift:** every arm in a context gets the *same* zero-mean additive offset
`off(x)` (scale `1.5`). Because it is common to all arms, `off(x)` does **not**
change `a*(x)` — the decision problem is unchanged — but it contaminates
raw-reward credit (positive-offset contexts reinforce whatever arm was tried
first → lock-in). Regret subtracts a same-context counterfactual, cancelling
`off(x)` exactly, so it is immune. Metric = decision quality = fraction of
contexts whose final greedy arm equals `a*(x)`; primary =
`regret_advantage_ood` = quality(regret) − quality(reward) under OOD.

**Two discriminating controls** keep the primary non-strawman:
`regret_advantage_indist` (same advantage with the shift OFF — should be ~0, so
`reward_only` is a fair baseline, not a globally broken agent) and
`shuffled_null_ood` (regret from a MISMATCHED context's counterfactual — the
cancellation is destroyed, so ~0/negative, proving it is the true counterfactual
structure that helps, not generic subtraction).

## Confirmed caveats (adversarial review)

1. **The gate reads RAW `advantage_ood`, not the strict shift-specific premium.**
   The premium `advantage_ood − advantage_indist` is the theoretically pure
   quantity (it nets out any residual regret edge that exists even without a
   shift). The failure_condition and decision bands operate on **raw ood**
   instead. Unlike ADR-008 — where a raw metric hid a vacuous gate — this is
   acceptable here **only because the premium is large and clean**: raw-ood
   `+0.355` vs in-distribution `+0.070` vs shuffled `−0.135`, with **all 5 ood
   seeds positive** [FACT: run log]. The premium itself is `+0.285` mean
   [FACT: run log], well clear of the 0.20 INTEGRATE band even after netting out
   the in-distribution edge. **Disclosure:** the gated quantity is raw-ood
   (calibrated to sit just above the ~in-distribution control), NOT the premium.
2. **The threshold note was imprecise.** The old note claimed 0.06 "= the
   in-distribution control level." The measured in-distribution advantage is
   `+0.070` [FACT: run log] — slightly **above** 0.06. So 0.06 is a floor *near*
   that control, not exactly equal to it. Fixed in `failure_condition.note`
   (op/threshold unchanged).
3. **The shuffled control is noisy and can go strongly negative** (`−0.135` mean,
   std `0.187`, one seed `−0.475`) [FACT: run log]. This is expected, not a
   defect: destroying the counterfactual match doesn't merely zero the signal, it
   can actively mislead — which is exactly the point (the *structure* matters).
4. **Scope firewall (loud):** regret here is a DEFINED MATHEMATICAL QUANTITY (a
   difference of values). It is **explicitly NOT** an emotion/affect. Forbidden
   reading: regret-as-affect, valence, phenomenal "disappointment." Permitted:
   regret as a functional control/credit signal.
5. **Declared architectural precondition:** the regret signal **requires
   full-info counterfactuals** — it must observe the best-alternative value each
   step. Under bandit-only feedback the signal is unavailable and this advantage
   **cannot be realized** (recorded in `architecture.tradeoff`).

## Scope guard

- **C0–C3 functional decision control only.** The C0⇏C4 (phenomenal/qualia)
  line is never crossed; no claim of sentience, feeling, or subjective valence.
- **Environment class:** a single synthetic contextual-bandit family
  purpose-built to exhibit additive-shift invariance. The verdict is scoped to
  this class; external validity to messier / non-additive shifts and to
  bandit-only settings is **unestablished**.
- **Provenance discipline:** pilot family `985000–985004` was used to freeze
  parameters (advantage_ood ≈ `+0.33`, shuffled ≈ `−0.12`, indist ≈ `+0.06`
  [FACT: pilot log 2026-07-14]); the confirmatory run uses the **disjoint** fresh
  family `985500–985504`.

## Verdict

**INTEGRATE** — `python rsc.py run control_signals`, 5 seeds (985500–985504),
2026-07-14. All numbers [FACT: run log]:

| condition | mean | std | per-seed | role |
|---|---|---|---|---|
| **regret_advantage_ood** (primary) | **0.355** | 0.084 | 0.350 / 0.400 / 0.200 / 0.375 / 0.450 | gated |
| regret_advantage_indist | 0.070 | 0.056 | 0.050 / 0.075 / 0.025 / 0.025 / 0.175 | control (~0) |
| shuffled_null_ood | −0.135 | 0.187 | −0.125 / 0.050 / −0.475 / −0.150 / 0.025 | control (~0/neg) |
| premium (ood − indist) | 0.285 | — | 0.300 / 0.325 / 0.175 / 0.350 / 0.275 | reported |

- `regret_advantage_ood = 0.355 ≥ 0.20` → **INTEGRATE**; failure_condition
  `advantage_ood < 0.06` **not triggered** [FACT: run log].
- **Honest reading:** the mechanism is real and cleanly demonstrated. The signal
  cancels the additive OOD offset **by construction**, all 5 seeds are positive,
  the in-distribution control confirms raw-reward is a fair baseline (its residual
  edge is only `+0.070`), and the shuffled control confirms it is the *true*
  counterfactual structure — not generic subtraction — that carries the effect.
  The **shift-specific premium is `+0.285`**, still far above the INTEGRATE band.
- **The honest discount:** this is a synthetic environment built to display the
  exact invariance regret has by definition; the `0.355` measures how favorable
  the setup is as much as how good the signal is. INTEGRATE is warranted for the
  kernel's control layer **where full-info counterfactuals exist**, but the effect
  size should not be read as a claim about messy real tasks or bandit-only
  regimes.

## Consequence

INTEGRATE licenses adopting regret as a first-class **credit/control signal** in
the kernel's decision layer, gated on the availability of full-info
counterfactuals (a hard precondition). It remains a defined scalar control input;
nothing here authorizes any affect/valence interpretation, and the C0–C3 scope is
unchanged.
