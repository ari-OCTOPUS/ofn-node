---
type: registry
project: OCTOPUS
status: active
wave: 4
tags: [octopus, registry, extractors, reference, nervous-system]
created: 2026-07-13
updated: 2026-07-13
---

# OCTOPUS · Extractor Registry

> **What this is:** The definitive catalog of all 17 Python extractors in the nervous system.
> **Scope:** Path, size, source data, output JS, schema variable, consumers, and known issues.
> **Last synced:** 2026-07-13 with filesystem evidence.

---

## Quick Reference Table

| # | Extractor | Size | Source Data | Output JS | Window Var | Runtime | Depends On |
|---|---|---|---|---|---|---|---|
| 1 | `extract_live_data.py` | ~4.7 KB | `4d_system/outputs/` | `live-data.js` | `LIVE_DATA` | ~1s | SQLite DB |
| 2 | `extract_ops_data.py` | ~2.6 KB | `_ops/state/` | `ops-data.js` | `OPS_DATA` | ~0.5s | — |
| 3 | `extract_graph.py` | ~11.6 KB | Vault `.md` files | `graph-data.js` | `OCTOPUS_GRAPH` | ~2s | — |
| 4 | `extract_audit_data.py` | ~11.4 KB | `_ops/state/*.jsonl` | `audit-data.js` | `AUDIT_DATA` | ~1s | — |
| 5 | `extract_health_score.py` | ~11.6 KB | `_ops/state/ORGANISM-STATE.json` | `health-data.js` | `HEALTH_DATA` | ~0.5s | `fitness-latest.json` |
| 6 | `extract_watchdog_data.py` | ~7.6 KB | `_ops/state/`, `governor-alerts.md` | `watchdog-data.js` | `WATCHDOG_DATA` | ~0.5s | — |
| 7 | `extract_neural_data.py` | ~10.1 KB | `_ops/state/neural_*.json` | `neural-data.js` | `NEURAL_DATA` | ~0.5s | — |
| 8 | `extract_queue_data.py` | ~3.5 KB | `_ops/state/unified-approval-queue.json` | `queue-data.js` | `QUEUE_DATA` | ~0.3s | — |
| 9 | `extract_research_data.py` | ~11.4 KB | `00 - Inbox/scout-digests/*.md` | `research-data.js` | `RESEARCH_DATA` | ~1s | — |
| 10 | `extract_obsidian_tasks.py` | ~8.0 KB | Vault `.md` files | `task-data.js` | `TASK_DATA` | ~3s | — |
| 11 | `extract_git_status_data.py` | ~10.3 KB | `.git/` repos | `git-data.js` | `GIT_DATA` | ~2s | `git` CLI |
| 12 | `extract_wallet_data.py` | ~6.8 KB | `_ops/state/wallet_*.json` | `wallet-data.js` | `WALLET_DATA` | ~0.5s | — |
| 13 | `extract_mining_data.py` | ~14.3 KB | `_ops/state/mining_*.json` | `mining-data.js` | `MINING_DATA` | ~0.5s | — |
| 14 | `extract_crypto_data.py` | ~14.8 KB | `_ops/state/crypto_*.json`, caches | `crypto-data.js` | `CRYPTO_DATA` | ~0.5s | — |
| 15 | `extract_project_index.py` | ~11.3 KB | `03 - Projects/*/` | `project-data.js` | `PROJECT_DATA` | ~1s | — |
| 16 | `extract_ideas_backlog.py` | ~11.9 KB | `03 - Projects/*/idea_*.md` | `ideas-data.js` | `IDEAS_DATA` | ~1s | — |
| 17 | `extract_telegram_control.py` | ~9.9 KB | `_ops/state/telegram/` | `telegram-data.js` | `TELEGRAM_DATA` | ~0.5s | — |
| 18 | `extract_telegram_commands.py` | ~7.7 KB | `_ops/telegram_center/center.py` + config | `telegram-commands-data.js` | `TELEGRAM_COMMANDS_DATA` | ~0.5s | — |
| 19 | `extract_audit_trail.py` | ~4.7 KB | `_ops/state/action-audit.jsonl` | `audit-trail-data.js` | `AUDIT_TRAIL_DATA` | ~0.3s | — |
| *S* | `extract_task_summary.py` | ~4.2 KB | `task-data.js` (derived) | `task-summary-data.js` | `TASK_SUMMARY_DATA` | ~0.3s | `extract_obsidian_tasks.py` |

**Total extractor code:** ~166 KB
**Total JS output:** ~1.07 MB

---

## Schema Convention

Every extractor follows the same output contract:

```javascript
window.VAR_NAME = {
  generated: "2026-07-13T06:30:00Z",
  // ... payload ...
};
```

Where `VAR_NAME` is always `SOMETHING_DATA` (upper_snake_case).

### Consumer Destructure Pattern

The admin UI uses this canonical mapping:

```javascript
const L = window.LIVE_DATA || {};
const O = window.OPS_DATA || {};
const H = window.HEALTH_DATA || {};
const Q = window.QUEUE_DATA || {};
const N = window.NEURAL_DATA || {};
const W = window.WATCHDOG_DATA || {};
const C = window.CRYPTO_DATA || {};
const M = window.MINING_DATA || {};
const WL = window.WALLET_DATA || {};
const R = window.RESEARCH_DATA || {};
const G = window.GIT_DATA || {};
const TK = window.TASK_DATA || {};
const I = window.IDEAS_DATA || {};
const P = window.PROJECT_DATA || {};
const T = window.TELEGRAM_DATA || {};
const TC = window.TELEGRAM_COMMANDS_DATA || {};
const AT = window.AUDIT_TRAIL_DATA || {};
```

---

## Extractor Detail Cards

### extract_live_data.py
- **Path:** `F:/backup/nervous-system/extract_live_data.py`
- **Sources:**
  - `4d_system/outputs/daemon_state.json`
  - `4d_system/outputs/decision_packets.jsonl`
  - `4d_system/outputs/self_evolved/frontier.json`
  - `4d_system/outputs/4d_experiments.db` (SQLite)
- **Output:** `live-data.js` (~141 KB)
- **Schema:** `window.LIVE_DATA = { sog, events, frontier, budget, packets, daemon, cycle, portrait }`
- **Runtime:** ~1s (SQLite query dominates)
- **Known issues:** `frontier.json` path fallback to backups if primary missing

### extract_ops_data.py
- **Path:** `F:/backup/nervous-system/extract_ops_data.py`
- **Sources:**
  - `_ops/state/ORGANISM-STATE.json`
  - `_ops/state/fitness-latest.json`
  - `_ops/state/cardiac-budget.json`
- **Output:** `ops-data.js` (~0.9 KB)
- **Schema:** `window.OPS_DATA = { money, time, projects, generated }`
- **Runtime:** ~0.5s
- **Known issues:** None — very stable

### extract_graph.py
- **Path:** `F:/backup/nervous-system/extract_graph.py`
- **Sources:** Vault markdown files
- **Output:** `graph-data.js` (~107 KB)
- **Schema:** `window.OCTOPUS_GRAPH = { total_files, total_links, nodes, edges }`
- **Runtime:** ~2s
- **Known issues:** Large output; cap may be needed for mobile

### extract_audit_data.py
- **Path:** `F:/backup/nervous-system/extract_audit_data.py`
- **Sources:** `_ops/state/events.jsonl`, `traces.jsonl`, `ledger-fallback.jsonl`
- **Output:** `audit-data.js` (~11 KB)
- **Schema:** `window.AUDIT_DATA = { freshness, delta, by_agent, by_status, spans, generated }`
- **Runtime:** ~1s
- **Known issues:** Stale flag triggers at >45min

### extract_health_score.py
- **Path:** `F:/backup/nervous-system/extract_health_score.py`
- **Sources:** `ORGANISM-STATE.json`, `fitness-latest.json`, `telemetry-latest.json`
- **Output:** `health-data.js` (~1.2 KB)
- **Schema:** `window.HEALTH_DATA = { overall, status, subscores, details, alerts, weights }`
- **Runtime:** ~0.5s
- **Known issues:** Weights can be overridden via `health-weights.json`

### extract_watchdog_data.py
- **Path:** `F:/backup/nervous-system/extract_watchdog_data.py`
- **Sources:** `ORGANISM-STATE.json`, `governor-alerts.md`, `events.jsonl`
- **Output:** `watchdog-data.js` (~15 KB)
- **Schema:** `window.WATCHDOG_DATA = { state, alerts, stale, generated }`
- **Runtime:** ~0.5s
- **Known issues:** Alert cutoff = 24h; `MAX_ALERTS = 50`

### extract_neural_data.py
- **Path:** `F:/backup/nervous-system/extract_neural_data.py`
- **Sources:** `_ops/state/neural_*.json`
- **Output:** `neural-data.js` (~1.5 KB)
- **Schema:** `window.NEURAL_DATA = { vitals, rhythm, circadian, layers, generated }`
- **Runtime:** ~0.5s
- **Known issues:** Protective mode flag can be stale if chrono not running

### extract_queue_data.py
- **Path:** `F:/backup/nervous-system/extract_queue_data.py`
- **Sources:** `_ops/state/unified-approval-queue.json`
- **Output:** `queue-data.js` (~0.3 KB)
- **Schema:** `window.QUEUE_DATA = { queue: { items, counts, badge, first_action, by_source } }`
- **Runtime:** ~0.3s
- **Known issues:** Very small; fast but empty queue = blank UI without fallback

### extract_research_data.py
- **Path:** `F:/backup/nervous-system/extract_research_data.py`
- **Sources:** `00 - Inbox/scout-digests/*.md`
- **Output:** `research-data.js` (~3.9 KB)
- **Schema:** `window.RESEARCH_DATA = { pipeline, fleet, synthesis, triage, recent_digests, health }`
- **Runtime:** ~1s
- **Known issues:** `CANONICAL_SCOUTS` hardcoded; new scouts won't appear in fleet health

### extract_obsidian_tasks.py
- **Path:** `F:/backup/nervous-system/extract_obsidian_tasks.py`
- **Sources:** All `.md` files in vault (skips noise dirs)
- **Output:** `task-data.js` (~677 KB)
- **Schema:** `window.TASK_DATA = { summary, open_tasks[], done_tasks[], by_project }`
- **Runtime:** ~3s (vault scan dominates)
- **Known issues:** Largest payload by far; summary extractor mitigates

### extract_git_status_data.py
- **Path:** `F:/backup/nervous-system/extract_git_status_data.py`
- **Sources:** `.git/` repos under `F:/backup`
- **Output:** `git-data.js` (~4.8 KB)
- **Schema:** `window.GIT_DATA = { summary, repos[] }`
- **Runtime:** ~2s (git CLI calls dominate)
- **Known issues:** Files capped at 50 per repo; timeout 30s per repo

### extract_wallet_data.py
- **Path:** `F:/backup/nervous-system/extract_wallet_data.py`
- **Sources:** `_ops/state/wallet_*.json`, eToro cache
- **Output:** `wallet-data.js` (~1.5 KB)
- **Schema:** `window.WALLET_DATA = { gate, portfolio, budget, generated }`
- **Runtime:** ~0.5s
- **Known issues:** eToro cache may be stale; gate shows "unknown" when missing

### extract_mining_data.py
- **Path:** `F:/backup/nervous-system/extract_mining_data.py`
- **Sources:** `_ops/state/mining_*.json`, coin hunter cache
- **Output:** `mining-data.js` (~7.4 KB)
- **Schema:** `window.MINING_DATA = { fleet, readiness, security, coins, runtime, generated }`
- **Runtime:** ~0.5s
- **Known issues:** Coin hunter cache empty → empty candidates list

### extract_crypto_data.py
- **Path:** `F:/backup/nervous-system/extract_crypto_data.py`
- **Sources:** `_ops/state/crypto_*.json`, LunarCrush cache, CryptoQuant cache
- **Output:** `crypto-data.js` (~4 KB)
- **Schema:** `window.CRYPTO_DATA = { composite, registry, project, blockers, lunarcrush, cryptoquant, generated }`
- **Runtime:** ~0.5s
- **Known issues:** LunarCrush often stale; registry empty on first run

### extract_project_index.py
- **Path:** `F:/backup/nervous-system/extract_project_index.py`
- **Sources:** `03 - Projects/*/` folders
- **Output:** `project-data.js` (~4.4 KB)
- **Schema:** `window.PROJECT_DATA = { summary, projects[] }`
- **Runtime:** ~1s
- **Known issues:** Health scoring heuristic; may misclassify stalled projects

### extract_ideas_backlog.py
- **Path:** `F:/backup/nervous-system/extract_ideas_backlog.py`
- **Sources:** `03 - Projects/*/idea_*.md`, `_ops/ideas.yaml`
- **Output:** `ideas-data.js` (~83 KB)
- **Schema:** `window.IDEAS_DATA = { summary, ideas[] }`
- **Runtime:** ~1s
- **Known issues:** 83 KB payload; may need summary mode for preview

### extract_telegram_control.py
- **Path:** `F:/backup/nervous-system/extract_telegram_control.py`
- **Sources:** `channel-status.json`, `telegram_offset.json`, `approvals.jsonl`, `budget-state.json`
- **Output:** `telegram-data.js` (~1.9 KB)
- **Schema:** `window.TELEGRAM_DATA = { channel, poll, approvals, queue, budget_gate, health, admin_actions }`
- **Runtime:** ~0.5s
- **Known issues:** Stub mode when env missing; offset age grows when bot paused

### extract_task_summary.py (Satellite)
- **Path:** `F:/backup/nervous-system/extract_task_summary.py`
- **Sources:** `task-data.js` (derived)
- **Output:** `task-summary-data.js` (~0.5 KB)
- **Schema:** `window.TASK_SUMMARY_DATA = { open, done, total, completion_rate, by_priority, by_project, next_action }`
- **Runtime:** ~0.3s
- **Known issues:** Depends on `extract_obsidian_tasks.py` having run first

---

## Dependency Graph

```
extract_live_data.py      ──┐
extract_ops_data.py         ├─► foundation (no deps)
extract_graph.py            ──┘

extract_health_score.py     ──► needs ORGANISM-STATE + fitness + telemetry
extract_watchdog_data.py    ──► needs ORGANISM-STATE + governor-alerts
extract_neural_data.py      ──► needs neural state files
extract_queue_data.py       ──► needs unified-approval-queue.json
extract_research_data.py    ──► needs scout-digests
extract_git_status_data.py  ──► needs git CLI + repos

extract_obsidian_tasks.py   ──► task-data.js
extract_task_summary.py     ──► needs task-data.js (run AFTER tasks)

extract_wallet_data.py      ──┐
extract_mining_data.py      ├──► independent (parallelizable)
extract_crypto_data.py      ──┘

extract_project_index.py    ──► independent
extract_ideas_backlog.py    ──► independent
extract_telegram_control.py ──► independent
extract_telegram_commands.py ──► independent
extract_audit_trail.py      ──► independent
extract_audit_data.py       ──► independent
```

---

## Wave 6 Extractor Detail Cards

### extract_telegram_commands.py
- **Path:** `F:/backup/nervous-system/extract_telegram_commands.py`
- **Sources:**
  - `_ops/state/telegram/center-config.json`
  - `_ops/state/telegram_offset.json`
  - `_ops/state/pulse/telegram-poll.json`
  - `_ops/telegram_center/center.py` (command registry parse)
- **Output:** `telegram-commands-data.js` (~7 KB)
- **Schema:** `window.TELEGRAM_COMMANDS_DATA = { bot, commands[], poll, safety_summary }`
- **Runtime:** ~0.5s
- **Safety:** Masks chat IDs; emits mode labels (READ-ONLY, PROPOSE-ONLY, NOT YET WIRED)

### extract_audit_trail.py
- **Path:** `F:/backup/nervous-system/extract_audit_trail.py`
- **Sources:**
  - `_ops/state/action-audit.jsonl`
- **Output:** `audit-trail-data.js` (~1-5 KB)
- **Schema:** `window.AUDIT_TRAIL_DATA = { stats, recent_actions[], rollback_classification }`
- **Runtime:** ~0.3s
- **Safety:** Read-only from append-only log; computes dry-run vs live ratio and rollback coverage

---

## Backlinks

- [[OCTOPUS-CHANNEL-REGISTRY]] — channel-level view
- [[Wave-4 · Full Channel Fleet]] — build context
- [[OCTOPUS-ADMIN-DASHBOARD-MAP]] — how extractors feed the UI
- [[OCTOPUS-KNOWN-RISKS]] — risks by extractor
