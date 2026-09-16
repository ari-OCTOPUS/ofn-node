# WORKLOCK Proposal — Stage 2–3 suites

- **Status:** APPROVED + APPLIED 2026-08-11 (owner vote; append-only)
- **Evidence:** `_ops/state/adr-033/evidence/EVIDENCE_MANIFEST.json`
- **Preflight:** `worklock-preflight.json` + `worklock-preflight-suites.log`

## Suites to add (minimum)

| Suite file | Why |
|---|---|
| `test_adr033_control_plane.py` | PolicyGate / evidence plane |
| `test_approval_state.py` | approval SM fail-closed |
| `test_signals_registry_schema.py` | JSON Schema registry gates |
| `test_registry_semantic_validator.py` | Stage 2–3 semantic rules + report |
| `test_kalman_shadow_pipeline.py` | shadow period sensor |
| `test_bcm_hebbian_shadow_e2e.py` | BCM/Hebbian shadow e2e |
| `test_nociceptor_chaos_shadow.py` | pain chaos shadow |
| `test_adr034_neural_demote.py` | ADR-034 A+B demotion pin |

## Explicit non-goals of this proposal

- No registration without owner approval
- No re-arm of `OCTOPUS_NEURAL_LEARNED_APPLY=1`
- No treating `request_protective_halt` as a signal

## Owner approval checklist

- [ ] Read `STAGE-2-3-EVIDENCE.md`
- [ ] Confirm validator report `ok=true`
- [ ] Approve adding the eight suites to `run_all.py`
- [ ] Assign WORKLOCK lane owner for the `run_all.py` edit

## Suggested commit message (after approval)

```
agent-checkpoint: WORKLOCK register Stage 2-3 registry + ADR-034 demote suites
```
