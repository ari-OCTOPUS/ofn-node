# Controlled capability awakening preflight

Captured before source, registry, service, or live-database changes.

- Captured at: `2026-08-25T13:04:24Z`
- Gate: `GATE-CONTROLLED-CAPABILITY-AWAKENING-15MIN`
- Decision: `APPROVED_WITH_CONDITIONS`
- Approval scope: `ONE_USE`
- Approval used: `false`
- Branch: `feat/phase3-completion`
- Expected starting commit: `65258776598c6eb43bb49dacb5208c42a65084b4`
- Verified Git/source commit: `65258776598c6eb43bb49dacb5208c42a65084b4`
- Tracked Python/shell source-tree SHA-256: `3bb50659f37a2eac9c0cb75f8f5106ab46567134871d54ac2bb35af5a4800ee1`
- Organism PID: `38843`
- Llama PID: `527`
- Soak PID: `38871`
- Gateway PID: `641`
- Organism unit: `active/running`, `NRestarts=0`
- Soak unit: `active/running`, `NRestarts=0`

## Configuration

- Combined organism unit/drop-in/start-script SHA-256: `422bf2930c7a523732bbdb13c89113716e999a78c4d6b64567b60ed74ce896ca`
- Unit SHA-256: `ac0b4002240ab16e2c6b2f02e13ccf3b388d337c30172f947bfabd1996fbeb10`
- Security drop-in SHA-256: `69b034fb5f6487d0247ac7baf8a2ea55838cc113ce06374aa684b4728d84d62b`
- Start script SHA-256: `8e0dfa2408fbc25a4c1f94a59fafdd0f32a22fcf1abd8eb3a1809df8992fc22d`
- `OCTOPUS_GET_PURE=1`
- `OCTOPUS_REQUIRE_LAN_TOKEN=1`
- `OCTOPUS_LEARN_EXTERNAL=0`
- Live response: `autonomy_state=PROPOSE_ONLY`, `external_api=DISABLED`
- `WAVE0_OBSERVE_ONLY=true` remains the source/runtime contract.
- LAN token path: `/etc/octopus/lan-token`; mode/owner: `0600 root:root`. Token content was not emitted.
- Unauthenticated LAN data request: HTTP `401` (`UNAUTHENTICATED_LAN_ACCEPTED=false`).

## Registry

- Existing capability registry: `ABSENT`
- Registry state before gate: approved internal capabilities are treated as `LOCKED`, except the already disconnected/non-executable Active Inference implementation, treated as `SHADOW`.
- No live schema or identity-format change is authorized.

## Database and identity

- Live schema marker: `phase3-skin-1`
- SQLite `PRAGMA integrity_check`: `ok`
- SQLite `PRAGMA quick_check`: `ok`
- Identity head at database snapshot: sequence `250`, hash `d037f7887ebdc514e4227146f7ab7817f73d3c6fa92bc4d0d52c7f62bfc4ae52`
- Independent identity verification: `valid=true`, scope `INTERNAL_HASH_CHAIN_CONSISTENCY`
- Event head: node sequence `461`, event id `cb283fb0ee44bfd110cb61000a04352b`, hash `ffb1e3f2d7481055004fb029d390fd0977e79a7da5d7b274eea1d86bd1233f40`
- Episode count: `461`
- Memory receipt count: `533`
- Decision evidence count: `388`
- Self-model version: `89`
- WAN fetch count: `0`
- Memory future-use total: `0`
- Executable evidence total: `0`

Counts may advance from ordinary heartbeats after this timestamp; this block is the immutable gate baseline.

## Resources

- Root available: `7016050688` bytes (`6.53 GiB`)
- Root use: `89%`
- RAM available: `2292670464` bytes (`2186 MiB`)
- SoC temperature: `28692 mC`
- Disk requirement (`>=5 GiB` and root `<92%`): `PASS`
- RAM requirement (`>=350 MiB`): `PASS`
- Thermal margin requirement: `PASS`

## Watcher precondition

The previous bounded checkpoint watcher had exited after the earlier homogeneous soak. No `checkpoint-watcher.py` process was running at the initial snapshot, so this precondition was initially unsatisfied and is not represented as passing. The approved remediation is to start one explicitly timeout-bounded watcher before implementation/deployment and require both a live process and a fresh heartbeat throughout the canary. A bad receipt remains quarantine/report-only.

Remediation at `2026-08-25T13:05Z`: started PID `41212` under GNU `timeout --signal=TERM 3600s`. The first observed heartbeat was fresh (`12.581s` old), `running=true`, `status=ok`. This satisfies the watcher precondition only while both the bounded process and fresh heartbeat continue to be observed.

## Preflight disposition

All immutable safety and integrity checks passed. `checkpoint watcher running` requires the bounded remediation above before capability transitions or live execution. If that remediation fails, final status must be `BLOCKED_PRECONDITION` with `ACTION_EXECUTED=false`.
