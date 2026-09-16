# ADR-015 — Adaptive forgetting under distribution drift (EXP-004)

- **Status:** Closed — machine verdict OPTIMIZE (see §Verdict)
- **Date:** 2026-07-14
- **Spec:** `specs/adaptive_forgetting.yaml` (EXP-004, PASS 6/6) · `experiments/adaptive_forgetting.py`
- **Decision rule (GO/NO-GO):** adaptive_advantage < 0.03 → DISCARD · [0.03,0.06) → OPTIMIZE · ≥0.06 → INTEGRATE

## Context

EXP-004 [P L1820]: "No-Forgetting vs Adaptive Forgetting — equalize total memory
capacity and compute." Reuses gridworld_wm verbatim. A fixed base cortex streams
experience over a temporal DRIFT (early regime 85% one cue modality → late regime
shifts to the other); winning-trajectory keys stream into a BOUNDED schema store
(capacity C=90, pool ~550) evicted online by one of four rules. All arms share
the identical event stream + key→action per universe and differ ONLY in the
eviction rule; each final store is scored as a policy on the same post-drift
heldout via the frozen `evaluate()`.

## Decision — the four eviction arms

- **adaptive** (treatment): recency-decayed utility (decay 0.98) — evicts rules
  that stopped paying off after the drift.
- **cumulative** (primary baseline): decay 1.0 — keeps stale rules forever.
- **random** / **FIFO**: blind eviction controls.
Primary metric = adaptive − cumulative post-drift heldout success at EQUAL
capacity. Discriminating controls: `null_unbounded` (no capacity pressure → must
be ~0) and `null_nodrift` (no drift → forgetting should not help).

## Verdict

**OPTIMIZE** — `python rsc.py run adaptive_forgetting`, confirmatory family
965000 (disjoint from pilot 960000), 5 seeds, 2026-07-14. All numbers
[FACT: run log]:

| condition | mean | std |
|---|---|---|
| **adaptive_advantage** (vs cumulative, primary) | **0.056** | 0.041 |
| adaptive_vs_random | 0.032 | — |
| adaptive_vs_fifo | 0.018 | — |
| null_unbounded | 0.000 | 0.000 |
| null_nodrift | −0.056 | — |

- 0.056 ∈ [0.03, 0.06) → **OPTIMIZE**. null_unbounded = 0 (capacity pressure is
  necessary — a structural guarantee: identical stores when unbounded);
  null_nodrift = −0.056 (drift is necessary — no drift, forgetting HURTS).

## Confirmed caveats (adversarial review) — read before trusting the verdict

1. **Primary baseline is the WEAKEST arm.** The gate uses adaptive − *cumulative*
   (keeps-everything, the weakest). Against the STRONGER pure baseline (FIFO,
   which forgets old rules by accident), the edge is **+0.018, BELOW the 0.03
   SESOI**. So "adaptive forgetting beats a strong forgetting baseline" is NOT
   established here; adaptive clearly beats only the never-forget arm. The
   adaptive-vs-cumulative choice is defensible as mechanism-isolation (does
   *utility-aware* forgetting beat *no* forgetting under drift → yes) but the
   stronger claim fails.
2. **Thin margin / fragile verdict.** 0.056 ± 0.041 on n=5 with one NEGATIVE
   seed (−0.007); SEM ≈ 0.018. No significance test in the harness. A ~0.026
   downward shift flips OPTIMIZE→DISCARD. The pilot (960000) landed +0.064
   (INTEGRATE band); the disjoint confirmatory landed a band lower — honest
   pilot→confirmatory regression.
3. **Control-strength narrative didn't replicate.** The spec prose called FIFO a
   "strong, drift-aware-by-accident baseline" with adaptive−fifo ≈ +0.041 at
   pilot; confirmatory gives +0.018 (< half). The pilot's random-vs-fifo
   ordering also flipped. The numbers, not the narrative, govern.
4. **Nulls are prose-enforced, not machine-gated** — only adaptive_advantage is
   gated; the "unbounded = 0 / no-drift ≤ 0" requirements are checked by review
   (both hold: 0.000 and −0.056).

## Scope guard

C0–C3, grid-world family, single-snapshot synthetic drift. No phenomenal/qualia
claim. Honest reading: adaptive utility-forgetting gives a small, drift-specific
advantage over never-forgetting, but does NOT clearly beat a plain FIFO — a
modest, appropriately-OPTIMIZE result, not a strong one.
