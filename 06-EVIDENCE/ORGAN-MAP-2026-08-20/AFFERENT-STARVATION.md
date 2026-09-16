# T66 — afferent starvation root cause

**Verdict: `MIXED`**

```text
NO_SOURCE + BROKEN_READER + THRESHOLD_MISCALIBRATION
```

Thresholds were **compared, not changed**.

## How the code measures it

- Hebbian signal `afferent_starved` when `sensory.afferent_ratio <= 0.1` (`_ops/wiring.py`).
- SensoryBus alarm when ratio `< 0.15` after ≥5 events (`_ops/afferent/sensory_bus.py`).
- Empty bus returns **0.0**. Organism default `_last_afferent_ratio = 1.0` until the first `afferent_beat`.
- Cadence: `CHRONO_AFFERENT_EVERY_N_BEATS` default **1440**.
- Health contract (brain_core): `afferent_ratio>=0.5 && !protective_halt`.

## What actually feeds the bus

`wiring._observations_from_snapshot` builds observations only from:

- `per_organ_alltime_musd` (organs with spend > 0)
- `suspect_zero_total`
- month micro-USD

Vault notes are **not** an afferent source. `knowledge_leg` is an honest skeleton (`live=False`) even though newest note age is **0 days**.

## Why protective_halt history said `afferent_starved`

Verified in `_ops/state/neural/effect-shadow.jsonl` (e.g. 2026-08-01 streaks: `signals: ["afferent_starved", "errors_high"]`).

Mechanism:

1. Notes exist → **NO_SOURCE** (not wired).
2. Reader looks at spend-shape → **BROKEN_READER**.
3. Ratio stays 1.0 (fake healthy) until a beat with empty observations latches **0.0** → **THRESHOLD_MISCALIBRATION**.

Today (session): organism `halted=null`, pain ~0.24 < 0.35. Hunger is structural, not the current halt.

## Metric added

`afferent_events_per_minute_by_source` — implemented in `_ops/organs/telemetry.py`. This session’s knowledge burst is a one-shot scan (655 events), not a sustained minute-rate.
