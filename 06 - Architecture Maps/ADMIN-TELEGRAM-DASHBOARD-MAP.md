---
type: architecture
# title: Admin Telegram Dashboard Map
status: active
created: 2026-07-12
updated: 2026-07-12
tags: [octopus, admin-telegram, dashboard, ui, wave-5]
related:
  - "[[OCTOPUS-CHANNEL-REGISTRY]]"
  - "[[OCTOPUS-EXTRACTOR-REGISTRY]]"
  - "[[WAVE-5-HARDENING-PLAN]]"
---

# Admin Telegram Dashboard Map

> All 13 panels in `OCTOPUS/admin-telegram/index.html`: data sources, schemas, and control modes.

## File

- **Path**: `F:/backup/OCTOPUS/admin-telegram/index.html`
- **Size**: ~37KB
- **Preview**: `F:/backup/OCTOPUS/admin-telegram/preview.html` (~1MB, self-contained)
- **Data dir**: `F:/backup/nervous-system/`

## System Banner

At the top of the page (Wave 5 addition):
- **System Mode**: SHADOW / PROPOSE-ONLY
- **Owner Approval**: Required flag (red)
- **Last Refresh**: Computed from freshest `generated` timestamp across all loaded data sources
- **Active Channels**: Count of successfully loaded data sources / 16 total

## Panel Map

### 1. Vitals — وضعیتِ زنده
- **Mode**: READ-ONLY
- **Data**: `live-data.js` (`window.LIVE_DATA`)
- **Extractor**: `extract_live_data.py`
- **Schema**: `{sog: {identity_now, drift_now, healthy}, events: {total_rows, recent}, budget: {remaining, cap}, daemon: {total_ticks, stopped_at}}`
- **Fallback**: Shows "دادهٔ زنده یافت نشد" if `L` missing.

### 2. Queue — صفِ تأیید
- **Mode**: OWNER VERDICT REQUIRED
- **Data**: `queue-data.js` (`window.QUEUE_DATA`)
- **Extractor**: `extract_queue_data.py`
- **Schema**: `{queue: {items: [{id, title, source, status, risk_level, amount_aud}], counts: {pending, approved, rejected}}}`
- **Actions**: `actOne(id, action)` and `actAll(action)` are **propose-only** — they show a placeholder message and require owner confirmation in Telegram.
- **Fallback**: Shows "صف خالی است" if no items.

### 3. Health — سلامتِ سیستم
- **Mode**: READ-ONLY
- **Data**: `health-data.js` (`window.HEALTH_DATA`)
- **Extractor**: `extract_health_score.py`
- **Schema**: `{overall, subscores: {system, fitness, telemetry}, status, status_emoji}`
- **Fallback**: Shows "health-data.js لود نشد" if `H` missing.

### 4. Neural — شبکهٔ عصبی
- **Mode**: READ-ONLY
- **Data**: `neural-data.js` (`window.NEURAL_DATA`)
- **Extractor**: `extract_neural_data.py`
- **Schema**: `{rhythm: {mode_color, T_beat, stress}, circadian: {readiness}, vitals: {mode_color, readiness, stress, protective}}`
- **Fallback**: Shows "neural-data.js لود نشد" if `N` missing.

### 5. Wallet / eToro — کیف پول
- **Mode**: SHADOW MODE
- **Data**: `wallet-data.js` (`window.WALLET_DATA`)
- **Extractor**: `extract_wallet_data.py`
- **Schema**: `{gate: {security_gate, hard_rules, primary_blocker}, portfolio: {position_count, approved_count}, budget: {remaining, daily_cap, depleted}}`
- **Actions**: No action buttons. Advisory display only.
- **Fallback**: Shows "wallet-data.js لود نشد" if `WL` missing.

### 6. Mining — ⛏ ماینینگ
- **Mode**: SHADOW MODE
- **Data**: `mining-data.js` (`window.MINING_DATA`)
- **Extractor**: `extract_mining_data.py`
- **Schema**: `{fleet: {nodes_total, nodes_running, electricity_safe}, readiness: {score, mood, reasons}, security: {gates: {...}}, coins: {top_candidates: [...]}}`
- **Actions**: No action buttons sent to fleet. Advisory only.
- **Fallback**: Shows "mining-data.js لود نشد" if `M` missing.

### 7. Crypto / eToro — 📈 کریپتو
- **Mode**: SHADOW MODE
- **Data**: `crypto-data.js` (`window.CRYPTO_DATA`)
- **Extractor**: `extract_crypto_data.py`
- **Schema**: `{composite: {score, status}, project: {execution_state, security_gate}, registry: {registry_empty}, lunarcrush: {...}, cryptoquant: {...}, blockers: [{id, label, active}]}`
- **Actions**: ZERO live trades. EdgeClassifier is unwired → permanent NO_ACTION.
- **Fallback**: Shows "crypto-data.js لود نشد" if `C` missing.

### 8. Research / Scout — 🔬 اسکاوت
- **Mode**: READ-ONLY
- **Data**: `research-data.js` (`window.RESEARCH_DATA`)
- **Extractor**: `extract_research_data.py`
- **Schema**: `{pipeline: {total_digests, total_findings, total_sources}, fleet: {active_scouts, stale_scouts, coverage_24h, coverage_7d}, synthesis: {latest_date, count}, triage: {open_proposals, top_salience}, health: {score}}`
- **Fallback**: Shows "research-data.js لود نشد" if `R` missing.

### 9. Git Status — ⛓ وضعیتِ گیت
- **Mode**: READ-ONLY
- **Data**: `git-data.js` (`window.GIT_DATA`)
- **Extractor**: `extract_git_status_data.py`
- **Schema**: `{summary: {total_repos, clean_repos, dirty_repos}, repos: [{branch, last_commit: {hash_short, message, author, date_relative}, status: {dirty_total, modified, untracked, ahead, behind}, files: [{status, path}]}]}`
- **Fallback**: Shows "git-data.js لود نشد" if `G` missing.

### 10. Task Queue — ✓ صفِ کارها
- **Mode**: READ-ONLY
- **Data**: `task-summary-data.js` (`window.TASK_SUMMARY_DATA`) — **lightweight default**
- **Full data**: `task-data.js` (`window.TASK_DATA`) — **lazy-loaded on demand**
- **Extractors**: `extract_obsidian_tasks.py` → `extract_task_summary.py`
- **Schema (summary)**: `{open_tasks, done_tasks, total_tasks, completion_rate, by_priority: {بحرانی, بالا, متوسط, کم}, by_project: {...}, next_action: {text, project, priority, file}}`
- **Lazy load**: Click "📂 جزئیات کامل" button to load full `task-data.js` (~678KB).
- **Fallback**: Shows "task-summary-data.js لود نشد" if `TK` missing.

### 11. Ideas Backlog — 💡 بک‌لاگِ ایده‌ها
- **Mode**: READ-ONLY
- **Data**: `ideas-data.js` (`window.IDEAS_DATA`)
- **Extractor**: `extract_ideas_backlog.py`
- **Schema**: `{summary: {total_ideas, avg_strategic_score, ready_to_build_count}, ideas: [{id, title, tier, strategic_score, status, type}]}`
- **Fallback**: Shows "ideas-data.js لود نشد" if `I` missing.

### 12. Project Index — 📁 ایندکسِ پروژه‌ها
- **Mode**: READ-ONLY
- **Data**: `project-data.js` (`window.PROJECT_DATA`)
- **Extractor**: `extract_project_index.py`
- **Schema**: `{summary: {total_projects, active, stalled, average_health}, projects: [{name, status, phase, health, blockers, open_todos, file_count}]}`
- **Fallback**: Shows "project-data.js لود نشد" if `P` missing.

### 13. Telegram Control — 📡 کنترلِ تلگرام
- **Mode**: NOT YET WIRED
- **Data**: `telegram-data.js` (`window.TELEGRAM_DATA`)
- **Extractor**: `extract_telegram_control.py`
- **Schema**: `{channel: {live, mode}, poll: {last_offset, offset_age_hours}, approvals: {total, by_verdict}, queue: {pending_count, approved_count, rejected_count}, budget_gate: {halted}, health: {score, label, emoji}}`
- **State**: `live=false` (stub mode). Bot credentials not configured.
- **Fallback**: Shows "telegram-data.js لود نشد" if `T` missing.

## Navigation

Footer links:
- ‹ هاب (`../worlds/index.html`)
- کاکپیت (`../worlds/01-cockpit/index.html`)
- ریسک (`../worlds/08-risk/index.html`)
- پول (`../worlds/03-money/index.html`)

## Style

- Dark theme with cyan/green/gold/purple accents
- Collapsible panels (click header to toggle)
- Mobile-first (safe-area-inset, max-width 720px)
- Persian (RTL) with English technical terms
