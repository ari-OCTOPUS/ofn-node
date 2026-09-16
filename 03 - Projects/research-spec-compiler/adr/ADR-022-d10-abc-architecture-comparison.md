# ADR-022 — D10-ABC: Architecture comparison (single-model vs orchestrator vs multi-agent)

- **Status:** Open — preregistration frozen; confirmatory run NOT launched (requires owner verdict for real-model injection)
- **Date:** 2026-08-10
- **Spec:** `specs/d10_abc_architecture_comparison.yaml` · `experiments/d10_abc.py`
- **Decision rule:** quality(C)−quality(B) < 0.05 → REJECT_C_PREFER_B_OR_A · [0.05,0.10) → RESTRICT_C · ≥0.10 → KEEP_C (cost guardrail may downgrade)

## Namespacing

This is **D10-ABC**, explicitly distinct from **Mining D-10** (a governance
`HARD_STOP` rule in `03-Projects/Mining/mining_os/organs/governance.py`). No
collision. The "ABC" suffix is the disambiguator: three architecture arms.

## Context

The audit (2026-08-10) found that D10-ABC was `spec-only` — no benchmark
runner, frozen task suite, arm dispatcher, trace schema, A/A runner, blinded
judge protocol, or analysis script existed. The current cycle-preregistration
infrastructure had ~14 rows repeating the same goal/metric with target `> 0`,
which is pseudoreplication (effective hypothesis count = 1, not 14).

This ADR establishes the full statistical preregistration and delivers a
deterministic fake harness that validates the plumbing end-to-end.

## Arms

```
A = single model + same tools (no role switching, no handoff)
B = one orchestrator + explicit role switching (in-prompt, not cross-process)
C = current multi-agent state-file architecture (organism + cortex + handoff)
```

Arm C is defined from **runtime**, not documentation. The current architecture
is state-file-handoff-based, not chat-handoff-based — the benchmark measures
what actually runs.

## Primary estimand

```
paired_quality_diff_C_minus_B = quality(C) − quality(B) per task
```

Task is the unit of inference (not judge vote, not subagent output, not episode).

## SESOI

`delta = 0.05` quality points. This is the minimum improvement that justifies
the coordination cost of multi-agent architecture (handoff overhead, state sync,
failure surface, latency). It is set **a priori** from the architecture
rationale, NOT from pilot treatment results.

## Sensitivity table (paired, two-sided alpha 0.05, power 0.80)

```
sigma_d=10: n=32 | sigma_d=15: n=71 | sigma_d=20: n=126 | sigma_d=25: n=197
```

The final `n` is UNKNOWN until the A/A pilot calibrates `sigma_d`. The "28
tasks" figure from the prompt was a planning placeholder, not a power result.

## Multiplicity

- **Primary:** C vs B (the gated contrast)
- **Secondary:** C vs A (closed-testing — tested ONLY if primary is significant)
- **Exploratory:** B vs A (per-class, not powered)
- `max(A,B)` selection after observing results is **PROHIBITED** (selection bias)
- Holm correction for secondary metrics

## A/A objectives

The A/A run is NOT for treatment effects. It is for:
1. State/cache leakage detection
2. Instrumentation correctness
3. Order/warm-up/time drift
4. Judge repeatability (inter-rater reliability)
5. Paired variance estimate (`sigma_d` calibration)

Rules:
- Interleaved/counterbalanced
- Equivalence margin preregistered (TOST)
- CI includes zero ≠ equivalence
- Do not claim Type-I calibration with <20 tasks
- If budget is insufficient for a conclusive result, say INCONCLUSIVE

## Cost guardrail

Regardless of quality verdict: if `cost(C) > cost(B) * 1.5` OR
`error(C) > error(B) + 0.1`, downgrade by one band
(KEEP_C → RESTRICT_C, RESTRICT_C → REJECT_C_PREFER_B_OR_A). Quality alone is not enough.

## Decision rule

| Primary mean | Verdict |
|---|---|
| < 0.05 | REJECT_C_PREFER_B_OR_A |
| [0.05, 0.10) | RESTRICT_C |
| ≥ 0.10 | KEEP_C |

Cost guardrail may downgrade by one band.

## Verdict

**PENDING** — the deterministic fake harness validates plumbing only. The
confirmatory run with real models requires:
1. Owner verdict to authorize paid API calls
2. A/A pilot to calibrate `sigma_d`
3. Final `n` locked from power calculation
4. Real model adapters injected (not the deterministic stub)

## Confirmed caveats

1. **The fake harness validates plumbing, not efficacy.** The deterministic
   stub has an embedded ground truth that makes the harness testable. Real
   efficacy measurement requires real model injection — a separate owner-gated
   step.

2. **Task suite is not yet frozen from real workload.** The current
   `TASK_MANIFEST` is a synthetic placeholder. The real suite must be
   stratified from the system's 30-day workload (read-only, sanitized).

3. **Judging is not yet external/blinded in production.** The harness
   simulates blinding (arm → ARM_X). Real judging requires external judges
   who don't know the code map.

4. **The preregistration is immutable after Stage 1 launch.** Any change =
   amendment / new ADR. The pilot may only calibrate `sigma_d`, not SESOI,
   arms, or decision_rule.
