---
type: build-wave
wave: 4
status: completed
tags: [octopus, build, wave-4, channels, extractors, full-fleet]
created: 2026-07-12
updated: 2026-07-13
---

# Build Wave 4 · Full Channel Fleet (16 Channels, 17 Extractors)

> **Goal:** Complete the remaining 9 channels to reach the full 16-channel operational surface. Every data source that matters now has an extractor + UI panel.
> **Status:** ✅ Completed
> **Date:** 2026-07-13

---

## Summary

| Metric | Value |
|---|---|
| **Total channels** | 16 |
| **Total extractors** | 17 |
| **JS data files** | 17 |
| **Admin panels** | 13 |
| **Cockpit worlds wired** | 10 |

---

## New Channels (Wave 4)

| Channel | Name | Extractor | Output | UI Panel | Status |
|---|---|---|---|---|---|
| **CH-01** | Research Scout Fleet | `extract_research_data.py` | `research-data.js` | 🔬 Scout / Research | ✅ Implemented |
| **CH-02** | Git Status | `extract_git_status_data.py` | `git-data.js` | ⛓ Git Status | ✅ Implemented |
| **CH-03** | Vault Graph Scanner | `extract_graph.py` | `graph-data.js` | (worlds only) | ✅ Implemented |
| **CH-05** | Obsidian Task Queue | `extract_obsidian_tasks.py` | `task-data.js` | ✓ Task Queue | ✅ Implemented |
| **CH-08** | Crypto / eToro + Wallet | `extract_crypto_data.py` + `extract_wallet_data.py` | `crypto-data.js` + `wallet-data.js` | 📈 Crypto + 💰 Wallet | ✅ Implemented |
| **CH-09** | Mining Fleet Monitor | `extract_mining_data.py` | `mining-data.js` | ⛏ Mining | ✅ Implemented |
| **CH-12** | Ideas Backlog | `extract_ideas_backlog.py` | `ideas-data.js` | 💡 Ideas Backlog | ✅ Implemented |
| **CH-13** | Project Architecture Index | `extract_project_index.py` | `project-data.js` | 📁 Project Index | ✅ Implemented |
| **CH-15** | Telegram Control Surface | `extract_telegram_control.py` | `telegram-data.js` | 📡 Telegram Control | ✅ Implemented |

---

## Extractor Details

### CH-01 · Research Scout Fleet
- **Source:** `00 - Inbox/scout-digests/*.md`
- **Metrics:** digests, findings, sources, spores, cross-domain links, fleet health, coverage 24h/7d, triage board
- **Window var:** `RESEARCH_DATA`
- **Size:** ~3.9 KB

### CH-02 · Git Status
- **Source:** All `.git/` repos under `F:/backup`
- **Metrics:** branch, last commit, dirty files, ahead/behind, clean/dirty repo counts
- **Window var:** `GIT_DATA`
- **Size:** ~4.8 KB

### CH-03 · Vault Graph Scanner
- **Source:** Vault markdown files + links
- **Metrics:** total files, total links, node/edge graph
- **Window var:** `OCTOPUS_GRAPH` (via `graph-data.js`)
- **Size:** ~107 KB

### CH-05 · Obsidian Task Queue
- **Source:** All `.md` files in vault
- **Metrics:** open/done tasks, by priority, by project, next action, completion rate
- **Window var:** `TASK_DATA`
- **Size:** ~677 KB (full), ~0.5 KB (summary via `extract_task_summary.py`)

### CH-08 · Crypto / eToro + Wallet
- **Crypto source:** `_ops/state/crypto_*.json`, LunarCrush cache, CryptoQuant cache
- **Wallet source:** `_ops/state/wallet_*.json`, eToro portfolio cache
- **Metrics:** composite score, registry status, blockers, signals, gate status, positions, budget
- **Window vars:** `CRYPTO_DATA`, `WALLET_DATA`
- **Size:** ~4 KB + ~1.5 KB

### CH-09 · Mining Fleet Monitor
- **Source:** `_ops/state/mining_*.json`, coin hunter cache
- **Metrics:** fleet readiness, electricity mood, node status, security gates, top coin candidates
- **Window var:** `MINING_DATA`
- **Size:** ~7.4 KB

### CH-12 · Ideas Backlog
- **Source:** `03 - Projects/*/idea_*.md`, `_ops/ideas.yaml`
- **Metrics:** total ideas, gold/silver/bronze tiers, ready-to-build count, avg strategic score
- **Window var:** `IDEAS_DATA`
- **Size:** ~83 KB

### CH-13 · Project Architecture Index
- **Source:** `03 - Projects/*/` folders
- **Metrics:** project count, active/stalled, average health, per-project cards (phase, autonomy, blockers)
- **Window var:** `PROJECT_DATA`
- **Size:** ~4.4 KB

### CH-15 · Telegram Control Surface
- **Source:** `_ops/state/channel-status.json`, `telegram_offset.json`, `unified-approval-queue.json`, `budget-state.json`
- **Metrics:** channel live/mode, poll offset age, approvals by verdict, queue counts, budget gate
- **Window var:** `TELEGRAM_DATA`
- **Size:** ~1.9 KB

---

## UI Integration

`OCTOPUS/admin-telegram/index.html` now has **13 panels**:

1. **Vitals** (`L`, `O`) — identity, budget, daemon, events, wires
2. **Queue** (`Q`) — HITL items with approve/reject actions
3. **Health** (`H`) — composite score + subscores
4. **Neural** (`N`) — mode, T_beat, readiness, stress
5. **Wallet** (`WL`) — gate, positions, budget, blockers
6. **Mining** (`M`) — readiness, electricity, nodes, gates, coins
7. **Crypto** (`C`) — composite, registry, blockers, signals
8. **Research** (`R`) — digests, findings, scouts, triage
9. **Git Status** (`G`) — branch, commit, dirty files
10. **Task Queue** (`TK`) — open/done, priority breakdown, next action
11. **Ideas Backlog** (`I`) — total, tiers, ready-to-build
12. **Project Index** (`P`) — active/stalled, health cards
13. **Telegram Control** (`T`) — channel health, approvals, queue, budget gate

---

## Extractor Orchestrator

`refresh-live-data.bat` now runs **17 extractors** in dependency order:

```batch
extract_live_data.py      → L (foundation)
extract_ops_data.py        → O (foundation)
extract_graph.py           → graph (foundation)
extract_audit_data.py      → AUDIT (for twin world)
extract_health_score.py    → H (depends on organism state)
extract_watchdog_data.py   → W (depends on alerts)
extract_neural_data.py     → N (depends on neural modules)
extract_queue_data.py      → Q (depends on approval queue)
extract_research_data.py   → R (depends on scout digests)
extract_obsidian_tasks.py  → TK (depends on vault scan)
extract_git_status_data.py → G (depends on git repos)
extract_wallet_data.py     → WL (depends on wallet state)
extract_mining_data.py     → M (depends on mining state)
extract_crypto_data.py     → C (depends on crypto state)
extract_project_index.py   → P (depends on project folders)
extract_ideas_backlog.py   → I (depends on idea files)
extract_telegram_control.py→ T (depends on channel state)
```

---

## Known Issues at Wave 4 Boundary

| Issue | Severity | Panel Affected | Note |
|---|---|---|---|
| `H.overall` undefined crash | 🔴 High | Health | Fixed in Wave 4 — added null checks |
| `H.subscores.system` undefined | 🔴 High | Health | Fixed in Wave 4 |
| `Q.queue.items` undefined | 🔴 High | Queue | Fixed in Wave 4 |
| `task-data.js` 677 KB | 🟡 Medium | Tasks | Addressed by `extract_task_summary.py` |
| `preview.html` ~1 MB | 🟡 Medium | Preview | Bundles full task-data.js inline |
| LunarCrush data stale | 🟡 Medium | Crypto | Stub mode when cache missing |
| Telegram stub mode | 🟡 Medium | Telegram | Channel live=false when env missing |
| Empty registries | 🟢 Low | Crypto, Mining | Graceful "empty" messages shown |

---

## Evidence

- All 17 extractor `.py` files present in `nervous-system/`
- All 17 `.js` data files generated and non-empty
- `refresh-live-data.bat` runs successfully end-to-end
- Admin UI renders all 13 panels without console errors
- Preview.html opens offline with all data inline

---

## Related

- [[Wave-3|Wave-3 · Cockpit Worlds + Preview]] — previous wave
- [[OCTOPUS-CHANNEL-REGISTRY]] — all 16 channels in one view
- [[OCTOPUS-EXTRACTOR-REGISTRY]] — all 17 extractors in one view
- [[OCTOPUS-WAVE5-HARDENING-PLAN]] — next wave objectives
