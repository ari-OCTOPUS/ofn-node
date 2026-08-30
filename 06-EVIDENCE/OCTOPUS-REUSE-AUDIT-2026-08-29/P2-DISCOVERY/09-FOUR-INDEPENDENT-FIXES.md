---
type: report
project: "[[04 - Architect System/architect/PROJECT]]"
status: ready
tags: [octopus, defects, independent]
created: 2026-08-29
updated: 2026-08-29
created_by: agent
language: fa
sources:
  - "[[06-EVIDENCE/OCTOPUS-TELEGRAM-WEBAPP-PHASE0-2026-08-29]]"
  - "[[_ops/flag_drift.py]]"
---

# 09 — Four independent fixes (discovery only)

No patches in this phase. All four are **independent of EDGE-6**.

## 1. BEARER secret classification

```text
DEFECT_PROVEN=YES
TICKET_STATUS=CLOSED
CLOSED_COMMIT=7d65f2d
CURRENT_BEHAVIOR=is_secret_name substring match; _SECRET_TOKENS includes BEARER
EXPECTED_BEHAVIOR=name containing BEARER redacts like TOKEN/KEY; values never copied
CANONICAL_FILE=_ops/flag_drift.py
EXISTING_TEST_FILE=_ops/tests/test_flag_drift.py
RISK_TIER=CLOSED_HERE
INDEPENDENT_OF_EDGE6=YES
RUNTIME_ACTIVATION_REQUIRED=NO
ROLLBACK=revert 7d65f2d
```

Vault HEAD `7d65f2d` now includes `BEARER` in `_SECRET_TOKENS`. Isolated `00c4fbf` is superseded on this tree. Secret **values** were not read. Ticket **CLOSED**.

RED design: fixture names `OCTOPUS_BOARD_CP_BEARER`, `X_BEARER`, `Authorization` / `Bearer` / whitespace variants; snapshot must not contain the value.

## 2. rfc_id undefined fail-closed

```text
DEFECT_PROVEN=YES_HISTORICAL
CURRENT_BEHAVIOR_ON_VAULT=fail-closed; badge شناسه نامعلوم; no buttons
EXPECTED_BEHAVIOR=public API may omit rfc_id; UI never shows string undefined as id
CANONICAL_FILE=_ops/telegram_center/miniapp/app.js + miniapp_state.py
EXISTING_TEST_FILE=test_miniapp_cockpit_ui.py, test_miniapp_lifecycle_view.py
MINIMAL_CHANGED_FILES=none_on_this_tree
RISK_TIER=CLOSED_HERE
INDEPENDENT_OF_EDGE6=YES
SAFE_TO_PARALLELIZE=YES
RUNTIME_ACTIVATION_REQUIRED=ALREADY_DONE_ON_191
ROLLBACK=revert 0016cdf/1c163ea only if reopening old renderer
```

API **intentionally** strips `rfc_id` (`miniapp_state.py` `_lifecycle_public_stalled_rows`). Renderer was stale; now fail-closed. Owner confirmed on fresh WebView. Persistent Menu Button remains a separate unversioned Telegram object.

## 3. Receipt scan budget >2048

```text
DEFECT_PROVEN=YES
CURRENT_BEHAVIOR=shared MAX_FILES=2048; _lease_map scans receipts first; inbox/outbox then empty/degraded
EXPECTED_BEHAVIOR=receipt history must not consume queue-item budget; cursor pages items
CANONICAL_FILE=138 ofn/adapters/cockpit_v2_read_model.py
EXISTING_TEST_FILE=tests/test_cockpit_v2_read_model.py (no >2048+inbox case)
MINIMAL_CHANGED_FILES=cockpit_v2_read_model.py,test_cockpit_v2_read_model.py
RISK_TIER=YELLOW
INDEPENDENT_OF_EDGE6=YES
SAFE_TO_PARALLELIZE=YES_except_same_file_as_P1
RUNTIME_ACTIVATION_REQUIRED=YES
ROLLBACK=revert two files; restart ofn.service
```

138 live: receipts **>3871** `.claim.json`; inbox 6; outbox 9; V2 `items=[]`, `total=null`, `degraded`. Pagination does not protect the scan.

Preferred reuse: **partition budget** (or existing per-source budget), not raise 2048 unbounded.

## 4. owner_items frontend visibility

```text
DEFECT_PROVEN=YES
CURRENT_BEHAVIOR=API field exists only at a27eb05 unloaded; UI reads data.items only
EXPECTED_BEHAVIOR=labelled business group from owner_items; mesh items unchanged; missing callback null+degraded not fake empty-success
CANONICAL_FILE=138 web/cockpit-v2/src/pages/queue.js (source, not generated; body_not_on_this_host)
EXISTING_TEST_FILE=tests/test_cockpit_v2_owner_queue.py (API only)
MINIMAL_CHANGED_FILES=queue.js + frontend test AFTER P1 load
RISK_TIER=GREEN_YELLOW
INDEPENDENT_OF_EDGE6=YES
SAFE_TO_PARALLELIZE=YES_after_P1_runtime
RUNTIME_ACTIVATION_REQUIRED=YES_for_API
ROLLBACK=revert queue.js
```

Vault `panel.html:1370` uses `data.items || []`. `queue.js` not on `F:\backup`. Restart alone does **not** complete P1 end-to-end.
