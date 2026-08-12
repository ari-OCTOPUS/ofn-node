# Stage 2–3 Evidence — Signals Registry + Semantic Validator

- **Date:** 2026-08-11
- **Prerequisite:** ADR-034 ACCEPTED (A+B); controlled restart AFTER flags APPLY=0 / PROPOSAL=1
- **WORKLOCK:** not registered — proposal only (see `WORKLOCK-PROPOSAL-STAGE-2-3.md`)

## Inputs locked

| Input | Value |
|---|---|
| ADR-034 | ACCEPTED |
| neural-learned-apply | TESTED / SHADOW / trace_only |
| production_apply_enabled | false |
| protective halt | control action (`capabilities-registry.yaml`), **not** a signal |
| Prior validator | JSON Schema only → now Schema + semantic |

## Deliverables

| # | Path | Status |
|---|---|---|
| 1 | `architecture/signals-registry.yaml` | updated (+ `neural-learned-apply`) |
| 2 | `architecture/signals-registry.schema.json` | + `production_apply_enabled` |
| 3 | `_ops/scripts/validate_signals_registry.py` | Schema + semantic + JSON report |
| 4 | `_ops/tests/test_signals_registry_schema.py` | updated |
| 5 | `_ops/tests/test_registry_semantic_validator.py` | new |
| 6 | this evidence file | written |
| — | `architecture/capabilities-registry.yaml` | control inventory (halt **not** in signals) |

## Boundary: signal vs control

- `neural-learned-apply` ∈ **signals-registry** (PainAssessment / proposal / SHADOW).
- `protective-halt-control` ∈ **capabilities-registry** only (`request_protective_halt` + PolicyGate).
- Validator asserts `request_protective_halt` is absent from signals YAML.

## Validator rules enforced

- JSON Schema validate
- duplicate ID reject
- implementation_path / test paths must exist (built statuses)
- SPEC_NOT_BUILT ⇒ `implementation_path=null`
- diagnostic/detector ⇒ `may_gate=false`
- every signal ⇒ `may_mutate_ledger=false`, `may_trigger_tool=false`
- non-none `allowed_effect` ⇒ evidence SHADOW+ + `rollback_flag`
- ARMED/LOCKED ⇒ ≥1 test + `shadow_window_days>=7`
- truth_status must not exceed evidence_level on ladder
- **neural-learned-apply** pin: TESTED + SHADOW + trace_only + `production_apply_enabled=false` (+ capability JSON agree)
- report JSON: digest, git SHA, errors, warnings, signal count, timestamp

Report artifact: `_ops/state/adr-033/reports/signals-registry-validate.json`

## Test results (local)

```
validate_signals_registry.py → ok=true, errors=0, signals=9 (1 warning: kalman evidence dir absent)
test_signals_registry_schema.py → 7/7
test_registry_semantic_validator.py → 10/10
```

### Semantic negative cases covered

| Case | Result |
|---|---|
| YAML realistic | pass |
| duplicate ID | fail |
| diagnostic may_gate=true | fail |
| SPEC_NOT_BUILT with code path | fail |
| SHADOW effect without rollback | fail |
| ARMED without 7-day window | fail |
| neural production_apply_enabled=true | fail |
| missing implementation path | fail |
| missing test path | fail |

## Temporary invariants (remain locked)

```
OCTOPUS_NEURAL_LEARNED_APPLY=0
OCTOPUS_NEURAL_PROTECTIVE_PROPOSAL=1
neural-learned-apply.evidence_level=SHADOW
neural-learned-apply.authority.allowed_effect=trace_only
neural-learned-apply.authority.may_gate=false
neural-learned-apply.production_apply_enabled=false
```

Re-arming APPLY=1 requires: new ADR + 7-day artifact + chaos/replay tests + **explicit owner approval** (not local green alone).
