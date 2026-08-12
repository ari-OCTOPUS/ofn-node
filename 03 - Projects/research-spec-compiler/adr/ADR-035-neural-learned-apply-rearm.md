# ADR-035 — Re-arm NEURAL_LEARNED_APPLY (production protective apply)

- **Status:** ACCEPTED — owner verdict 2026-08-12 («هردو»: flag=1 + apply اجرایی)
- **Date:** 2026-08-12
- **Supersedes (partial):** ADR-034 containment of `OCTOPUS_NEURAL_LEARNED_APPLY=1`
- **Preserves from ADR-034:** `PainAssessment` immutable record · `request_protective_halt` PolicyGate path · learned_pressure **cap** · effect-shadow JSONL
- **Evidence:** `_ops/state/adr-033/reports/ADR-035-REARM-EVIDENCE.md`
- **Capability record:** `_ops/capabilities/neural-learned-apply.json`

## Decision

Owner requested **both**:
1. Set `OCTOPUS_NEURAL_LEARNED_APPLY=1`
2. Restore **executable** neural protective apply (organism/brain_worker may set `protective_skip` when neural returns executable halt)

ADR-034 made `APPLY=1` a no-op for execution (proposal/SHADOW only). That is superseded for the apply path.

## Capability Truth (post re-arm)

| Field | Value |
|---|---|
| Capability | neural-learned-apply |
| truth_status | TESTED |
| evidence_level | ARMED (ladder; production apply on) |
| Feature flag | `OCTOPUS_NEURAL_LEARNED_APPLY=1` |
| Proposal flag | `OCTOPUS_NEURAL_PROTECTIVE_PROPOSAL=1` (still used for assessment fold + traces) |
| production_apply_enabled | **true** |
| allowed_effect | gate_internal |
| may_gate | **true** (non-essential beat work only via `protective_skip`) |
| may_mutate_ledger / may_trigger_tool / external | false |

## Dual-mode contract

| Flag | Behavior |
|---|---|
| `APPLY=0` | ADR-034 semantics: `protective_proposal` / SHADOW only · `executable=false` |
| `APPLY=1` | learned_pressure (capped) folds into pain · pain>thr or critical → `protective_halt` · `override=true` · `executable=true` · organism/brain_worker set `protective_skip` |

## Still fail-closed

- Learned pressure uses **capped** value only.
- `request_protective_halt` remains PolicyGate-only (approval + kill-switch + store) for *explicit* control-plane halt requests — neural skip is beat-local, not that API.
- No EXTERNAL_SEND / LIVE-ENABLED / money from this path.
- Rollback: set `OCTOPUS_NEURAL_LEARNED_APPLY=0` in `OCTOPUS-flags.cmd` + restart.

## Non-claims

No AGI / consciousness claims. Skip only pauses non-essential work for the beat.

## Sources

- `_ops/wiring.py` (`emit_pain_assessment`, `protective_override`)
- `_ops/organism.py`, `_ops/brain_worker.py`
- `_ops/OCTOPUS-flags.cmd`
- Tests: `test_adr035_neural_rearm.py` (+ updated ADR-034 suite for dual-mode)
