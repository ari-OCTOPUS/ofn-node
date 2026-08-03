---
type: map
project: OCTOPUS
status: active
wave: 4
tags: [octopus, admin, dashboard, ui, panels, reference]
created: 2026-07-13
updated: 2026-07-13
---

# OCTOPUS · Admin Telegram Dashboard Map

> **What this is:** A complete mapping of all 13 panels in `OCTOPUS/admin-telegram/index.html` to their data sources, schemas, and UI consumers.
> **Scope:** Panel name, data variable, extractor, output file, mode label, fallback behavior, and cross-references.
> **File:** `OCTOPUS/admin-telegram/index.html`
> **Last synced:** 2026-07-13

---

## Dashboard Architecture

```
┌─────────────────────────────────────────┐
│  SYSTEM MODE BANNER (Wave 5 addition)   │
├─────────────────────────────────────────┤
│  Panel 1: Vitals                        │
│  Panel 2: Queue                         │
│  Panel 3: Health                        │
│  Panel 4: Neural                        │
│  Panel 5: Wallet (collapsed)            │
│  Panel 6: Mining (collapsed)            │
│  Panel 7: Crypto (collapsed)            │
│  Panel 8: Research/Scout (collapsed)    │
│  Panel 9: Git Status (collapsed)        │
│  Panel 10: Task Queue (collapsed)       │
│  Panel 11: Ideas Backlog (collapsed)    │
│  Panel 12: Project Index (collapsed)    │
│  Panel 13: Telegram Control (collapsed) │
├─────────────────────────────────────────┤
│  Navigation → Hub / Cockpit / Risk / $$ │
└─────────────────────────────────────────┘
```

---

## Panel Registry

### Panel 1 · وضعیتِ زنده (Vitals)

| Attribute | Value |
|---|---|
| **Data var** | `L = LIVE_DATA`, `O = OPS_DATA` |
| **Extractor** | `extract_live_data.py`, `extract_ops_data.py` |
| **Output file** | `live-data.js`, `ops-data.js` |
| **Key schema** | `L.sog.identity_now`, `L.budget.remaining`, `L.daemon.total_ticks`, `O.time.wires_on` |
| **Mode** | `READ-ONLY` |
| **Fallback** | "⚠ داده لود نشد — extract_live_data.py را اجرا کن" + 🔴 offline chip |
| **Worlds using** | 01-cockpit, 08-risk, hub |
| **Channel** | Foundation (no CH number) |

---

### Panel 2 · صفِ تأیید (Queue)

| Attribute | Value |
|---|---|
| **Data var** | `Q = QUEUE_DATA` |
| **Extractor** | `extract_queue_data.py` |
| **Output file** | `queue-data.js` |
| **Key schema** | `Q.queue.items[]`, `Q.queue.counts.pending` |
| **Mode** | `OWNER VERDICT REQUIRED` + `PROPOSE-ONLY` |
| **Fallback** | "صف خالی است" + "هیچ موردی برای تأیید نیست" |
| **Actions** | Approve one, Reject one, Approve all, Reject all, Refresh |
| **Action wiring** | `actOne()` / `actAll()` log only — "propose-only → need owner verdict in Telegram" |
| **Channel** | CH-14 |

---

### Panel 3 · سلامتِ سیستم (Health)

| Attribute | Value |
|---|---|
| **Data var** | `H = HEALTH_DATA` |
| **Extractor** | `extract_health_score.py` |
| **Output file** | `health-data.js` |
| **Key schema** | `H.overall`, `H.subscores.system`, `H.subscores.fitness`, `H.subscores.telemetry` |
| **Mode** | `READ-ONLY` |
| **Fallback** | "🔴 health — health-data.js لود نشد" |
| **Worlds using** | 01-cockpit |
| **Channel** | CH-07 |
| **Known issue** | Wave 4 fixed null-reference on `H.overall` and `H.subscores.system` |

---

### Panel 4 · شبکهٔ عصبی (Neural)

| Attribute | Value |
|---|---|
| **Data var** | `N = NEURAL_DATA` |
| **Extractor** | `extract_neural_data.py` |
| **Output file** | `neural-data.js` |
| **Key schema** | `N.rhythm.mode_color`, `N.rhythm.T_beat`, `N.circadian.readiness`, `N.rhythm.stress` |
| **Mode** | `READ-ONLY` |
| **Fallback** | "🔴 neural — neural-data.js لود نشد" |
| **Worlds using** | All 10 worlds + hub |
| **Channel** | CH-16 |

---

### Panel 5 · کیف پول / eToro (Wallet)

| Attribute | Value |
|---|---|
| **Data var** | `WL = WALLET_DATA` |
| **Extractor** | `extract_wallet_data.py` |
| **Output file** | `wallet-data.js` |
| **Key schema** | `WL.gate.security_gate`, `WL.portfolio.position_count`, `WL.budget.remaining` |
| **Mode** | `SHADOW MODE` (advisory only — no trades executed from UI) |
| **Fallback** | "🔴 wallet — wallet-data.js لود نشد" |
| **Details** | Blockers list, hard rules, copy button |
| **Worlds using** | 03-money |
| **Channel** | CH-08 (wallet half) |

---

### Panel 6 · ⛏ ماینینگ (Mining)

| Attribute | Value |
|---|---|
| **Data var** | `M = MINING_DATA` |
| **Extractor** | `extract_mining_data.py` |
| **Output file** | `mining-data.js` |
| **Key schema** | `M.fleet.electricity_mood`, `M.readiness.score`, `M.security.gates`, `M.coins.top_candidates` |
| **Mode** | `SHADOW MODE` (advisory — no actual mining control) |
| **Fallback** | "🔴 mining — mining-data.js لود نشد" |
| **Details** | Readiness breakdown, security gates (PASS/FAIL), coin candidates with toggle |
| **Worlds using** | 03-money |
| **Channel** | CH-09 |
| **Known issue** | Empty coin hunter cache → "کاندیدی یافت نشد" |

---

### Panel 7 · 📈 کریپتو / eToro (Crypto)

| Attribute | Value |
|---|---|
| **Data var** | `C = CRYPTO_DATA` |
| **Extractor** | `extract_crypto_data.py` |
| **Output file** | `crypto-data.js` |
| **Key schema** | `C.composite.score`, `C.registry.positions_active_count`, `C.blockers[]`, `C.lunarcrush.summary` |
| **Mode** | `SHADOW MODE` (advisory — no trades executed from UI) |
| **Fallback** | "🔴 crypto — crypto-data.js لود نشد" |
| **Details** | Blockers list, LunarCrush signals, CryptoQuant aggregate, top buy coins |
| **Worlds using** | 03-money |
| **Channel** | CH-08 (crypto half) |
| **Known issue** | LunarCrush often stale; registry empty on first run |

---

### Panel 8 · 🔬 اسکاوت / تحقیق (Research / Scout)

| Attribute | Value |
|---|---|
| **Data var** | `R = RESEARCH_DATA` |
| **Extractor** | `extract_research_data.py` |
| **Output file** | `research-data.js` |
| **Key schema** | `R.pipeline.total_digests`, `R.fleet.active_scouts`, `R.fleet.stale_scouts`, `R.health.score` |
| **Mode** | `READ-ONLY` |
| **Fallback** | "🔴 research — research-data.js لود نشد" |
| **Details** | Source/spore/cross-domain counts, coverage 24h/7d, synthesis date, triage proposals, stale scout list |
| **Worlds using** | 01-cockpit |
| **Channel** | CH-01 |

---

### Panel 9 · ⛓ وضعیتِ گیت (Git Status)

| Attribute | Value |
|---|---|
| **Data var** | `G = GIT_DATA` |
| **Extractor** | `extract_git_status_data.py` |
| **Output file** | `git-data.js` |
| **Key schema** | `G.repos[0].branch`, `G.repos[0].status.dirty_total`, `G.repos[0].last_commit`, `G.summary` |
| **Mode** | `READ-ONLY` |
| **Fallback** | "🔴 git — git-data.js لود نشد" |
| **Details** | Commit message, author, modified/untracked/ahead/behind counts, file list toggle (cap 20) |
| **Worlds using** | None yet (Wave 5 may add to 01-cockpit) |
| **Channel** | CH-02 |

---

### Panel 10 · ✓ صفِ کارها (Task Queue)

| Attribute | Value |
|---|---|
| **Data var** | `TK = TASK_DATA` (or `TASK_SUMMARY_DATA` after Wave 5) |
| **Extractor** | `extract_obsidian_tasks.py` + `extract_task_summary.py` |
| **Output file** | `task-data.js` (~677 KB) / `task-summary-data.js` (~0.5 KB) |
| **Key schema** | `TK.summary.open_tasks`, `TK.summary.done_tasks`, `TK.summary.by_priority`, `TK.summary.next_action` |
| **Mode** | `READ-ONLY` |
| **Fallback** | "🔴 tasks — task-data.js لود نشد" |
| **Details** | Priority breakdown, files scanned, next action text/project/priority/file |
| **Worlds using** | 01-cockpit |
| **Channel** | CH-05 |
| **Known issue** | 677 KB payload; Wave 5 switches default to summary + lazy-load full |

---

### Panel 11 · 💡 بک‌لاگِ ایده‌ها (Ideas Backlog)

| Attribute | Value |
|---|---|
| **Data var** | `I = IDEAS_DATA` |
| **Extractor** | `extract_ideas_backlog.py` |
| **Output file** | `ideas-data.js` (~83 KB) |
| **Key schema** | `I.summary.total_ideas`, ideas filtered by `tier` (gold/silver/bronze), `ready_to_build_count` |
| **Mode** | `READ-ONLY` |
| **Fallback** | "🔴 ideas — ideas-data.js لود نشد" |
| **Details** | Top 5 ideas with tier emoji + strategic score, avg strategic score |
| **Worlds using** | None yet (Wave 5 may add to 07-decision) |
| **Channel** | CH-12 |
| **Known issue** | 83 KB payload; consider summary mode for preview |

---

### Panel 12 · 📁 ایندکسِ پروژه‌ها (Project Index)

| Attribute | Value |
|---|---|
| **Data var** | `P = PROJECT_DATA` |
| **Extractor** | `extract_project_index.py` |
| **Output file** | `project-data.js` (~4.4 KB) |
| **Key schema** | `P.summary.total_projects`, `P.summary.active`, `P.summary.stalled`, `P.summary.average_health`, `P.projects[]` |
| **Mode** | `READ-ONLY` |
| **Fallback** | "🔴 projects — project-data.js لود نشد" |
| **Details** | Per-project cards: name, health %, phase, autonomy, blockers, todos, file count |
| **Worlds using** | None yet |
| **Channel** | CH-13 |

---

### Panel 13 · 📡 کنترلِ تلگرام (Telegram Control)

| Attribute | Value |
|---|---|
| **Data var** | `T = TELEGRAM_DATA` |
| **Extractor** | `extract_telegram_control.py` |
| **Output file** | `telegram-data.js` (~1.9 KB) |
| **Key schema** | `T.channel.live`, `T.health.score`, `T.approvals.total`, `T.budget_gate.halted`, `T.admin_actions.needs_attention` |
| **Mode** | `READ-ONLY` + `PROPOSE-ONLY` (actions logged, not executed) |
| **Fallback** | "🔴 telegram — telegram-data.js لود نشد" |
| **Details** | Poll offset age, recent approvals, queue counts, budget spent, attention flag |
| **Channel** | CH-15 |
| **Known issue** | Stub mode when `TELEGRAM_BOT_TOKEN` missing |

---

## Data Load Order

`index.html` loads scripts in this order:

```html
<script src="../../nervous-system/live-data.js"></script>      <!-- L -->
<script src="../../nervous-system/ops-data.js"></script>        <!-- O -->
<script src="../../nervous-system/health-data.js"></script>     <!-- H -->
<script src="../../nervous-system/queue-data.js"></script>      <!-- Q -->
<script src="../../nervous-system/neural-data.js"></script>     <!-- N -->
<script src="../../nervous-system/watchdog-data.js"></script>   <!-- W -->
<script src="../../nervous-system/crypto-data.js"></script>     <!-- C -->
<script src="../../nervous-system/mining-data.js"></script>     <!-- M -->
<script src="../../nervous-system/wallet-data.js"></script>     <!-- WL -->
<script src="../../nervous-system/research-data.js"></script>   <!-- R -->
<script src="../../nervous-system/git-data.js"></script>        <!-- G -->
<script src="../../nervous-system/task-data.js"></script>       <!-- TK -->
<script src="../../nervous-system/ideas-data.js"></script>      <!-- I -->
<script src="../../nervous-system/project-data.js"></script>    <!-- P -->
<script src="../../nervous-system/telegram-data.js"></script>   <!-- T -->
<script src="../worlds/octo-data.js"></script>                  <!-- shared core -->
```

**Total script payload:** ~1.07 MB (largely due to `task-data.js` 677 KB + `live-data.js` 141 KB + `graph-data.js` 107 KB)

---

## Mode Label Mapping (Wave 5 Target)

| Panel | Target Mode | Rationale |
|---|---|---|
| Vitals | `READ-ONLY` | Display only |
| Queue | `OWNER VERDICT REQUIRED` | Actions need owner approval |
| Health | `READ-ONLY` | Display only |
| Neural | `READ-ONLY` | Display only |
| Wallet | `SHADOW MODE` | Advisory; no trade execution |
| Mining | `SHADOW MODE` | Advisory; no actual mining control |
| Crypto | `SHADOW MODE` | Advisory; no trade execution |
| Research | `READ-ONLY` | Display only |
| Git Status | `READ-ONLY` | Display only |
| Task Queue | `READ-ONLY` | Display only |
| Ideas Backlog | `READ-ONLY` | Display only |
| Project Index | `READ-ONLY` | Display only |
| Telegram Control | `READ-ONLY` + `PROPOSE-ONLY` | Status display + action proposals |

---

## Backlinks

- [[OCTOPUS-CHANNEL-REGISTRY]] — channels feeding these panels
- [[OCTOPUS-EXTRACTOR-REGISTRY]] — extractors producing the data
- [[OCTOPUS-WAVE5-HARDENING-PLAN]] — panel hardening objectives
- [[Wave-4|Wave-4 · Full Channel Fleet]] — when these panels were built
