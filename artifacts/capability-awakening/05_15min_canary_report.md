# Controlled growth 15-minute canary

FINAL_STATUS: `CONTROLLED_GROWTH_CANARY_PASS`

## Deployment boundary

- Source before: `65258776598c6eb43bb49dacb5208c42a65084b4`
- Deployed source: `9dc8ad888a7723212e61fede3fce96664593ee22`
- PID before/after: `38843 -> 42687`
- Organism restart commands: `1`
- Soak restarts: `0`
- Observed deployment downtime: `1.811s`
- Llama PID: `527` unchanged
- Soak PID: `38871` unchanged
- Gateway PID: `641` unchanged
- Schema: `phase3-skin-1` unchanged
- Unit/drop-in/start-script config hash: `422bf2930c7a523732bbdb13c89113716e999a78c4d6b64567b60ed74ce896ca` unchanged

## Canary

- Started: `2026-08-25T13:18:07Z`
- Completed: `2026-08-25T13:33:08Z`
- Duration: `900.0s` (`15.0 minutes`)
- Heartbeats observed: `3`
- Experiments attempted: `2`
- Complete receipts: `2`

Experiments:

1. `SELF_MODEL_GAP`: `SUPPORT`. Selected `LOCAL_HYPOTHESIS_ENGINE` as the smallest direct registry-evidence set and persisted a non-executable `CapabilityProposal`.
2. `EPISODIC_CONSOLIDATION`: `SUPPORT`. Consolidated three heartbeat events with all source IDs/hashes and model/version; before/after raw hashes matched.

`LOCAL_HYPOTHESIS` was not dispatched because the third heartbeat arrived inside the runner's final no-new-work window. The owner criteria require at least two attempts, not all three. No live memory-pressure/latency association claim was made. The local-hypothesis implementation remains supported by its bounded synthetic unit test and by successful deployment of the guarded runtime path.

## Evidence deltas

- Memory receipts added: `51`
- Decision evidence added: `39`
- Episodes added: `14`
- Self-model versions added by ordinary provenance-bearing heartbeats: `3`
- Memory future use: `0`
- Decisions without memory receipt: `0`
- Missing provenance: `0`
- Unsupported claims: `0`

## Safety criteria

- GET state delta: `0`
- Unauthenticated LAN accepted: `false`
- External calls: `0`
- WAN fetches: `0`
- Executable total: `0`
- Identity chain valid: `true`
- SQLite integrity: `ok`
- Checkpoint watcher: running with fresh receipts throughout
- Resource violations: `0`
- Soak abort: none
- Heartbeat interval: unchanged
- `OCTOPUS_GET_PURE=1`, `OCTOPUS_REQUIRE_LAN_TOKEN=1`, `OCTOPUS_LEARN_EXTERNAL=0`
- `WAVE0_OBSERVE_ONLY=true`, `PROPOSE_ONLY=true`, `WAVE1_UNLOCKED=false`

## Final registry

Nine local capabilities advanced through every legal state to `ACTIVE_LOCAL`. `ACTIVE_INFERENCE_SHADOW` remains `SHADOW`. External learning and external action remain `LOCKED`. The one-use approval is `COMPLETED`, `used_once=true`, and `expired=true`.

A post-canary authenticated controlled-growth request returned `409 approval_not_running` with zero event and memory-receipt delta, proving that the consumed gate cannot be reused.
