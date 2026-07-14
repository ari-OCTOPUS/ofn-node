---
type: build-wave
wave: 1
status: completed
tags: [octopus, build, wave-1, nervous-system]
created: 2026-07-12
updated: 2026-07-12
---

# Build Wave 1 · Nervous System Foundation

> **Goal:** Establish the data backbone — extractors that read from `_ops` and `4d_system` and emit JS data files.
> **Status:** ✅ Completed
> **Date:** 2026-07-09

---

## Deliverables

| # | File | Role | LOC |
|---|---|---|---|
| 1 | `nervous-system/extract_live_data.py` | 4d_system → `live-data.js` | ~129 |
| 2 | `nervous-system/extract_ops_data.py` | `_ops/state` → `ops-data.js` | ~58 |
| 3 | `nervous-system/extract_graph.py` | Vault graph → `graph-data.js` | ~24 |

---

## extract_live_data.py

**Sources:**
- `4d_system/outputs/daemon_state.json`
- `4d_system/outputs/decision_packets.jsonl`
- `4d_system/outputs/self_evolved/frontier.json`
- `4d_system/outputs/4d_experiments.db` (SQLite)

**Output:** `live-data.js`

**Key metrics:**
- SOG identity (`E_shadow + Δ_self`)
- Drift (`temporal_mi`)
- Frontier cells (count, families, rho/kurt/mi)
- Budget (cap, cloud_calls, remaining, by_provider)
- Daemon ticks + generation
- Recent dashboard events

---

## extract_ops_data.py

**Sources:**
- `_ops/state/ORGANISM-STATE.json`
- `_ops/state/fitness-latest.json`
- `_ops/state/cardiac-budget.json`

**Output:** `ops-data.js`

**Key metrics:**
- Money: month/today spend, confirmed/claimed
- Project status (Lead-نقاشی, Mining Fleet, Vault Cartographer)
- Time: chrono_beat, metabolic_age, age_tick, wires_on/total

---

## extract_graph.py

**Sources:**
- Vault note graph (via simple file scan or existing graph engine)

**Output:** `graph-data.js`

**Purpose:** Feed the topology visualizations (`OCTOPUS/01-topology.html`, dream world).

---

## Orchestrator

`refresh-live-data.bat` was created with these 3 extractors (later extended to 9 in Wave 2).

---

## Impact

- Established the **Source → Transform → Sink** pattern
- Proved stdlib-only, offline extractors work
- Created the `nervous-system/` directory as the data hub
- Enabled `OCTOPUS/worlds/` to show real (not fabricated) data

---

## Related

- [[Wave-2 · P1 Channels]] — next wave
- [[Dataflow]] — full pipeline architecture
- [[Backbone]] — shared JS data layer
