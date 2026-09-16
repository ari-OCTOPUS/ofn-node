---
type: report
project: "[[04 - Architect System/architect/PROJECT]]"
status: ready
tags: [octopus, edges]
created: 2026-08-29
updated: 2026-08-29
created_by: agent
---

# TOP-EDGES — E1 / E2 / E8 (copied + filled from MISSING-EDGES)

Observer: node 191 `DESKTOP-KA9RFN5` / `192.168.0.191` (session label 180 was wrong).  
Target: node 138 `DietPi` / eth0 `192.168.0.138`. Observed 2026-08-29.

## E1 — runtime provenance (was: restart receipt vs `c803dee`)

| Field | Value |
|---|---|
| producer | `systemd` `ofn.service` + git worktree `/home/ari/ofn` |
| consumer | owner / auditor (this receipt) |
| source | `systemctl show` · `/proc/$PID/{cwd,exe,cmdline}` · `git -C cwd` |
| transport | SSH 191→138 read-only |
| current evidence | PID `1351408` active since `2026-08-27 11:33:40 AEST`; cwd `/home/ari/ofn`; cmdline `python3 -m ofn.run`; HEAD `68813370c726a1a650a7cb2fb99207c300358db9`; branch `integration/138-business-spine-20260828` |
| missing proof | in-process module objects vs disk (import check was from a **new** interpreter). Process environ had no `PYTHONPATH`; imports work via cwd on `sys.path`. |
| smallest connection | this evidence pack; do **not** restart automatically |
| test that proves closure | PID≠0 + cwd expected + cmdline `-m ofn.run` + import hashes == `sha256sum` + no relevant mtime after `ActiveEnterTimestamp` |
| E0 result | **RUNTIME_BYTES_UNPROVEN_RESTART_REQUIRED** for spine adapters (mtime 2026-08-28 after start). `run.py` / `http_api.py` / `cockpit_v2_read_model.py` / `ledger.py` / `outbox.py` mtimes are **before** start. `c803dee` is **not** the 138 tree. |

## E2 — queue identity (Cockpit V2 vs decide/outbox)

| Field | Value |
|---|---|
| producer | mesh queue files (`_collect_queue`) **and** OFN `Outbox` (`owner_queue`) |
| consumer | Cockpit V2 GET `/api/v2/owner/queue` vs legacy `POST /api/v1/decide` |
| source | `cockpit_v2_read_model.py:_project_queue_row` (`id=message_id`) · `node.py:owner_queue` (`id=tenant:idem`) · `outbox.py` scoped insert |
| transport | HTTP loopback `:8794` (Host-gated) + SQLite outbox |
| current evidence | offline P1 CONFIRMED two ID spaces; live probe this run (see `v2-queue-http.txt` / `outbox-recent-ids.txt`) |
| missing proof | one shared `idem_key` equal across V2 item, `owner_queue()`, outbox row, panel item |
| smallest connection | add OFN outbox projection into existing ReadModel (`business_outbox` or `_collect_queue`); no new API |
| test | equality of id, idem_key, run_id, payload hash, decision state, source timestamp — **IDs not counts** |

## E8 — OwnerDecision vertical slice (existing only)

| Field | Value |
|---|---|
| producer | `OwnerDecision` (12 fields) @ `ofn/adapters/owner_decision.py` |
| consumer | `fake_executor` (tests) · **should** be `outbox.approve_manual` + receipt |
| source | `6881337` adapters; `run.py` / `http_api.py` do **not** import them |
| transport | in-process fake JSONL in tests; production decide path ignores them |
| current evidence | files on disk 138 (sha in `source-sha256.txt`); mtime after process start; process started before those files existed |
| missing proof | live or shadow: OwnerDecision → existing outbox → fake/shadow executor → ACK → receipt |
| smallest connection | translate `owner_decide` success into `OwnerDecision`; keep `POST /api/v1/decide` |
| test | existing `tests/test_owner_decision_fake.py` + `tests/test_executor_fake.py` + `tests/test_witness_mint.py` (hermetic) |
