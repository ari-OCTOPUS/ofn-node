# ADR-034 A+B Evidence — 2026-08-11

Owner vote applied: **A now**, then **B demotion**. Stage 2–3 registry/schema deferred until after B.

## Capability truth (post-containment)

| Field | Value |
|---|---|
| capability_id | neural-learned-apply |
| truth_status | TESTED |
| evidence_level | SHADOW |
| allowed_effect | trace_only |
| may_gate | false |
| may_mutate_ledger | false |
| may_trigger_tool | false |
| production_apply_enabled | false |
| containment_flag | `OCTOPUS_NEURAL_LEARNED_APPLY=0` |
| proposal_flag | `OCTOPUS_NEURAL_PROTECTIVE_PROPOSAL=1` |

Record: `_ops/capabilities/neural-learned-apply.json`

## A acceptance (5 checks)

| # | Check | Result | Evidence |
|---|---|---|---|
| 1 | neural_beat / nociceptor / BCM still snapshot/trace | PASS | BCM/learned tests in `test_neural_loop_close.py`; PainAssessment JSONL via `emit_pain_assessment` when PROPOSAL/SHADOW |
| 2 | `protective_halt` / `_protective_skip` not from neural trigger | PASS | `organism.py` / `brain_worker.py` demoted; `test_adr034_neural_demote.py::t_organism_brain_cannot_neural_skip` |
| 3 | no new `protective_skip` write from neural path | PASS | neural sets `protective_proposal` + `pain_assessment` only (`protective_mode: false`) |
| 4 | pain > threshold → proposal / SHADOW_ALERT only | PASS | `t_high_pain_proposal_only`; organism alerts `SHADOW_ALERT neural:` |
| 5 | replay deterministic; zero external side effect; no control mutation | PASS | `t_replay_deterministic_zero_control_mutation`; halt only via `request_protective_halt` + PolicyGate |

**If any had failed:** remain BLOCKED; do not re-arm APPLY. All passed → B demotion accepted for code path.

## B Definition of Done

| Criterion | Status |
|---|---|
| Immutable `PainAssessment` with pain, components, status, reason_codes, trace_id | DONE — `_ops/neural/pain_assessment.py` |
| Threshold → `protective_proposal` only; no halt/skip/state write from neural | DONE — `wiring.emit_pain_assessment` / `protective_override` |
| Executable `protective_halt` only via PolicyGate (approval, kill switch, store) | DONE — `wiring.request_protective_halt` + `PROTECTIVE_CONTROL_POLICY` |
| organism / brain_worker cannot convert neural → skip | DONE |
| Tests: high-pain, NaN, store-down, kill-switch, replay, APPLY deprecated | DONE — `test_adr034_neural_demote.py` (+ updated frontier/organism/truthmap/hebbian/neural_loop) |
| `OCTOPUS_NEURAL_LEARNED_APPLY=1` no longer means direct apply | DONE — deprecated; use `OCTOPUS_NEURAL_PROTECTIVE_PROPOSAL` for shadow fold |

## Tests run (local, not registered in WORKLOCK / run_all)

```
test_adr034_neural_demote.py — 10/10
test_organism_protective.py — 9/9
test_neural_loop_close.py — apply path updated — green
test_frontier.py — protective suite updated
test_truthmap_fixes.py — P3 updated
test_hebbian_eventclock.py — ceiling/APPLY semantics updated
```

## Schedule (unchanged owner order)

1. ~~A / containment flag~~ **DONE**
2. ~~B / demotion + tests~~ **DONE (code)**
3. Stage 2–3 / registry, schema, semantic validator — **NEXT**
4. WORKLOCK proposal + owner approval — **after Stage 2–3**

## Non-claims

- No AGI / awareness / EFE claims.
- No WORKLOCK registration of new suites.
- BCM / Hebbian / Nociceptor modules not deleted — observation preserved.
- Live `flags-loaded-*.json` snapshots may lag until process restart reloads `OCTOPUS-flags.cmd`.
