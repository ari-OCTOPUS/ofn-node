---
type: report
project: "[[04 - Architect System/architect/PROJECT]]"
status: ready
tags: [octopus, e0, provenance]
created: 2026-08-29
updated: 2026-08-29
created_by: agent
---

# CHECKPOINT — E0 live provenance + E1/E2/E8

```
RESEARCH_VERDICT=REUSE_AUDIT_COMPLETE_OFFLINE
AUDIT_KIND=REUSE_ONLY
REPO_STATUS=READ
RUNTIME_PROBED_TODAY=1
IMPLEMENTATION_VERIFIED=0
DEFECT_FIXED=0
READY_TO_PROCEED_RUNTIME_PROVENANCE=1
MARK_AS_FIXED=NO

VERDICT=RUNTIME_BYTES_UNPROVEN_RESTART_REQUIRED
PID=1351408
CWD=/home/ari/ofn
BRANCH=integration/138-business-spine-20260828
HEAD=68813370c726a1a650a7cb2fb99207c300358db9
WORKTREE_CLEAN=false
TRACKED_SOURCE_CLEAN=true
IMPORT_ORIGINS_MATCH=true
SOURCE_CHANGED_AFTER_START=true
TOP_EDGES_DEFINED=3
PARITY_IDS_MATCH=NOT_RUN
SHADOW_ACK=true
SHADOW_RECEIPT_SHA=NOT_RUN
TESTS_PASSED=37
TESTS_FAILED=0
RUNTIME_CHANGES=0
EXTERNAL_EFFECTS=0
EVIDENCE_DIR=/home/ari/ofn/06-EVIDENCE/runtime-provenance-20260828T230743Z
VAULT_COPY=06-EVIDENCE/OCTOPUS-REUSE-AUDIT-2026-08-29/runtime-provenance-20260828T230743Z
NEXT=do-not-auto-restart; obtain owner session for GET /api/v2/owner/* then compare one studio:idem to V2 queue id
```

## Identity

Claimed session role was board 180. Live this host: hostname `DESKTOP-KA9RFN5`, Wi-Fi `192.168.0.191`. Ethernet disconnected. Vantage for this probe: **191 → 138 SSH**. 138 eth0 `192.168.0.138` `DietPi`. Tunnel `127.0.0.1:8791-8796` LISTEN on 191.

## Why not PROVEN

`ofn.service` started `2026-08-27 11:33:40 AEST` (same PID as 28 Aug audit).  
HEAD is `6881337` (28 Aug 11:05). New spine files mtime 28 Aug ~10:53–10:54 — **after** start. Process cannot have loaded `owner_decision` / `witness_mint` / `fake_executor`.  
`run.py`, `http_api.py`, `cockpit_v2_read_model.py` mtimes are **before** start; disk hashes match a fresh import from `/home/ari/ofn`. That is **not** a memory dump of PID 1351408.

First import check (no cwd/`PYTHONPATH`) was a false UNAVAILABLE. Retry with `PYTHONPATH=/home/ari/ofn` matched `sha256sum`.

Worktree porcelain: `?? 06-EVIDENCE/` only (this probe). Tracked sources clean. `diff --check` empty.

## Line counts (exact commands)

`physical=len(splitlines())` · `nonempty=sum(1 for ln if ln.strip())`

- `cockpit_v2_read_model.py`: physical **2966** · nonempty **2775** · bytes **109911**
- `http_api.py`: physical **1844** · nonempty **1731** · bytes **99192**

## E2 live

`GET /api/v2/owner/version|queue` with `Host: panel.master-painting.com` → **401**. No session.  
Outbox (ids only): **25** rows, all `manual_completed`, form `studio:<hex>`. Zero pending. ID compare V2↔outbox **NOT_RUN**.

## E8 shadow

`unittest` `test_owner_decision_fake` + `test_executor_fake` + `test_witness_mint` + `test_business_source_export`: **37 OK** in 0.083s. No production write. Receipt sha of a live chain: NOT_RUN.

## Tracked backups (not runtime)

`TRACKED_BACKUP_NOT_RUNTIME` — do not delete this run:

- `http_api.py.bak-assistant-20260806-004412`
- `http_api.py.bak-delete-upload-20260807-114125`
- `studio_assistant.py.bak-saba-surgery-20260806-203317`
- `studio_store.py.bak-assistant-20260806-004412`
- `studio_store.py.bak-category-20260805-225353`

## Forbidden still

No new subsystem. No auto restart. No Mark as fixed.
