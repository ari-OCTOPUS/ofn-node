# ADR-006 — Consolidation as library learning vs raw replay

- **Status:** Closed — machine verdict INTEGRATE (see §Verdict)
- **Date:** 2026-07-14
- **Spec:** `specs/consolidation.yaml` (H-OWN-04 / EXP-002, PASS 6/6) · `experiments/consolidation.py`
- **Decision rule (GO/NO-GO):** schema_minus_replay < 0.0 → DISCARD · [0.0,0.03) → OPTIMIZE · ≥0.03 → INTEGRATE

## Context

Operationalizes H-OWN-04 [P L1486] / EXP-002 [P L1811]: consolidation should
convert repeated episodes into a reusable **schema library** rather than merely
replaying raw episodes. Reuses gridworld_wm (improve-not-rewrite); seed family
998000+.

## Decision

Three equal-budget arms sharing a base tabular agent (abstract
minimal-sufficient representation, B_TRAIN episodes on train tasks):
- **no_consolidation** — base, frozen.
- **raw_replay** — B_CONS more Q-learning on train tasks.
- **schema_library** — consolidate experience into bin→most-winning-action
  rules (roll out the base policy, tally actions on winning episodes), seed a
  fresh Q from the library.
Primary metric = schema_transfer − raw_replay_transfer on heldout.

## Methodological finding (the important part) — a confound caught pre-run

The first pilot showed schema beating replay by a striking **+0.077**. That was
an **artifact**: `train`'s ε-schedule restarts at ε_hi=0.30, so "raw replay"
was really a fresh burst of high-exploration random actions that corrupted the
converged base Q — not a fair refinement. Fix: `train` gained optional
`eps_hi/eps_lo` params (backward-compatible), and raw_replay now runs a
low-exploration (ε=0.05) refinement. The apparent effect collapsed to **+0.010**
[FACT: smoke 2026-07-14]. The honest lesson: most of the naive "library beats
replay" signal was a broken baseline. This is exactly why the pipeline
smoke-tests and freezes before the confirmatory run.

## Honest scope

In a **flat tabular** grid-world with a fixed good abstraction, schema
consolidation and fair replay operate on the same bins and largely converge, so
any library-learning advantage is expected to be small. The real payoff of
library learning (compositional reuse, DreamCoder/Voyager-style) needs a
compositional task space this substrate does not have. A likely OPTIMIZE/DISCARD
here is a legitimate negative-ish result, not a failure of the method — and the
`schema_vs_base` control plus the memory-size ablation (library rules ≪ raw
episodes) document the compression angle EXP-002 also asks about. C0/C1 scope;
no C4 claim.

## Verdict

**INTEGRATE** — `python rsc.py run consolidation`, family 998000+, 5 seeds,
120k budget, 2026-07-14. All numbers [FACT: run log]:

| condition | mean | std |
|---|---|---|
| **schema_vs_replay** (primary) | **0.045** | 0.051 |
| schema_vs_base (control) | 0.057 | 0.008 |

- schema_vs_replay 0.045 ≥ 0.03 → **INTEGRATE**; failure (<0.0) not triggered.
- The cleaner signal is **schema_vs_base = 0.057 with low std 0.008**: the
  consolidated library beats the frozen base robustly. Majority-vote
  consolidation across many train tasks sharing an abstract bin DENOISES the
  per-bin action (better than any single bin's raw Q-argmax), so the library
  transfers better than both the base and raw replay. This is a genuine
  "episodes → reusable schema" gain, not the earlier ε-restart artifact.
- **Honest caveat:** schema_vs_replay's std (0.051) is larger than its mean —
  raw_replay is itself noisy (helps some universes, hurts others), so the
  primary estimate is ~2 SE above zero, not tight. The robust claim is
  schema > base; schema > replay holds on the mean but with wide variance. A
  follow-up should add more seeds for a tighter interval before treating the
  INTEGRATE as settled.
- At the 60k single-seed pilot the effect was only +0.010; at 120k×5 it rose to
  +0.045 — consolidation's edge grows as the base converges (a denoised library
  helps more when there is a well-formed policy to compress).
