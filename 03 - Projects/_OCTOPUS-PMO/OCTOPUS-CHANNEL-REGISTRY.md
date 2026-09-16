---
type: registry
project: OCTOPUS
status: active
wave: 4
tags: [octopus, registry, channels, reference]
created: 2026-07-13
updated: 2026-07-13
---

# OCTOPUS · Unified Channel Registry

> **What this is:** The single source of truth for all 16 data channels in the OCTOPUS system.
> **Scope:** Every channel that has an extractor, a JS data file, and a UI consumer.
> **Last synced:** 2026-07-13 with filesystem evidence.

---

## Channel Overview

| # | Channel | Name | Extractor | JS Output | UI Panel / World | Status |
|---|---|---|---|---|---|---|
| 1 | **CH-01** | Research Scout Fleet | `extract_research_data.py` | `research-data.js` | 🔬 Scout / Research (admin) | ✅ Implemented |
| 2 | **CH-02** | Git Status | `extract_git_status_data.py` | `git-data.js` | ⛓ Git Status (admin) | ✅ Implemented |
| 3 | **CH-03** | Vault Graph Scanner | `extract_graph.py` | `graph-data.js` | 02-ontology, 05-galaxy, hub | ✅ Implemented |
| 4 | **CH-04** | Telegram Bot Unified | `telegram_bot_unified.py` | — | Bot interface (Telegram app) | ✅ Implemented |
| 5 | **CH-05** | Obsidian Task Queue | `extract_obsidian_tasks.py` | `task-data.js` | ✓ Task Queue (admin) | ✅ Implemented |
| 6 | **CH-07** | Health Score Composite | `extract_health_score.py` | `health-data.js` | 🫀 Health (admin), 01-cockpit | ✅ Implemented |
| 7 | **CH-08** | Crypto / eToro + Wallet | `extract_crypto_data.py` + `extract_wallet_data.py` | `crypto-data.js` + `wallet-data.js` | 📈 Crypto + 💰 Wallet (admin) | ✅ Implemented |
| 8 | **CH-09** | Mining Fleet Monitor | `extract_mining_data.py` | `mining-data.js` | ⛏ Mining (admin), 03-money | ✅ Implemented |
| 9 | **CH-10** | Git Watcher + Self-Evolution | `git_watcher.py` | — | Event bus trigger | ✅ Implemented |
| 10 | **CH-11** | Tracer + Audit Dashboard | `extract_audit_data.py` | `audit-data.js` | 04-twin (audit world) | ✅ Implemented |
| 11 | **CH-12** | Ideas Backlog | `extract_ideas_backlog.py` | `ideas-data.js` | 💡 Ideas Backlog (admin) | ✅ Implemented |
| 12 | **CH-13** | Project Architecture Index | `extract_project_index.py` | `project-data.js` | 📁 Project Index (admin) | ✅ Implemented |
| 13 | **CH-14** | HITL Queue | `extract_queue_data.py` | `queue-data.js` | 📋 Queue (admin), 01-cockpit badge | ✅ Implemented |
| 14 | **CH-15** | Telegram Control Surface | `extract_telegram_control.py` | `telegram-data.js` | 📡 Telegram Control (admin) | ✅ Implemented |
| **CH-15b** | Telegram Command Registry | `extract_telegram_commands.py` | `telegram-commands-data.js` | 📡 Telegram Control (admin) | ✅ Wave 6 — commands defined, execution stubbed |
| **CH-18** | Audit Trail | `extract_audit_trail.py` | `audit-trail-data.js` | 🔍 Audit Trail (admin) | ✅ Wave 6 |
| 15 | **CH-16** | Neural Vitals | `extract_neural_data.py` | `neural-data.js` | 🧠 Neural (admin), all worlds | ✅ Implemented |
| 16 | **CH-17** | Watchdog Alerts | `extract_watchdog_data.py` | `watchdog-data.js` | (background, alert bus) | ✅ Implemented |
| 17 | **CH-15b** | Telegram Command Registry | `extract_telegram_commands.py` | `telegram-commands-data.js` | 📡 Telegram Control (admin) | ✅ Wave 6 |
| 18 | **CH-18** | Audit Trail | `extract_audit_trail.py` | `audit-trail-data.js` | 🔍 Audit Trail (admin) | ✅ Wave 6 |

---

## Foundation Channels (No Extractor — Core Data)

These are not counted in the 16 above because they are data foundations consumed by multiple channels:

| Source | Extractor | Output | Consumers |
|---|---|---|---|
| `4d_system/outputs/` | `extract_live_data.py` | `live-data.js` | Vitals, Cockpit, Risk, all worlds |
| `_ops/state/` | `extract_ops_data.py` | `ops-data.js` | Vitals, Cockpit |

---

## Channel Detail Cards

### CH-01 · Research Scout Fleet
- **Purpose:** Aggregate research digests from the scout fleet into a health dashboard
- **Source dir:** `F:/backup/00 - Inbox/scout-digests/`
- **Key metrics:** `total_digests`, `total_findings`, `active_scouts`, `stale_scouts`, `coverage_24h`, `coverage_7d`
- **Last modified:** 2026-07-13
- **Known issues:** Stale scouts accumulate if digest intake stops; synthesis lag >48h reduces health score

### CH-02 · Git Status
- **Purpose:** Surface repository hygiene across all project git repos
- **Source:** `.git/` directories under `F:/backup`
- **Key metrics:** `dirty_total`, `ahead`, `behind`, `branch`, `last_commit`
- **Last modified:** 2026-07-13
- **Known issues:** Cap at 50 files per repo for JS size; large repos may be slow to scan

### CH-03 · Vault Graph Scanner
- **Purpose:** Build the note-link graph for ontology/galaxy worlds
- **Source:** All `.md` files in vault
- **Key metrics:** `total_files`, `total_links`, `nodes[]`, `edges[]`
- **Last modified:** 2026-07-13
- **Known issues:** 107 KB output; loads on every hub/world open

### CH-04 · Telegram Bot Unified
- **Purpose:** Single HITL interface bridging `_ops` organism and `4d_system` brain
- **Files:** `4d_system/brain/telegram_bot_unified.py`, `_ops/budget/approval_channel_merge.py`
- **Status:** Credentials gated; stub mode when `TELEGRAM_BOT_TOKEN` missing
- **Last modified:** 2026-07-12

### CH-05 · Obsidian Task Queue
- **Purpose:** Extract all `- [ ]` / `- [x]` tasks from the vault
- **Source:** All `.md` files in vault (skips noise dirs)
- **Key metrics:** `open_tasks`, `done_tasks`, `completion_rate`, `by_priority`, `by_project`, `next_action`
- **Output size:** ~677 KB (full), ~0.5 KB (summary)
- **Last modified:** 2026-07-13
- **Known issues:** Large payload; summary extractor (`extract_task_summary.py`) addresses this

### CH-07 · Health Score Composite
- **Purpose:** Compute 0-100 health score from 3 axes (system, fitness, telemetry)
- **Sources:** `ORGANISM-STATE.json`, `fitness-latest.json`, `telemetry-latest.json`
- **Key metrics:** `overall`, `subscores.system`, `subscores.fitness`, `subscores.telemetry`
- **Last modified:** 2026-07-12
- **Known issues:** UI had null-reference crashes (fixed Wave 4)

### CH-08 · Crypto / eToro + Wallet
- **Purpose:** Surface trading readiness, portfolio status, and budget gate
- **Sources:** `_ops/state/crypto_*.json`, `wallet_*.json`, LunarCrush cache, eToro cache
- **Key metrics:** `composite.score`, `registry.positions_active_count`, `gate.security_gate`, `budget.remaining`
- **Last modified:** 2026-07-13
- **Known issues:** LunarCrush cache often stale → fallback to stub mode; registry empty on first run

### CH-09 · Mining Fleet Monitor
- **Purpose:** Monitor mining readiness, electricity safety, and coin candidates
- **Sources:** `_ops/state/mining_*.json`, coin hunter cache
- **Key metrics:** `readiness.score`, `fleet.electricity_mood`, `security.gates`, `coins.top_candidates`
- **Last modified:** 2026-07-13
- **Known issues:** Coin hunter cache may be empty → "کاندیدی یافت نشد" message

### CH-10 · Git Watcher + Self-Evolution
- **Purpose:** Trigger self-evolution proposals from git events
- **File:** `4d_system/brain/git_watcher.py`
- **Status:** Event-driven trigger (no periodic extractor)

### CH-11 · Tracer + Audit Dashboard
- **Purpose:** Content-free telemetry + audit trail
- **Sources:** `_ops/state/events.jsonl`, `traces.jsonl`, `ledger-fallback.jsonl`
- **Key metrics:** span trees, freshness, delta detection
- **Last modified:** 2026-07-12

### CH-12 · Ideas Backlog
- **Purpose:** Surface strategic ideas with tier scoring
- **Sources:** `03 - Projects/*/idea_*.md`, `_ops/ideas.yaml`
- **Key metrics:** `total_ideas`, `gold/silver/bronze` counts, `ready_to_build_count`, `avg_strategic_score`
- **Last modified:** 2026-07-13
- **Known issues:** 83 KB payload; may need summary mode for preview

### CH-13 · Project Architecture Index
- **Purpose:** Index all active projects with health cards
- **Source:** `03 - Projects/*/` folders
- **Key metrics:** `total_projects`, `active`, `stalled`, `average_health`, per-project blockers/todos
- **Last modified:** 2026-07-13

### CH-14 · HITL Queue
- **Purpose:** Surface unified approval queue for owner verdict
- **Source:** `_ops/state/unified-approval-queue.json`
- **Key metrics:** `pending_count`, `approved_count`, `rejected_count`, `money_at_risk`
- **Last modified:** 2026-07-12

### CH-15 · Telegram Control Surface
- **Purpose:** Monitor Telegram channel health, poll offset, approvals, budget gate
- **Sources:** `channel-status.json`, `telegram_offset.json`, `approvals.jsonl`, `budget-state.json`
- **Key metrics:** `channel.live`, `poll.offset_age_hours`, `approvals.total`, `budget_gate.halted`
- **Last modified:** 2026-07-13
- **Known issues:** Stub mode when `TELEGRAM_BOT_TOKEN` missing; offset age grows when bot is paused

### CH-16 · Neural Vitals
- **Purpose:** Extract neural stack telemetry (mode, readiness, stress, circadian)
- **Sources:** `_ops/state/neural_*.json`, chrono rhythm state
- **Key metrics:** `vitals.mode_color`, `vitals.readiness`, `rhythm.stress`, `circadian.phase`
- **Last modified:** 2026-07-12

### CH-17 · Watchdog Alerts
- **Purpose:** Aggregate stay-alive + governor alerts
- **Sources:** `ORGANISM-STATE.json`, `governor-alerts.md`, `events.jsonl`
- **Key metrics:** alert counts, stale flags, severity distribution
- **Last modified:** 2026-07-12

---

## Backlinks

- [[Wave-4|Wave-4 · Full Channel Fleet]] — build context
- [[OCTOPUS-EXTRACTOR-REGISTRY]] — extractor-level detail
- [[OCTOPUS-ADMIN-DASHBOARD-MAP]] — how channels map to UI panels
- [[OCTOPUS-KNOWN-RISKS]] — risks by channel
