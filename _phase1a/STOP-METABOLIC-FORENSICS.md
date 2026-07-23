# STOP-METABOLIC — Forensic Investigation (read-only audit)

Date: 2026-07-23 · Auditor: sole investigator · Access: **READ-ONLY** (no code/state changed).
Halt file `_ops/STOP-METABOLIC` (latest write `2026-07-23T22:10:26`):
`billed↔telemetry divergence 100% > 20% (billed AU$0.06 vs telemetry AU$0.00)`

## One-line verdict
The AU$0.06 is a **real, authorized, correctly-metered LLM spend** (cortex), not a fraudulent or
runaway charge. The halt is a **false alarm** from comparing two *different* metering sources — one of
which (`core.db`) has been **frozen/empty since 2026-07-06**.

## Exact money trail (from `_ops/budget/organ-gate-log.jsonl`)
All spend is organ `ARCHITECT_SYS`, task `cortex-primary` (i.e. `_ops/cortex/model_router.py` →
`organ_gate.reserve/settle`):

| settle ts | actual_usd | task |
|---|---|---|
| 2026-07-15T10:08:39 | 0.001425 | cortex-primary |
| 2026-07-15T21:49:06 | 0.002185 | cortex-primary |
| 2026-07-16T11:11:50 | 0.017685 | cortex-primary |
| **2026-07-23T13:31:45** | **0.016805** | cortex-primary (today) |

Σ July = **0.038100 USD × fx 1.5 = AU$0.05715** → exactly `budget-state.json.spent_month_aud`
(and `organ-state.json ARCHITECT_SYS spent_month_musd=38100`, `spent_today_musd=16805`). Every settle
carries a real `actual_usd` (not an estimate) → the spend **was** metered by `organ_gate`.

## Why telemetry reads 0 (source of the divergence)
`telemetry.py.reconcile()` compares:
- **billed** = `budget-state.json.spent_month_aud` = 0.05715 — correct, from the live cortex path (organ_gate).
- **telemetry** = `snapshot().month.aud`, built from **`core.db.usage`** + genome-ledger `llm_cost_usd`.

Read-only inspection:
- `core.db` (`_launchpad/second-brain-live/control-brain/core.db`): `usage` table has **0 rows**
  (`SELECT COUNT(*) FROM usage` = 0), file mtime **2026-07-06T13:07:29** (frozen).
- Genome ledger has 771 July lines but they are backup/guardian METRICs — **no `llm_cost_usd`**.

So telemetry always reads 0. The cortex path meters into `organ_gate` but **never writes to
`core.db.usage`** — they are two independent metering systems.

## Trigger timeline
- Through July 16: month spend 0.0213 USD ≈ 0.032 AUD → below the 5¢ floor (`billed_aud > 0.05`) → the
  divergence check is inactive; no halt.
- **2026-07-23T13:31:45**: cortex-primary settle (0.016805) pushes the month to **AU$0.05715** > 5¢.
- **2026-07-23T13:36:03**: first fire — `_ops/budget/FREEZE.flag` + `_ops/STOP-METABOLIC` written
  (billed 0.057 vs telemetry 0 → 100% > `DIVERGENCE_DEATH`=0.20).
- The periodic reconcile re-fires and rewrites the halt timestamp (16:28 → … → 22:10:26).

The organism ran normally until 13:36 today, then froze. The 13:31 cortex call happened *before* the halt.

## Cause classification
| hypothesis | result |
|---|---|
| fraudulent / unauthorized spend | ❌ — legitimate cortex calls with real actual_usd |
| runaway cost | ❌ — 5.7¢ vs 30 AUD cap |
| rounding error | ❌ — genuine sum of 4 real calls |
| stale billing | ❌ — spend is current/real |
| unmetered call (in telemetry) | ✅ yes in the *telemetry* source only — it IS metered in organ_gate |
| **metering-source mismatch (observability gap)** | ✅ **ROOT CAUSE** — `core.db.usage` empty/frozen; cortex path never writes there |

## Safety recommendation (owner decision)
**Money/security: removing STOP-METABOLIC is SAFE.** The spend is real, authorized, tiny (5.7¢), far
under caps, and correctly billed. No financial risk.

**But do NOT clear it alone** — the next reconcile will re-compare billed(0.057) vs telemetry(0) and
**re-halt immediately** (the 5¢ floor is already exceeded). Fix the source mismatch *first*:
1. Preferred: make `telemetry.py` reconcile against the **live** source (`organ-state.json` /
   organ-gate-log `actual_usd`) instead of the empty `core.db`, so billed↔telemetry share one system.
2. Or: raise the comparison floor from 5¢ to a meaningful absolute (e.g. $1), and/or only alarm when
   `telemetry > 0` (so an empty source can never manufacture a 100% divergence).
3. Or: wire the cortex/gateway path to also write `core.db.usage` (if `core.db` is meant to be the SoT).

Then manually delete `_ops/budget/FREEZE.flag` and `_ops/STOP-METABOLIC` (per `telemetry.py`'s own note).

All of the above are code changes and were **not** performed (read-only mission).
