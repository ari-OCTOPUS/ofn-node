# Phase 3 — PHASE 1 RECOVERABILITY

PHASE1_RECOVERABILITY: PASS
METHOD: SQLite Online Backup API (`Connection.backup`, pages=32, sleep=0.25)
SOURCE: `file:/opt/octopus/lab/lab-data/organism.db?mode=ro` + `PRAGMA query_only=ON`
LIVE_DATABASE_MODIFIED: false

## Backup

- destination: `/opt/octopus/lab/lab-data/backups/organism-phase3-online-20260825T104854Z.db`
- size_bytes: 1069056
- mode: 0600 (new file only; live files were not chmod'd)
- integrity_check (destination): ok
- quick_check (destination): ok
- table_set_equal_to_live: true (18 tables)
- elapsed_s: 0.017 (source main file ~1 MiB; WAL remained on live)

## Count comparison

See `backup_table_counts.csv`. Live counts can move between preflight and backup because soak/heartbeats continue. Deltas recorded; no live writes from this backup process.

## Restore rehearsal

- copy: `/opt/octopus/lab/lab-data/backups/organism-phase3-restore-rehearsal-20260825T104854Z.db`
- identity_ledger rows: 205
- events rows: 354
- rehearsal wrote `_rehearsal_marker` **only on the copy**
- live `sqlite_master` still has no `_rehearsal_marker`

## Exclusions (not copied)

- `/opt/octopus/models`
- `/opt/octopus/venv`
- `/opt/octopus/runtime/llama.cpp-src`
- `/opt/octopus` full tree

## Manifest

`backup_manifest.csv`
