# ADR-005 — Homeostatic self-model (allostasis) vs reactive control

- **Status:** Closed — machine verdict OPTIMIZE (see §Verdict)
- **Date:** 2026-07-14
- **Spec:** `specs/homeostasis.yaml` (EXP-003, PASS 6/6) · env: `experiments/homeostasis.py` · map: GEOMETRY.md §3
- **Decision rule (GO/NO-GO):** advantage_ood < 0.02 → DISCARD · [0.02,0.05) → OPTIMIZE · ≥0.05 → INTEGRATE

## Context

Promotes the first `[SPEC]` object from GEOMETRY.md to `[RUN]`: the homeostatic
deviation potential `D_t = Σ_i w_i·|s_i − s_i*|` [N F3; O F9] over an internal-
state space. Tests the raw files' H1 [N L833]: an agent with a predictive
self-model of its internal state regulates better **under OOD perturbation**
than a reactive (−D_t-greedy) agent.

## Decision — a new deterministic environment + two hand-coded controllers

`HomeostasisWorld` (new, `experiments/homeostasis.py`): 7×7 grid, 3 needs
(energy/temperature/integrity), one depot per need; needs decay each step,
stepping on a depot refills it, any need hitting 0 kills the agent. `D_t` is the
per-step deviation from the setpoint; the episode metric is its mean (death
fills the remainder at max deviation). No learning, no LLM — the manipulation is
control STRATEGY:
- **reactive** (= self-model ablated): go to the currently-lowest need. Myopic,
  distance-blind −D_t descent — exactly the baseline the file says an agent must
  not rely on alone [N L822].
- **anticipatory** (= predictive self-model / allostasis): model-predictive
  control that simulates "head to depot c, then act reactively" for a 40-step
  horizon and picks the best first target — owns a forward model of depletion
  and weighs travel distance.

Primary metric = **advantage_ood** = reactive_deviation − anticipatory_deviation
under an OOD perturbation (decay ×1.8). Controls: `indist_advantage` (same under
training decay) and a `null_control` (reactive vs reactive = exactly 0).

## Development honesty (pilot → freeze → confirmatory)

The anticipatory policy went through three broken designs before MPC — recorded
so the next agent does not repeat them:
1. pure-slack targeting **oscillated** (two depots, never arriving) → death.
2. reactive+override chased **lost causes** under fast decay → worse than reactive.
3. MPC with too-short horizon (< max time-to-live) was **blind to neglect-deaths**.
4. a **sim/executor mismatch** (planner assumed "reached → reactive" but the
   executor sat on a full depot forever) — fixed by mirroring the sim's first
   action in the executor.
After MPC worked, parameters (OOD_FACTOR=1.8, horizon=40, N_TASKS=60) were
FROZEN on pilot family 995500, and the confirmatory run uses fresh family
996000+. Pilot [FACT: sweep log 2026-07-14]: advantage_ood ≈ 0.02–0.04 across
OOD factors 1.2–2.2, in-distribution advantage ≈ +0.012 — i.e. the self-model
helps, and slightly more under perturbation, but the OOD premium is small
(anticipation is close to a globally-better controller here, not a dramatically
OOD-specific one). This is an honest, non-strawman result: the MPC planner is a
strong best-effort self-model, so if it barely beats reactive that reflects the
environment, not a weak treatment.

## Scope guard (locked)

C3-flavored (self-maintenance) in the file's ladder, but the metric is
**functional regulation only**. Forbidden interpretation: pain/pleasure/affect
[N L867-871]. No C4 claim. The anticipatory agent's extra planning compute is a
declared cost (the file demands costs be stated).

## Verdict

**OPTIMIZE** — `python rsc.py run homeostasis`, confirmatory family 996000+,
5 seeds, 2026-07-14. All numbers [FACT: run log]:

| condition | mean | std |
|---|---|---|
| **ood_advantage** (primary) | **0.029** | 0.005 |
| indist_advantage (control) | 0.015 | 0.006 |
| null_control (reactive vs reactive) | 0.000 | 0.000 |

- ood_advantage 0.029 > SESOI 0.02 → failure not triggered; ∈ [0.02, 0.05) →
  **OPTIMIZE**. null exactly 0 pins the zero-point.
- The self-model helps **more** under OOD (0.029) than in-distribution (0.015):
  the OOD premium is +0.014, positive.
- **Disclosure (from adversarial review, 2026-07-14):** the machine verdict
  gates ONLY on advantage_ood; the OOD-specificity (premium > 0) is a reported
  secondary observation, NOT a gated claim — the verdict would be identical
  with a zero premium. So this run establishes "the predictive self-model adds
  regulation value under OOD" (gated, OPTIMIZE) and merely *suggests* it is
  perturbation-favored (premium +0.014, ungated). A follow-up spec should
  preregister the premium itself as the primary metric to make the
  OOD-specificity claim falsifiable.
- Honest magnitude: the advantage is small in absolute deviation units (~3% of
  the [0,1] range). The predictive self-model earns a real but modest
  regulation edge here; whether it is worth its extra planning compute is the
  OPTIMIZE question for a follow-up.
