# ADR-021 — Adaptive forgetting v2: utility eviction vs the strong FIFO baseline (EXP-004b)

- **Status:** Closed — machine verdict REJECTED / DISCARD band (failure condition triggered, see §Verdict)
- **Date:** 2026-07-14
- **Spec:** `specs/adaptive_forgetting_v2.yaml` (EXP-004b, PASS 6/6, one accepted WARN) · `experiments/adaptive_forgetting_v2.py`
- **Decision rule (GO/NO-GO):** adaptive_advantage_v2 < 0.03 → DISCARD · [0.03,0.06) → OPTIMIZE · ≥0.06 → INTEGRATE (SESOI and bands inherited FROZEN from v1 / ADR-015)

## Context

Declared follow-up to ADR-015. v1's machine gate used the WEAKEST baseline
(cumulative / never-forget) and landed OPTIMIZE (+0.056); its confirmed caveat
#1 recorded that against the STRONGER baseline — FIFO, which under a purely
temporal drift evicts stale rules by accident — the edge was +0.018, below the
0.03 SESOI. v2 preregisters exactly THAT contrast as the gated primary:
**adaptive_advantage_v2 = success(rate_adaptive) − success(FIFO)** at equal
bounded capacity C=90 under drift, on post-drift heldout. One a-priori
strengthening was declared before the pilot (utility = recency-decayed
HIT-RATE, i.e. decayed hits normalized by decayed exposure, correcting the
frequency-conflation and tenure-asymmetry biases of v1's decayed count). The
honest pilot (assigned family 948000) landed +0.016 ± 0.018 — below the kill
line — and the spec said so out loud: **the preregistered expectation was
DISCARD**, and the kill line was deliberately not lowered to rescue the
hypothesis. All constants (C=90, γ=0.98, stream 300+120, SESOI 0.03, bands)
inherited frozen from v1; nothing re-tuned on the v2 pilot.

## Decision — gate on the strong baseline, accept the likely negative

Five conditions: `null_unbounded` (rate−FIFO with no capacity pressure —
structurally exactly 0), `null_nodrift` (decay on vs off within the identical
rate algorithm on a stationary stream — must be ≤ ~0), `vs_raw_decay`
(reported: what the strengthening itself added), `v1_rule_vs_fifo` (reported:
replication reference for ADR-015's +0.018), and the primary. Confirmatory
family 953000 was never piloted; pilot family 948000 only calibrated
`prediction.expected`, then was frozen.

## Verdict

**REJECTED** — `python rsc.py run adaptive_forgetting_v2`, confirmatory family
953000 (disjoint from pilot 948000 and every other family in the repo),
5 seeds, 2026-07-14. All numbers [FACT: run log]:

| condition | mean | std |
|---|---|---|
| **adaptive_advantage_v2** (rate-adaptive − FIFO, primary) | **+0.023** | 0.021 |
| null_unbounded (control) | 0.000 | 0.000 |
| null_nodrift (decay-necessity control) | −0.008 | 0.013 |
| vs_raw_decay (strengthening delta, reported) | +0.005 | 0.020 |
| v1_rule_vs_fifo (ADR-015 replication, reported) | +0.018 | 0.017 |

- 0.023 < 0.03 → **failure_condition TRIGGERED → REJECTED (DISCARD band)**,
  exactly as the preregistration anticipated it might. Both controls held:
  null_unbounded = 0.000 exactly (the structural guarantee — any edge is
  capacity-driven) and null_nodrift = −0.008 ≤ 0 (drift-necessity).
  v1_rule_vs_fifo = +0.018 replicates ADR-015's confirmatory +0.018 on a third
  disjoint family — the sub-SESOI edge vs FIFO is a stable fact, not noise.
- This is the project's third honest negative (after ADR-001 and ADR-013), and
  it is the discipline working, not failing: v1's OPTIMIZE stands — but only
  for adaptive-vs-never-forget (mechanism isolation). The STRONG claim
  ("utility-aware forgetting beats a strong forgetting baseline") is now
  rejected by preregistration.
- Honest reading: under this purely temporal drift, ANY forgetting — even
  blind FIFO — captures most of the value of forgetting; utility-awareness
  adds only a sub-SESOI sliver on top. That is a real scientific finding about
  WHERE the mechanism matters: forgetting per se matters under drift; *what*
  you forget barely matters when age and staleness coincide.

## Confirmed caveats (adversarial review)

1. **The verdict is regime-scoped, not universal.** The drift is purely
   temporal, so oldest ≈ stalest and FIFO is accidentally near-optimal — the
   very reason it was chosen as the strong baseline. v2 says nothing about
   regimes where age and staleness decouple (recurring/cyclic regimes,
   per-context drift rates); that is the question this result delimits, not
   answers.
2. **Near-the-line negative on heterogeneous seeds.** Per-seed deltas +0.020,
   0.000, 0.000, +0.053, +0.040 [FACT: run log] — two seeds exactly 0 and two
   individually above the SESOI; mean 0.023, SEM ≈ 0.009, no significance test
   in the harness (same limitation as ADR-015 caveat 2). The band assignment
   is correct, but a modest upward shift on another family could read
   OPTIMIZE; symmetric honesty with v1's fragile-OPTIMIZE caveat.
3. **Accepted validator WARN (kill_line_placement).** The 0.03 threshold sits
   above prediction.expected = 0.016, so the validator flags that the spec can
   "fail without contradicting the hypothesis." Disclosed and accepted a
   priori: the SESOI is frozen from v1 and lowering it post-pilot would have
   been rescue-by-threshold. Here the WARN is the preregistration discipline
   made visible.
4. **The a-priori strengthening bought ~nothing.** vs_raw_decay = +0.005 ±
   0.020: the hit-rate repair is definitionally real (stale-popular mass decays
   to a rate → 0; fresh rules judged on own tenure) but had no measurable
   FIFO-relative payoff in this regime (pilot said the same: +0.000 at C=90).
5. **Latent module-state fragility, not triggered.** Same pattern as ADR-016
   caveat 3: per-condition counter closures plus module-level `_UNIVERSE_CACHE`
   / `AFV2_LOG` mean a single 5-seed canonical run is correct, but invoking the
   factory twice in one process would advance into never-piloted seeds. Unlike
   ADR-016, the experiment WAS correctly wired at build time
   (`experiments/__init__.py` REGISTRY_REAL), so the canonical
   `python rsc.py run adaptive_forgetting_v2` reproduces the verdict as-is.
6. **Nulls are prose-enforced, not machine-gated** — only the primary is
   gated; the "unbounded = 0 / nodrift ≤ 0" requirements are checked by review
   (both hold: 0.000 exactly and −0.008).

## Scope guard

C0–C3, grid-world family, single-snapshot synthetic temporal drift; no
phenomenal/qualia claim. The v1 record (ADR-015) is untouched: its OPTIMIZE
verdict remains valid for the adaptive-vs-never-forget contrast. Honest
reading: resource-rational forgetting survives as "bounded stores must forget
under drift," but the utility-aware *selection* of what to forget adds no
established value over blind temporally-biased eviction in this regime — and
that is now said out loud, by the gate, as preregistered.
