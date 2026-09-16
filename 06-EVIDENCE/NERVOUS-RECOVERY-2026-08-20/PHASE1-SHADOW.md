---
type: evidence
created: 2026-08-20
updated: 2026-08-20
tags: [octopus, wave0, nervous-recovery, shadow]
---

# Phase 1 — Attribution shadow (no restart)

`wave1_unlocked=false`. Canary restart **NOT_GRANTED** / `EXECUTE=false`.

## Shadow window (today UTC)

Source `_ops/state/cortex/cost-receipts.jsonl` sha256 `2e9f84a7bd42a48ff950b944af1a43857f508eabbe8bafdd1e1db06e9986a8e1` — **unchanged** after scan (977 lines).

Shadow ledger: `receipts-v2-shadow.jsonl` (149 rows). Original jsonl was not opened for write.

| criterion | value | pass |
|---|---|---|
| duplicate_receipts | 0 | yes |
| fabricated_task_ids | 0 | yes |
| schema_validation | 1.0 | yes |
| original_receipt_hash coverage | 1.0 | yes |

`task_id` only from caller field or explicit `run_to_task` map. No map on disk → unresolved rows keep `task_id=null` and `attribution_status=unresolved`. PID / timestamp / capability never become an ID.

This PASS is **hygiene of the shadow window**, not `WAVE0_PASS`.

## Test registry (measurement correction)

Registry is **file-level** (`test_*.py` vs names in `TESTS`/`EXTRA_TESTS`/`PYTEST_TESTS`).

| | before | after register |
|---|---:|---:|
| discovered files | 790 | 790 |
| registered files | 636 | **637** |
| gap | 160 | **159** |

Owner expectation `790 → 798` mixed **discovered-file count** with **8 functions**. Those functions live in one file: `_ops/tests/test_nervous_recovery.py` (now **12** functions, all green). Registering eight phantom files would have been a false registry.

`python -X utf8 _ops/tests/run_all.py --only test_nervous_recovery.py` → 12 passed.

## Immune labels

| status | n |
|---|---:|
| VERIFIED | 0 |
| DECLARED_UNOBSERVED | 5 |
| DORMANT | 5 (no actuator / proven inactive path) |
| BLOCKED | 0 |

`DECLARED_UNOBSERVED` = declared + callable, no attributable receipt. Not proof the capability is absent.

## Wave 0 (still locked)

| Gate | now | pass |
|---|---|---|
| attribution | 0.3423 | false |
| test registry | 637/790 | false |
| memory streak | 1 | false |
| capability parse | 10 | true |

Verdict **WAVE0_PARTIAL**. Next PASS still needs attribution ≥0.95 **and** gap 0 **and** 10 consecutive memory cycles **and** fabricated_task_ids=0 **and** no critical regressions.

## Canary (not executed)

First producer: **cortex** (only confirmed writer of `cost-receipts.jsonl`). Never daemon+live+cortex together. See `CANARY-PLAN.json` / `CANARY-BASELINE.json` (`owner_permit: NOT_GRANTED`).
