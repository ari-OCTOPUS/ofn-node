# ADR-002 — Monte-Carlo Drake census over seeded universes

- **Status:** Closed — machine verdict OPTIMIZE (see §Verdict)
- **Date:** 2026-07-13
- **Specs:** `specs/drake_kernels.yaml` (PASS 6/6) · `specs/drake_multiverse.yaml` (FAIL 4/6, by design)
- **Decision rule (GO/NO-GO):** f_transfer < 0.4 → DISCARD · [0.4, 0.7) → OPTIMIZE · ≥ 0.7 → INTEGRATE

## Context

Owner request: use the Drake equation as an epistemic scaffold for
"multiverse and other consciousnesses". The Drake form N = Π fᵢ is valuable
exactly because it decomposes an untestable-looking question into factors that
can be individually tagged [FACT]/[EST]. Applied to the physical multiverse,
every consciousness factor is an [EST] with no observation channel — so the
raw idea must FAIL the compiler, and it does: `drake_multiverse.yaml` is
rejected on killer.falsifiability + killer.decision_rule [FACT: validate log
2026-07-13]. That rejection is a feature, not an accident: it is the formal
statement "این، در این شکل، شبه‌پژوهش است".

## Decision — the census pattern

The testable residue of the idea is a **Monte-Carlo Drake census over the
only multiverse with an observation channel: a simulated one.**

- Universe = independent seeded task suite (family 997000+, disjoint from
  pilot 987000 and confirmatory 991000+).
- Inside each universe, run the FROZEN EXP-001 kernel protocol unchanged
  (`experiments/drake_kernels.py` reuses `gridworld_wm` functions verbatim —
  no fork, per the improve-not-rewrite doctrine).
- Drake factor measured: f_transfer = fraction of universes where the
  WM-bottleneck kernel reaches transfer_accuracy > 0.5 (semantic threshold:
  "solves the majority of heldout episodes"; not tuned on outcomes).
- Baseline census: the unlimited-buffer kernel in the same universes.
- N_viable = N_universes × f_transfer is the honest analogue of Drake's
  N = R* × … : one measurable factor, everything else explicit [EST].

**Tradeoff:** compute × universes ↑; n=10 gives a wide CI on f_transfer
(±~0.15) — enough for the coarse DISCARD/OPTIMIZE/INTEGRATE bands, not for
fine estimation.

## Scope guard (locked)

C0 tabular agents in this simulated family. Licenses NO claim about the
physical multiverse, biological consciousness, or C4/LLM kernels. What it
DOES give the project: a reusable template for turning "big unanswerable"
questions into a factor chain where at least one factor runs on the harness
and the rest carry honest [EST] tags.

## Verdict

**OPTIMIZE** — machine verdict, real census run (10 universes, seed family
997000+, frozen EXP-001 protocol per universe), 2026-07-13. All numbers
[FACT: run log]:

- f_transfer(limited_wm) = **0.600** (6/10 universes above the 0.5 viability
  line; per-universe: 0.61, 0.47, 0.49, 0.64, 0.26, 0.67, 0.59, 0.57, 0.38,
  0.60)
- f_transfer(unlimited) = **0.000** (0/10; per-universe range 0.22–0.34 — the
  random-walk floor everywhere)
- failure_condition (f_transfer < 0.4) not triggered; 0.600 ∈ [0.4, 0.7) →
  OPTIMIZE.

Reading: emergence of transferable abstraction under a WM bottleneck is
**frequent but not robust** across universes — the dominant failure mode is
gating instability (universe 5 collapsed to 0.26; three near-misses at
0.38–0.49), the same instability seen across seeds in ADR-001. The Drake
factorization did its job: it converted "does abstraction emerge?" into a
measured between-universe rate with a named bottleneck factor to improve
(selection reliability), instead of a single-world anecdote.
