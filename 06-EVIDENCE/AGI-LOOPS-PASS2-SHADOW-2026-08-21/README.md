---
type: evidence
status: active
tags: [agi-loops, pass2, shadow, 2026-08-21]
created: 2026-08-21
updated: 2026-08-21
created_by: agent
project: "[[04 - Architect System/architect/PROJECT]]"
---

# AGI-LOOPS PASS 2 — SHADOW

Four cheap loops. No live send. No Wave 1 unlock. No production memory write. Doctor quarantine ran on a **copy** only.

| item | result |
|---|---|
| S-A03 calibration-latest → `improve.py` | gather_signals reads the file; `generate_proposals` emits propose-only `source=calibration` |
| S-A01 constant 0.4 → receipt EMA | no `confidence = 0.4` assign; `_accuracy_ema` present |
| S-D01 doctor-pulse timeout | copy: 1 open → 0; live `missions.json` still `awaiting-merge` |
| S-T03 outbox digest | 42 loops → 1 dry_run digest, coalesced=39, `sent=false`; replay `update_id` = `duplicate` |

`wave1_unlocked=false`. `paid_calls=NOT_GRANTED`. `live_telegram=false`. `pass3_live=NOT_GRANTED_BY_THIS_ORDER`.

T-05 tampered initData is already pinned in `_ops/tests/test_miniapp_gateway.py` (unit, not live). T-21/T-22/T-08 remain preconditions for any later LIVE grant.

Tests: `_ops/tests/test_agi_pass2_shadow.py` (not registered in `run_all.py`).
