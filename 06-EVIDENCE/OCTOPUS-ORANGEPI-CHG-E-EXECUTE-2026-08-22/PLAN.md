# PLAN — Orange Pi CHG-E EXECUTE (reversible cold evidence archive)

**Authorization / Token:** `OCTOPUS-ORANGEPI-CHG-E-20260822`  
**Board:** sensorium-opi5pro @ 192.168.0.182  
**Executor:** sensoriom  
**Written (AEST):** 2026-08-22T19:10:00+10:00  
**mutate_device:** true  
**Links:** ABD package complete (A→D→B PASS); E was deferred

## Problem

BOOTING / evidence corpus historically ~**4.7G** (indexes + cold windows). ABD Path A deferred heavy load; full **E compaction** was out of ABD package. Owner now authorizes **CHG-E execute**: shrink cold weight without destroying recoverability.

## Goal

1. **Reversible archive** of **cold** evidence (~4.7G class).
2. **Keep hot set** online (active ledgers, READY-critical, recent windows).
3. **Index rebuild** after archive (consistent index; no silent hash rewrite).
4. **No casual truncate** of observations.


## Gate status: **BLOCKED_NEED_ARCHIVE_ROOT**

Do **not** invent ARCHIVE_ROOT or hot paths. Owner must supply before Step 2 archive mutate:

- `ARCHIVE_ROOT` — absolute path with free space >= cold payload + margin
- `HOT_EVIDENCE_ROOT` — live evidence store root
- `HOT_RETENTION_WINDOW` — what stays hot
- `DISK_FREE_TARGET` — free-space target
- `INDEX_REBUILD_COMMAND` (or confirmed sensoriom rebuild procedure)

Until then: package files are complete; **mutate archive is blocked**. Sensoriom may run **read-only inventory** only.
## Allowed change set

1. **Classify hot vs cold**
   - Hot: current prediction/other ledgers in use, active configs, recent untainted windows needed for READY, CHG-D repaired chain heads.
   - Cold: aged windows, superseded indexes, already-quarantined tainted copies, bulky historical evidence not required for READY.

2. **Reversible archive**
   - Create archive (tar/zst or board-standard) on sufficient free disk / external path.
   - Generate **sha256 manifest** of archived members + archive digest.
   - Only after manifest verify: remove/move cold originals from hot path.
   - Never delete without archive+manifest PASS.

3. **Keep hot set**
   - Do not archive live ledger heads or READY-critical store files.
   - Do not casually truncate observation streams.

4. **Index rebuild**
   - Rebuild indexes from remaining hot set (or documented rebuild tool).
   - Verify store opens / sensorium READY still healthy (WatchdogSec=180 from CHG-A).
   - No in-place hash rewrite of ledger entries.

5. **Receipts**
   - Sizes before/after, archive path, manifest digests, READY soak note, TO-LAPTOP ack.

## Explicitly forbidden

- Casual truncate; zero-fill; in-place hash rewrite; delete-without-archive; MQTT/PWM/legs; keys; Doctor auto-patch; torch; LAN:9101; WAVE0 unlock; laptop SSH mutate.

## Success criteria

- Cold ~4.7G class reduced via reversible archive.
- Hot set intact; READY stable; index consistent.
- Rollback path (restore from archive) documented and preferably spot-tested.

