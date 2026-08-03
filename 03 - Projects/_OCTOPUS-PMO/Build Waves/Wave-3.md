---
type: build-wave
wave: 3
status: completed
tags: [octopus, build, wave-3, cockpit, worlds]
created: 2026-07-12
updated: 2026-07-12
---

# Build Wave 3 · Cockpit Worlds + Preview

> **Goal:** Wire real data into the 10 cockpit worlds and build the self-contained preview dashboard.
> **Status:** ✅ Completed
> **Date:** 2026-07-12

---

## Deliverables

| # | File | Role | Size |
|---|---|---|---|
| 1 | `OCTOPUS/worlds/index.html` | Hub navigation for 10 worlds | ~11 KB |
| 2 | `OCTOPUS/worlds/01-cockpit/index.html` | Mission control with real vitals | ~14 KB |
| 3 | `OCTOPUS/worlds/02-ontology/index.html` | Graph ontology viewer | ~7 KB |
| 4 | `OCTOPUS/worlds/03-money/index.html` | Money engine (wallet + mining + crypto) | ~9 KB |
| 5 | `OCTOPUS/worlds/04-twin/index.html` | Digital twin / audit trail | ~7 KB |
| 6 | `OCTOPUS/worlds/05-galaxy/index.html` | Knowledge galaxy | ~7 KB |
| 7 | `OCTOPUS/worlds/06-time/index.html` | Time river / chronos | ~7 KB |
| 8 | `OCTOPUS/worlds/07-decision/index.html` | Decision tree | ~7 KB |
| 9 | `OCTOPUS/worlds/08-risk/index.html` | Risk radar dome | ~8 KB |
| 10 | `OCTOPUS/worlds/09-compass/index.html` | Value compass | ~7 KB |
| 11 | `OCTOPUS/worlds/10-habit/index.html` | Habit lattice | ~7 KB |
| 12 | `OCTOPUS/admin-telegram/preview.html` | Self-contained preview (~1 MB) | ~1 MB |

---

## Data Integration

All 10 worlds now load from the real data backbone:

```
../../../nervous-system/live-data.js      → L = LIVE_DATA
../../../nervous-system/neural-data.js    → N = NEURAL_DATA
../../../nervous-system/health-data.js    → H = HEALTH_DATA
../../../nervous-system/research-data.js  → R = RESEARCH_DATA
../../../nervous-system/task-data.js      → TK = TASK_DATA
../../../nervous-system/git-data.js       → G = GIT_DATA
../octo-data.js                           → shared core
```

### Hub (`worlds/index.html`)
- Loads live-data.js + neural-data.js + task-data.js + git-data.js
- Displays organism vitals bar: identity, events, frontier, budget, neural
- Dataflow freshness indicator

### 01-cockpit
- Real-time SOG identity, drift, budget, events
- Neural readiness + protective mode indicator
- Health score with subscores
- Research scout fleet status
- Task queue badge (open/critical)
- Hero recommendation engine: picks top action from real data

### 08-risk
- Live risk radar: drift, budget depletion, daemon pause, owner-gate queue, failed events
- Security gates panel: daemon, owner gate, identity anchor, cloud budget
- Three modes: radar sweep, risk ladder, gate status

---

## Shared Infrastructure

| File | Purpose |
|---|---|
| `OCTOPUS/worlds/octo-data.js` | Shared data core + freshness API |
| `OCTOPUS/worlds/octo-core.js` | World bootstrap helpers |
| `OCTOPUS/worlds/octo-info.js` | Info panel renderer |
| `OCTOPUS/worlds/shared-ui.js` | Mathviz bridge + common UI |
| `OCTOPUS/worlds/graph-data.js` | Vault graph (107 KB) |
| `OCTOPUS/worlds/neural-data.js` | Neural stack snapshot |

---

## Design Principles

1. **Read-only from worlds** — no world mutates source data
2. **Graceful degradation** — if extractors not run, shows symbolic fallback
3. **Mobile-first** — all worlds are `touch-action:none` with safe-area insets
4. **Consistent glyph language** — each world has a unique SVG glyph + color
5. **One action per world** — each world surfaces exactly one "next action"

---

## Evidence

- All 10 world `index.html` files verified present
- Hub loads 5 real data files + graph-data.js
- Cockpit renders real identity, budget, events, neural, health, research, tasks
- Risk world renders live risk blips from `LIVE_DATA`
- Preview.html bundles all data inline (self-contained)

---

## Related

- [[Wave-2|Wave-2 · P1 Channels]] — previous wave
- [[Wave-4|Wave-4 · Full Channel Fleet]] — next wave
- [[OCTOPUS-CHANNEL-REGISTRY]] — all 16 channels
- [[OCTOPUS-ADMIN-DASHBOARD-MAP]] — panel-to-data mapping
