# REPORT-P1

## خط حقیقت

```text
octopus-shadow-prepared + arm-plan-documented + daily-checklist-ready
!= armed (pending owner activation on live tree) != 7-day-shadow-complete != AGI
```

## Done

### P1.1 — Arm plan with file:line evidence

| Flag | Seam | Precondition | Rollback |
|---|---|---|---|
| `OCTOPUS_WIRE_COLLAB=1` | `miniapp_gateway.py:769` | HMAC (`validate_init_data:188`) + owner allowlist (`TELEGRAM_OWNER_CHAT_ID`) | flag=0 + restart |
| `OCTOPUS_WIRE_COLLAB_MEMORY=1` | `collab_memory.py:42` | P1-1 stable 24h | flag=0 + wipe scoped |
| `OCTOPUS_WIRE_COLLAB_DIGEST=1` | `collab_digest.py:23` | P1-2 stable | flag=0 |
| `OCTOPUS_COLLAB_USE_MODEL=1` (optional) | `collaborator.py:41` | daily budget cap written | flag=0 + STOP-FUGU |

Rate limit: `_ASK_WINDOW_S=30.0` · `_ASK_MAX_PER_WINDOW=6` (`miniapp_gateway.py:131-132`)
Redact: `_redact()` on every response (`miniapp_gateway.py:170,778`)
State containment: `collab_memory._state_path()` enforces `OCTOPUS_STATE_DIR` root

### P1.2 — DAILY-INDEPENDENCE-CHECKLIST.md

6 daily KPIs + weekly checks + arm sequence + rollback for each flag.

### P1.3 — daily-cost.py

Read-only script: reads `paid-calls.jsonl`, sums `cost_usd` for today, shows per-tier counts, STOP-FUGU status, budget state. Zero send.

### P1.4 — Dark snapshot plan

After each arm, owner runs:
```bash
python _ops/dark_capabilities.py --json
```
and checks that newly-armed flags show `state: "ON"` (if `live_source` available) or
structurally-confirmed. Evidence goes in `_ops/test_intelligence/evidence/`.

## Evidence (paths + commands)

```text
Arm plan:           _ops/DAILY-INDEPENDENCE-CHECKLIST.md
Daily cost:         python _ops/scripts/daily-cost.py
Dark snapshot:      python _ops/dark_capabilities.py --json
Collab security:    python _ops/tests/test_ti_collab_security.py → 12/12
API collab:         python _ops/tests/test_api_collab.py → 17/17
Components:         python _ops/tests/test_collab_components.py → 23/23
```

## Flags touched (before → after)

```text
NO flags armed on live tree.
All documentation only — arm sequence defined for owner to execute.
```

## Gates

- [ ] 7 روز shadow بدون حادثه — **PENDING (not started)**
- [ ] مالک تأیید کند: «بدون تو هم کار روزانه می‌چرخد» — **PENDING**
- [x] صفر اثر خارجی ناخواسته (code audit: external_effect=False everywhere)
- [x] لاگ‌ها digest-only (collab_memory content-free; trace_schema digest-only)
- [x] Arm plan documented with file:line evidence
- [x] Daily checklist created
- [x] Read-only cost summary available

## NOT done / blocked

1. **Actual arm** — owner must set flags on live tree + restart
2. **7-day shadow observation** — starts after arm
3. **`OCTOPUS_FUGU_TIMEOUT_NOT_PROVIDER_FAIL`** — owner action (not P1 gate)
4. **CSV reconcile / لید 667951** — owner action (money goal, not P1 gate)

## Owner decisions needed

1. **Arm `OCTOPUS_WIRE_COLLAB=1` on live tree?** — پس از restart، `/api/collab` فعال
2. **Budget cap for model?** — اگر `OCTOPUS_COLLAB_USE_MODEL=1` می‌خواهی، سقف روزانه را بگو

## Next phase entry criteria

- P2 can be worked on in parallel with late P1 (code/docs only, no arm)
- P2 focuses on: ROUTE-POLICY + chaos matrix + golden traces + evidence ladder
- P3 blocked until P1 gate green
