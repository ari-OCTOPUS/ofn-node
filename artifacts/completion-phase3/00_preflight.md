# Phase 3 — PHASE 0 PREFLIGHT

PHASE3_STARTED: true
PHASE0_PREFLIGHT: PASS
SCAN_STARTED_UTC: 2026-08-25T10:47:18Z
MEGAPROMPT_FILE: MEGAPROMPT_FILE_NOT_FOUND
MEGAPROMPT_NOTE: Execution proceeded from owner command "همه چیو اجرا کن" plus the Phase 3 kickoff already in chat. File OCTOPUS_BOARD_COMPLETION_MEGAPROMPT_PHASE3_FA.md was not on disk.

## Disk

- filesystem: `/dev/mmcblk0p1` on `/`
- total_bytes: 61326831616
- used_bytes: 51772366848
- available_bytes: 7025836032 (~6.54 GiB)
- use_percent: 89
- inodes_used_percent: 3
- halt_rule: available < 5 GiB OR use >= 92%
- halt_triggered: false

Backup budget before 5 GiB floor: ~1.54 GiB. Planned SQLite backup << 16 MiB. No full copy of models/venv/llama.cpp-src.

## Git (at preflight)

- repo: `/opt/octopus/lab`
- branch: `experiment/board-life-001`
- HEAD: `50f31dbb244912ddf9dc1cb237bb6655a673a05c`
- remote: none
- tracked: 40
- status porcelain lines: 139
- untracked (??): 127
- modified/other tracked dirty: 12
- ignored listed: 91

## Live processes (command lines without env dumps)

- `octopus-llama-lab` PID 527 NRestarts=0 started 2026-08-25T05:30:08Z  
  exe: `/opt/octopus/runtime/llama.cpp-f280b26/bin/llama-server.f280b26`  
  listen: `127.0.0.1:8081`
- `octopus-organism-lab` PID 12748 NRestarts=0 started 2026-08-25T08:52:03Z  
  cmdline: `python3 -m ofn.organism.runtime.app --db /opt/octopus/lab/lab-data/organism.db --host 127.0.0.1 --port 8090 --heartbeat-interval 180`  
  cwd: `/opt/octopus/lab`
- `octopus-soak-lab` PID 4235 NRestarts=0 started 2026-08-25T06:49:18Z
- `octopus-afferent-lab` PID 4218 NRestarts=0 started 2026-08-25T06:49:16Z
- `octopus-gateway` PID 641 NRestarts=0 listen `0.0.0.0:8780`

Listeners: `127.0.0.1:8081`, `127.0.0.1:8090`, `192.168.0.180:8090`, `0.0.0.0:8780`. No `:8091`.

## Source hashes (disk)

- `ofn/organism/__init__.py` sha256 `1bd50fb91c5e534cbf558fd3d30e9bda9d994fbc8d201fbf27c9c4fabed2bfae` version `0.6.0`
- `ofn/organism/persistence/db.py` sha256 `2e4900c9ddefdf216bb56de43a292971c85b767c08ab0691df937879c66912f6` mtime 2026-08-25T08:58:38Z
- `ofn/organism/cognition/wan.py` sha256 `ae6fcc383bd450510d9090d3e7d8fc9630a986933cfab995f6fe96d2619e9acb` mtime 2026-08-25T08:59:23Z
- `ofn/organism/runtime/app.py` sha256 `beb16c55c2355bbbaa8407b42641287571836180441ebf3b3f71fcf28ff5ccdc`
- `ofn/organism/runtime/life_cycle.py` sha256 `26a95c1b7fcd624965c262d1f5624eed4900288ea426784372b8a6a532109fce`
- `ofn/organism/memory/episodic.py` sha256 `dc6b852d7ce8d67ac1f6c157d150abb49d3034263fd2b1b5ad40688fe5103b7f`
- `bin/start-organism.sh` sha256 `64bcfc0f84d2485e94e67d794631414a03a8252f4b859a739001f6db17caf272`

## Source / runtime mismatch

- live process start: 2026-08-25T08:52:03Z (PID 12748)
- `db.py` and `wan.py` on disk are newer than that start
- live SQLite has no `wan_fetches` table; disk `SCHEMA` defines it
- SOURCE_RUNTIME_MATCH: false
- Owner Gate required before restart/deploy of the running process

## SQLite live (read-only URI)

- db 1056768 B mode 0644
- wal 4120032 B mode 0644
- shm 32768 B mode 0644
- journal_mode=wal synchronous=FULL (2)
- integrity_check=ok
- quick_check=ok
- foreign_key_check violations=0
- tables=18 (no wan_fetches)
- counts snapshot: events=354 episodes=354 outbox=354 identity_ledger=205

## Identity

Independent verifier `/opt/octopus/lab/bin/verify-identity-chain.py`:

- valid: true
- entries: 205
- scope: INTERNAL_HASH_CHAIN_CONSISTENCY
- external_anchor: null

## Soak

`/opt/octopus/lab/evidence/SOAK-RESULTS.json` at preflight:

- running: true
- abort: null
- samples: 238
- age_seconds: 14253
- last health/organism HTTP 200 (existing soak process; this mission did not start soak)

## Dependencies absent (expected)

- vllm: absent
- nvidia-smi: absent
- cbor2: absent
- pymdp: absent

## Safety halt checks

- BLOCKED_SAFETY_DISK: no
- BLOCKED_INTEGRITY: no

## Next

PHASE 1 RECOVERABILITY: SQLite Online Backup API only; no live DB mutation; no full tree copy.
