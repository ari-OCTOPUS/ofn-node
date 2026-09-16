# ADR-020 — Skill-gap attribution: gating the increment v1 was named for (H-OWN-02b)

- **Status:** Closed — machine verdict OPTIMIZE (see §Verdict)
- **Date:** 2026-07-14
- **Spec:** `specs/comparison_metacog_v2.yaml` (H-OWN-02b, PASS 6/6) · `experiments/comparison_metacog_v2.py` · declared follow-up to `adr/ADR-010-comparison-metacog.md`
- **Decision rule (GO/NO-GO):** delta_gain < 0.002 → DISCARD · [0.002, 0.008) → OPTIMIZE · ≥ 0.008 → INTEGRATE. Falsifier: `delta_gain < 0.002` rejects H-OWN-02b. [FACT: spec `decision_rule` + `failure_condition`]

## Context

ADR-010 closed INTEGRATE (+0.019) with a recorded mechanism-attribution caveat:
the skill-gap correction `delta_hat` — the term the comparison-metacognition
architecture is *named* for — was never isolated by a gated condition. An
out-of-verdict probe put difficulty-ALIGNED fusion (`delta_hat := 0`) at ~+0.014
of the +0.019, leaving only ~+0.005 to the correction itself [FACT: ADR-010
§Confirmed caveats 1]. ADR-010 §Consequence declared the honest next step:
promote that aligned-fusion variant to a verdict-level condition so the
skill-gap term is falsifiably isolated. **v2 executes exactly that follow-up:
the gate now sits DIRECTLY on the mechanism-specific increment.**

Fresh preregistration, no retro-edit: pilot family 946000 (n=10) set the bands
and was FROZEN; confirmatory family 946500–946504 is disjoint from the pilot
and from every v1 family (980500+/981000+). The Rasch/IRT world is bit-identical
to v1's — enforced at runtime, not merely claimed: every universe is
cross-checked against v1's `universe_result` to 1e-12 (`err_base`, `err_cmp`,
`delta_hat`). v1's spec, experiment, and ADR-010 record are untouched. [FACT:
spec header + `experiments/comparison_metacog_v2.py` integrity asserts]

## Decision — gate the increment, against the strongest mechanism-light baseline

Primary metric: **delta_gain = brier_reduction(full mechanism) −
brier_reduction(aligned fusion) = err_aligned − err_full**, paired per universe.
The v2 baseline is NOT v1's self-only shrinkage but the strongest
mechanism-light variant — identical evidence, prior, OTHER observations and
fusion machinery, with the learned logit shift set to zero. Whatever survives
that subtraction is what `delta_hat` itself buys. Conditions (all on the
identical universe per seed index):

- **delta_gain (primary):** full fusion (`+delta_hat`) vs aligned fusion (`+0`).
- **shuffled_delta_gain (discriminating control):** `delta_hat` re-estimated
  under an exchangeability null — SELF/OTHER roles coin-flip swapped per train
  category (an exact sign flip, since `N_S_TRAIN == N_O_TRAIN`). Skill
  information destroyed; world, alignment, sample counts, fusion weight all
  held fixed. Must be ~0 or negative.
- **aligned_gain (context, NOT gated):** aligned fusion's own gain over v1's
  self-only baseline — the mechanism-light share, for attribution accounting.
- **null_control:** aligned vs aligned, exactly 0.

The attribution ledger is exact: `full_gain = aligned_gain + delta_gain`
(asserted to 1e-15 in the pilot path). Falsifiable: a biased/noisy `delta_hat`
shifts OTHER's logit the wrong way and the increment goes negative — v1's own
probe reversed the whole gain at `theta_o=3 / n_o=2` [FACT: ADR-010, −0.018].

## Verdict

**OPTIMIZE** — `python rsc.py run comparison_metacog_v2`, confirmatory family
946500 (disjoint from pilot 946000), 5 universes, 2026-07-14. All numbers
[FACT: run log]:

| condition | mean | std | role |
|---|---|---|---|
| **delta_gain** (primary) | **+0.005** | 0.001 | skill-gap correction's own increment over aligned fusion |
| shuffled_delta_gain (control) | −0.001 | 0.002 | exchangeability-null gap (information-free shift) |
| aligned_gain (context, not gated) | +0.015 | 0.001 | mechanism-light share of the v1 effect |
| null_control | 0.000 | 0.000 | plumbing zero-point (aligned vs aligned) |

- delta_gain **+0.005 ∈ [0.002, 0.008) → OPTIMIZE**; `failure_condition`
  (< 0.002) not triggered. Pre-registered expectation was `+0.004` [FACT: spec
  `prediction.expected`, pilot mean +0.0044 rounded down]; the confirmatory
  family reproduces it (unrounded mean +0.0046).
- **Tiny but real.** Per-universe delta_gain runs +0.0029 … +0.0073 — all 5
  positive [FACT: per-universe log, seeds 946500–946504]. The shuffled control
  is ≤ 0 in the mean (−0.001; per-universe −0.0032 … +0.0019, straddling zero
  as an information-free shift should), and the null zero-point is exact. On
  the decision (mean-over-5) scale the primary sits ~6.8σ above the shuffled
  null mean [FACT: pilot null parameters, SE = 0.0019/√5].
- **Honest reading:** v1's +0.019 headline was mostly aligned fusion — the
  mechanism-light share reproduces at +0.015 here. The skill-gap correction
  *itself* contributes ~+0.005 and lands OPTIMIZE just above the 0.002 kill
  line. The correction is real (all seeds positive, control at zero), but it
  stays a minority share of the total effect: keep-and-tune, NOT
  first-class-mechanism status. The INTEGRATE bar (≥ 0.008 ≈ 40% of v1's total)
  — the level at which naming the architecture after `delta_hat` would be
  justified — was not reached.

## Confirmed caveats (adversarial review)

1. **DISCARD-reachability rationale mixed scales (apples/oranges) — restated.**
   The frozen band-rationale comment argued "DISCARD is live" by comparing the
   pilot **per-universe min** (+0.0027) to the 0.002 kill line. But the gate is
   applied to the **mean over 5 universes**, not to any single universe; on the
   mean scale the pilot (mean +0.0044, std 0.0009) puts the kill line
   ≈ (0.0044 − 0.002)/(0.0009/√5) ≈ **6 SE below** the expected mean, so
   DISCARD by sampling noise alone was far less live than the comment implied.
   DISCARD remained genuinely reachable only via regime failure — a
   biased/noisy `delta_hat` driving the increment negative (v1's probe: −0.018)
   — not via per-universe spread. Restated in the spec prose; gating fields
   untouched.
2. **Kill line vs null-band edge — a scale wrinkle, stated precisely.** The
   spec's failure note motivated the 0.002 SESOI as "inside the
   exchangeability-null band", citing the **per-universe** +2σ edge
   (−0.0011 + 2·0.0019 ≈ +0.0027). The gate, however, is on the **mean** over
   5 universes, whose null band is tighter: upper 2σ edge ≈ −0.0011 +
   2·0.0019/√5 ≈ **+0.0006**. Precisely: a passing mean at the 0.002 line sits
   ~3.6σ above the null mean on the decision scale (the confirmatory +0.005
   sits ~6.8σ above), so the gate is *conservative* relative to the null it
   cites — a mean in [0.002, 0.0027) is NOT null-compatible on the scale that
   decides. The wrinkle cuts in the verdict's favor, but the original prose
   conflated the two scales; restated in the spec note.
3. **Latent module-state fragility (same pattern ADR-016 noted).** `CMP2_LOG`
   plus the per-condition counter closure: the single 5-seed canonical run is
   correct, but `evaluation.seeds > 5` would advance into universes (946505+)
   that were never piloted, and repeated factory calls in one process append
   duplicate log entries. Not triggered by the canonical path; noted for the
   same future refactor.

Prose fixes applied (no gating field changed): the two scale-mixing rationales
above restated in `specs/comparison_metacog_v2.yaml` (failure-note + band
comment) and flagged in the experiment docstring. Spec re-validates PASS 6/6.
[FACT: `python rsc.py validate specs/comparison_metacog_v2.yaml`, 2026-07-14]

## Scope guard

C0/C1, functional calibration only (well inside the C0–C3 functional range).
"Metacognition" here means a capability ESTIMATE — a functional
self-performance prediction — NOT any phenomenal self-awareness, introspective
experience, or qualia; the C0⇏C4 line is never crossed. [FACT: spec +
experiment `SCOPE` blocks] A single synthetic Rasch/IRT family; the increment
only exists where a skill gap is learnable at all (shared train tasks, equal
attempt counts for the swap-null) and shrinks toward 0 as `THETA_S → THETA_O`
(declared tradeoff). Honest reading: on this generative world, the skill-gap
correction buys a small, real, all-seeds-positive calibration increment beyond
difficulty-aligned fusion — enough to keep and tune it, not enough to headline
the architecture.
