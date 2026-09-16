# ADR-010 — Comparison-driven metacognition: social comparison as a self-calibration signal

- **Status:** Closed — machine verdict **INTEGRATE** on preregistered bands; recorded with an honest mechanism-attribution caveat (see §Confirmed caveats)
- **Date:** 2026-07-14
- **Spec:** `specs/comparison_metacog.yaml` (H-OWN-02, PASS 6/6) · `experiments/comparison_metacog.py` · pilot family 980500 (frozen) → confirmatory family 981000+
- **Decision rule (GO/NO-GO):** brier_reduction < 0.005 → DISCARD · [0.005, 0.015) → OPTIMIZE · ≥ 0.015 → INTEGRATE. Falsifier: `brier_reduction < 0.005` rejects H-OWN-02. [FACT: spec `decision_rule` + `failure_condition`]

## Context

Does an agent calibrate its OWN capability better by watching a *reference agent* solve the same tasks? The confound that makes this non-trivial is the one every self-model faces: on a heldout category, a low observed success rate can mean "this task is hard for everyone" (difficulty) or "I am bad at this" (low skill). The smallest world that contains that confound is a Rasch / item-response family — `p_success = sigmoid(skill − difficulty)` — where the shared difficulty term `d_c` is exactly what a second agent's outcomes on the same tasks can help cancel.

The baseline is deliberately not a strawman: it already uses SELF's own limited direct heldout evidence (`N_S_HELD = 3` noisy attempts per category) under a Beta-shrunk posterior toward a train-estimated self base rate [FACT: `experiments/comparison_metacog.py` constants]. The question is whether *adding the social-comparison term* buys calibration over that.

Parameters were set on a disjoint pilot family (980500) and then FROZEN; the confirmatory run uses a fresh disjoint family (981000+). No LLM anywhere; fully deterministic given the universe seed. [FACT: spec header + experiment constants]

## Decision — what it tests + mechanism

Three predictors share the identical direct self-evidence and the same base-rate prior; only the comparison term differs:

- **baseline (no_comparison):** posterior mean of SELF's `N_S_HELD = 3` heldout draws under a Beta prior (strength `KAPPA = 4`) centred on the self base rate `p_bar`.
- **comparison (primary):** baseline + `MCMP = 8` pseudo-observations at the comparison-derived estimate — take OTHER's observed heldout logit and shift it by an estimated skill gap `delta_hat` learned on TRAIN (where the per-category difficulty cancels in the logit difference, since SELF saw both its own and OTHER's outcomes on shared tasks). OTHER has `N_O_HELD = 15` observed heldout attempts, 5× SELF's 3.
- **shuffled (discriminating control):** identical machinery, but OTHER's heldout rates are PERMUTED across categories before the shift — same marginal values, difficulty alignment destroyed.

Calibration is scored as the mean squared error of predicted probability vs the true `p` — the reducible/reliability component of the Brier score; the irreducible `p(1−p)` term is identical across predictors on the same categories and cancels in every reported DIFFERENCE, so these gains are genuine expected-Brier reductions (cross-checked empirically in the experiment's `--pilot` path). [FACT: `experiments/comparison_metacog.py` docstring + constants]

`brier_reduction = err_base − err_comparison` on heldout is the primary metric. It is genuinely falsifiable: with a large skill gap and few OTHER samples the correction is biased and the gain REVERSES [FACT: spec probe `theta_o=3 / n_o=2 → −0.018`], and the shuffled control is negative.

## Confirmed caveats (adversarial review, 2026-07-14)

Recorded transparently — the verdict stands, but its *reading* is narrowed by three findings that survived verification:

1. **Mechanism-attribution gap (primary caveat).** The verdict-level design isolates comparison CONTENT (via `shuffled_gain`) but does NOT isolate the specific skill-gap-correction term `delta_hat`. A mechanism-light variant — fuse OTHER's difficulty-ALIGNED heldout rate with NO skill-gap shift (`delta_hat := 0`) — already scores **+0.014** of the +0.019 [FACT: `delta_hat:=0` ablation probe over the frozen estimator, confirmatory seeds 981000–981004, 2026-07-14]. So the skill-gap correction *itself* contributes only **~+0.005** [FACT: same probe], and most of the gain is difficulty-aligned fusion, not the advertised skill-gap mechanism. This is NOT a trivially-clearable metric — the baseline is exactly 0 and the shuffled control is negative (see Verdict) — but no condition in the run's ablation attributes the effect to `delta_hat` specifically. Honest statement: *the comparison signal calibrates; the skill-gap correction is a minority of why.*
2. **Advertised n was misleading.** The spec's `experiment.n` read `80`, but the harness decides on the mean over `evaluation.seeds = 5` universes (seeds 981000–981004); 80 is the heldout-category scoring set WITHIN each universe, not the number of independent decision samples. [FACT: `spec_compiler/harness.py` `run_ablation`, seeds from `evaluation.seeds`] **Fixed** in this pass: `experiment.n` corrected to `5` with an explanatory note; the 80 heldout categories remain documented in `experiment.dataset`. Gating fields (metric name, failure threshold, bands, prediction numbers) were left untouched — those are locked post-run.
3. **Part of the gain is a sample-count asymmetry — and that is defended.** OTHER carries 5× SELF's heldout observations (`N_O_HELD = 15` vs `N_S_HELD = 3`), which is part of why the social signal helps at all. The `shuffled_gain` null holds that asymmetry FIXED (same OTHER samples, alignment destroyed) and still goes negative, so the gain is the comparison's difficulty-aligned CONTENT, not merely "more observations". [FACT: run log `shuffled_gain = −0.032`; experiment constants] This is a strength of the design, stated so it is not mistaken for an unaddressed confound.

Prose fixes applied (no gating field changed): `experiment.n` 80→5 + note; a `delta_hat`-drop entry added to `evaluation.ablation`; attribution + sample-asymmetry caveats appended to the spec self-check block and to the experiment docstring. Spec re-validates PASS 6/6. [FACT: `python rsc.py validate specs/comparison_metacog.yaml`, 2026-07-14]

## Scope guard

C0/C1 functional calibration only. "Metacognition" here means a capability ESTIMATE — a functional self-performance prediction — NOT any phenomenal self-awareness, introspective experience, or qualia. The C0⇏C4 line is never crossed; this ADR makes no sentience claim of any kind. [FACT: spec + experiment `SCOPE` block] Permitted interpretation: functional self-performance estimation. Forbidden interpretation: introspective/phenomenal self-knowledge.

## Verdict

**INTEGRATE** — `python rsc.py run comparison_metacog`, confirmatory family 981000+, 5 universes, 2026-07-14. All numbers [FACT: run log]:

| condition | mean | std | role |
|---|---|---|---|
| **comparison_gain** (primary) | **+0.019** | 0.003 | calibration gain over self-only baseline |
| shuffled_gain | −0.032 | 0.011 | discriminating control (alignment destroyed) |
| null_control | 0.000 | 0.000 | plumbing zero-point (base vs base) |

- comparison_gain **+0.019 ≥ 0.015 → INTEGRATE**; `failure_condition` (< 0.005) not triggered. Pre-registered expectation was `+0.018` [FACT: spec `prediction.expected`, pilot-derived and rounded down]; pilot family 980500 (n=10) had mean **+0.0194**, std 0.0037 [FACT: `--pilot` run]. The confirmatory family reproduces it.
- **Honest reading of "does social comparison calibrate the self-model": yes, but with a narrowed mechanism claim.** The effect is real and directional — baseline gain is structurally 0, the shuffled control is clearly negative (−0.032, ~3 SE below 0), and the metric reverses in adjacent regimes — so it is not pinned positive by construction. BUT most of the +0.019 (~+0.014) comes from fusing OTHER's *difficulty-aligned* success rate; the specific skill-gap-correction term the architecture is named for adds only ~+0.005, and the run does not isolate it. The signal that calibrates is "OTHER's outcome on THIS task, correctly aligned to difficulty," more than "OTHER's outcome corrected by our estimated skill gap."
- **Scope caveat (locked):** a single synthetic IRT family. The 5 confirmatory universes are independent draws (unlike ADR-008's frozen snapshot), but they are simulated, not empirical; the verdict is scoped to "this generative world." The correction also assumes shared task difficulty (same world) and degrades to negative when the skill gap is large and OTHER is barely observed.

## Consequence

INTEGRATE licenses treating comparison-derived pseudo-observations as a sanctioned self-calibration input in the kernel's metacognition slot — but the ADR records that the *content alignment*, not the skill-gap correction per se, is doing most of the work. A follow-up that promotes the `delta_hat := 0` aligned-fusion variant to a verdict-level condition (so the skill-gap term is falsifiably isolated) is the honest next step before claiming the skill-gap mechanism specifically. Nothing here touches C4/phenomenal scope, and nothing is wired to the body — this is a kernel-internal calibration decision on a synthetic world.
