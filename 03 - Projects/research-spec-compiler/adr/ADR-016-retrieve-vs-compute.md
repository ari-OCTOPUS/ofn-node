# ADR-016 — Retrieve-vs-compute scheduler with costs in the objective (EXP-005)

- **Status:** Closed — machine verdict INTEGRATE (see §Verdict)
- **Date:** 2026-07-14
- **Spec:** `specs/retrieve_compute.yaml` (EXP-005, PASS 6/6) · `experiments/retrieve_compute.py`
- **Decision rule (GO/NO-GO):** scheduler_advantage < 0.01 → DISCARD · [0.01,0.03) → OPTIMIZE · ≥0.03 → INTEGRATE

## Context

EXP-005 [P L1823]: "Always-Retrieve vs Always-Compute vs Learned Scheduler —
include retrieval AND compute costs in the objective." A small deterministic,
CRC-seeded contextual cache/compute env (control_signals + homeostasis lineage,
zero LLM). States vary in cache staleness; **retrieve** is cheap but wrong on
drifted states, **compute** is costly but correct. The objective is
regret-under-compute-budget: `J = decision_regret + PRICE·compute_cost` (lower
is better).

## Decision — beat the BETTER pure strategy, not a strawman

Three arms: `always_retrieve`, `always_compute`, `learned_scheduler` (thresholds
a noisy staleness signal to choose per state). Primary metric =
**min(J_always_retrieve, J_always_compute) − J_learned** — the advantage over the
BETTER of the two pure baselines (so a scheduler that only beats the worse pure
strategy scores ≤ 0). Control = scheduler with a SHUFFLED staleness signal
(must be ~0). This design directly answers the strawman risk that sank the first
cut of ADR-008.

## Verdict

**INTEGRATE** — `python rsc.py run retrieve_compute`, confirmatory family 962500
(disjoint from pilot 962000), 5 seeds, 2026-07-14. All numbers [FACT: run log]:

| condition | mean | std |
|---|---|---|
| **scheduler_advantage** (vs better pure, primary) | **0.031** | 0.010 |
| shuffled_signal (control) | −0.022 | 0.021 |
| no_drift_null | 0.000 | 0.000 |

- 0.031 ≥ 0.03 → **INTEGRATE**. The learned scheduler beats the *better* of the
  two pure strategies at equal cost accounting — it genuinely arbitrates
  retrieve-vs-compute rather than mimicking whichever pure strategy happens to
  win. shuffled_signal < 0 (a mismatched staleness signal HURTS) and
  no_drift_null = 0 (with no staleness there is nothing to schedule) confirm the
  mechanism.

## Confirmed caveats (adversarial review)

1. **Was unwired at build time** (its local registry was dead code); the
   orchestrator added the import + `REGISTRY_REAL["retrieve_compute"]` so the
   canonical `python rsc.py run retrieve_compute` reproduces the verdict — done.
   (Because it was in neither registry, the CLI errored loudly rather than
   silently serving a mock — no fabricated-verdict risk.)
2. **Modest absolute margin** (0.031 ± 0.010, ~3 SE > 0) — robust but small.
3. **Latent module-state fragility** (RC_LOG + counter closure): a single 5-seed
   canonical run is correct; calling the factory twice in one process or
   seeds>5 would advance into never-piloted seeds. Not triggered by the standard
   path; noted for a future refactor.

## Scope guard

C0–C3, synthetic contextual env; the retrieve/compute cost model is stipulated.
No phenomenal/qualia claim. Requires the environment to expose a staleness
signal and counterfactual compute cost (declared tradeoff). Honest reading: a
learned scheduler that prices compute genuinely beats both pure policies, by a
small robust margin, on this synthetic env.
