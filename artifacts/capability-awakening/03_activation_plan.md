# One-use activation plan

Gate: `GATE-CONTROLLED-CAPABILITY-AWAKENING-15MIN`  
Decision: `APPROVED_WITH_CONDITIONS`  
Scope: `ONE_USE`

## Preconditions

Use the immutable baseline in `00_preflight.md`. Before consuming approval, recheck source/branch, live schema, security flags, identity, SQLite, disk, RAM, thermal state, service PIDs/restarts, unauthenticated LAN rejection, GET purity, external-learning lock, and a live timeout-bounded checkpoint watcher.

Any unsatisfied precondition produces `ACTION_EXECUTED=false` and `FINAL_STATUS=BLOCKED_PRECONDITION`.

## Legal state sequence

The registry was created at `LOCKED` for nine local capabilities and `SHADOW` for Active Inference. Forward activation is:

`LOCKED -> SHADOW -> TESTED -> CANARY -> ACTIVE_LOCAL`

No transition is skipped. `ACTIVE_INFERENCE_SHADOW` remains `SHADOW` throughout. External learning and external action remain `LOCKED`.

The `SHADOW` transition follows source/inventory review. The `TESTED` transition requires the complete offline organism suite. The one-use approval is consumed only when the tested registry is moved to `CANARY` with one execution ID.

## Deployment

- Commit the tested source, tests, registry, and pre-canary artifacts locally.
- Change no live schema, identity format, token, port, firewall, heartbeat interval, or systemd configuration.
- Restart `octopus-organism-lab` exactly once after the source commit.
- Do not restart soak, llama.cpp, gateway, Cellframe, or SSH.
- Require a new organism PID, healthy loopback/LAN behavior, identity continuity, SQLite integrity, the same security flags, and downtime below 60 seconds.
- If the first restart fails, do not retry. Disable the canary by returning the registry to `TESTED`; use the separately authorized rollback restart only if restoring the prior source is necessary.

## Controlled canary

Duration is 15 minutes, with the existing heartbeat interval unchanged. A newly committed real heartbeat event may authorize at most one experiment. The execution attempts, in order, no more than:

1. `SELF_MODEL_GAP`
2. `EPISODIC_CONSOLIDATION`
3. `LOCAL_HYPOTHESIS`

Each experiment performs the required twelve-step growth loop. Every database write is made by the live organism runtime through the memory gate/event kernel/episodic writer. The canary runner performs only read-only monitoring, authenticated endpoint calls, and bounded artifact writes under `/opt/octopus/lab`.

The checkpoint watcher is externally bounded by GNU `timeout`; both its process and fresh heartbeat are required on every sample.

## Abort handling

On any abort condition, stop dispatching experiments immediately. Preserve all result and failure evidence. Return activated registry entries to `TESTED` with an explicit rollback/quarantine history record; expire the one-use approval. This config rollback disables further controlled-growth calls without a restart.

Only if the deployed source itself must be removed may one rollback organism restart be used. No rollback deletes post-deploy cognitive data.

## Success handling

After at least 15 minutes, at least three heartbeats, at least two complete experiments, and every stated safety criterion passing:

- advance the nine local capabilities from `CANARY` to `ACTIVE_LOCAL`;
- leave Active Inference at `SHADOW`;
- leave external capabilities locked;
- mark the one-use approval `COMPLETED`, `used_once=true`, `expired=true`;
- set `READY_FOR_NEXT_OWNER_DECISION=true`;
- emit the required reports and final controlled-growth receipt.
