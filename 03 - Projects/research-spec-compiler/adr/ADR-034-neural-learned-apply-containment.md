# ADR-034 — NEURAL_LEARNED_APPLY containment + demotion

- **Status:** ACCEPTED — owner vote 2026-08-11 (A applied; B implemented in code)
- **Superseded in part by:** [[ADR-035-neural-learned-apply-rearm|ADR-035]] (2026-08-12 owner «هردو» re-armed APPLY=1 + executable path)
- **Date:** 2026-08-11
- **Parent:** ADR-033 Evidence-Control Plane · Inventory Stage 1
- **Evidence:** `_ops/state/adr-033/reports/ADR-034-A-B-EVIDENCE.md`
- **Capability record:** `_ops/capabilities/neural-learned-apply.json` (now mirrors ADR-035)

## Capability Truth (live — see ADR-035 for post-rearm)

Historical containment (2026-08-11 → 2026-08-12):

| Field | Value (ADR-034 era) |
|---|---|
| Capability | neural-learned-apply |
| truth_status | TESTED |
| evidence_level | SHADOW |
| Feature flag (containment) | `OCTOPUS_NEURAL_LEARNED_APPLY=0` |
| Proposal flag | `OCTOPUS_NEURAL_PROTECTIVE_PROPOSAL=1` |
| production_apply_enabled | false |
| allowed_effect | trace_only |

**Preserved under ADR-035:** PainAssessment · PolicyGate `request_protective_halt` · learned_pressure cap · effect-shadow JSONL · APPLY=0 proposal path.

---

## Decision (executed)

| Step | Status |
|---|---|
| **A** — `OCTOPUS_NEURAL_LEARNED_APPLY=0` | **DONE** (`OCTOPUS-flags.cmd`) |
| **B** — demote neural → proposal; PolicyGate owns halt | **DONE** (code + tests) |
| **C** — retain APPLY as control | **Rejected** |
| Stage 2–3 registry/schema | **NEXT** (after B) |
| WORKLOCK + owner approval | after Stage 2–3 |

---

## What changed (B)

1. `_ops/neural/pain_assessment.py` — immutable `PainAssessment`.
2. `wiring.protective_override` → `emit_pain_assessment` (always `override=False`, `executable=False`).
3. `wiring.request_protective_halt` — PolicyGate path (approval + idempotency + kill switch + store).
4. `policy.PROTECTIVE_CONTROL_POLICY` — `protective_halt` ∈ approval_actions.
5. `organism.py` / `brain_worker.py` — neural → `SHADOW_ALERT` + `protective_proposal` only; **never** `_protective_skip`.
6. `OCTOPUS_NEURAL_LEARNED_APPLY=1` **deprecated** for direct apply; shadow fold uses `OCTOPUS_NEURAL_PROTECTIVE_PROPOSAL`.

---

## Historical diagnosis (pre-B)

Full path was: `neural_beat` → learned_pressure fold (APPLY) → `protective_halt` → organism/brain_worker `_protective_skip` / state write, without Redis or kill-switch checks. That violated fail-closed + diagnostic/control separation. See prior revision / Inventory § discrepancy.

---

## Tests (local; not in run_all / WORKLOCK)

- `_ops/tests/test_adr034_neural_demote.py` (primary A+B)
- Updated: `test_organism_protective.py`, `test_frontier.py`, `test_truthmap_fixes.py`, `test_neural_loop_close.py`, `test_hebbian_eventclock.py`

---

## Rollback

Keep `OCTOPUS_NEURAL_LEARNED_APPLY=0`. Do **not** re-arm APPLY=1. Observation: `OCTOPUS_NEURAL_EFFECT_SHADOW` + `OCTOPUS_NEURAL_PROTECTIVE_PROPOSAL`.

---

## Sources

- `_ops/wiring.py` (`emit_pain_assessment`, `request_protective_halt`)
- `_ops/neural/pain_assessment.py`
- `_ops/organism.py`, `_ops/brain_worker.py`
- `_ops/policy/policy_gate.py` (`PROTECTIVE_CONTROL_POLICY`)
- `_ops/OCTOPUS-flags.cmd`
- `_ops/state/adr-033/reports/INVENTORY.md`
- `_ops/state/adr-033/reports/ADR-034-A-B-EVIDENCE.md`
