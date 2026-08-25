# Phase 3 P2 — Recoverability

LOCAL_DATABASE_BACKUP: PASS
RESTORE_REHEARSAL: PASS
LIVE_DATABASE_MODIFIED: false
BLOCKED_SAFETY_DISK: false

## Space

- available_bytes at backup: 7021625344 (~6.54 GiB)
- organism db+wal ~5.2 MiB
- budget 2x + 8 MiB ~18.9 MiB
- floor 5 GiB would remain after backup

Excluded from copy: models, venv, llama.cpp build, Cellframe, full `/opt/octopus`.

## Source manifest

`02_source_manifest.csv` — 90 files, 509787 bytes under `ofn/`, `bin/`, `docs/`, `scripts/`, `systemd/`. SHA-256 per file. No GGUF, no venv, no live DB.

## SQLite Online Backup

Receipt: `02_database_backup_receipt.json`

- method: `Connection.backup` pages=32 sleep=0.25
- source: `file:/opt/octopus/lab/lab-data/organism.db?mode=ro` + `query_only=ON`
- destination: `/opt/octopus/lab/lab-data/backups/organism-phase3-p2-20260825T111133Z.db` mode 0600
- integrity_check: ok
- tables_equal: true
- live vs backup counts: delta 0 on all 18 tables at backup instant (events=374)
- rehearsal copy wrote `_rehearsal_marker` only on the copy
- live sqlite_master has no `_rehearsal_marker`
