# CHG-D — Prediction ledger append-only repair (seq 9024 / break 9025)

**Authorization:** `OCTOPUS-ORANGEPI-CHG-ABD-20260822` (package A+B+D)  
**Board:** sensorium-opi5pro @ 192.168.0.182  
**Executor:** sensoriom  
**Written (AEST):** 2026-08-22T16:53:45+10:00

## Problem (evidence)

- Duplicate **seq=9024** (two hashes, same `prev_hash`); **break_seq=9025**.
- HEAD frozen ~Aug 18; chain verify fails at break.
- Silent in-place hash rewrite is **globally forbidden**.

## Goal

Restore a verifiable append-only chain: quarantine the duplicate, continue from a consistent tip (new epoch if required), and prove with `verify_all_ledgers.py`.

## Allowed change set (append-only discipline)

1. **Freeze writers** that append to the broken ledger (coordinate with B2 mask if WM is a writer).
2. **Backup** ledger files + tips to a dated quarantine/backup dir; record sha256 of every file before mutation.
3. **Identify duplicate**: two entries with seq=9024, divergent hashes, shared prev_hash. Quarantine the non-canonical duplicate aside (copy out; prefer new active file or verified tip restore — prefer new-epoch file if continuity cannot be proven).
4. **Canonical tip**: choose the entry whose hash continuity matches pre-break majority / documented tip; record choice rationale in receipt (never silent).
5. If continuity cannot be honestly restored without rewrite: start a **new epoch** ledger file with `epoch_id` / genesis prev_hash documented; leave old epoch immutable in quarantine.
6. **NEVER** silent in-place hash rewrite of historical rows.
7. Re-run **`verify_all_ledgers.py`** (or board-equivalent path); require PASS (or documented epoch-split PASS).
8. Resume writers only after verify PASS.

## Explicitly forbidden during D

- in-place hash rewrite; casual truncate of observations store; zero-fill; deleting ledger without quarantine copy; forging seq continuity; C/E package work; actuator/MQTT/legs; Doctor auto-patch rewriting ledger hashes.

## Verification

- `verify_all_ledgers.py` PASS on active set.
- break_seq cleared or confined to quarantined immutable epoch.
- New appends get seq > tip with correct prev_hash.
- Receipt: before/after hashes, duplicate quarantine paths, epoch decision, verify stdout.

## Rollback

1. Stop writers.
2. Restore active ledger from pre-D sha256 backup.
3. Re-quarantine any new-epoch file created during failed repair.
4. Re-run verify (expect pre-D failure mode restored honestly).
5. Report FAIL; do not attempt hash rewrite quick fix.

## Success criteria

- Verifiable chain (same epoch repaired tip **or** clean new epoch); duplicate quarantined; verify_all PASS; no silent rewrite.
