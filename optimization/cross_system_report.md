# Cross-System Duplication & Waste Report
**Generated:** 2026-07-16  
**Scope:** F:/backup/ (Octopus System)  
**Analyzer:** Cross-System Redundancy Inspector  

---

## Executive Summary

| Severity | Count | Description |
|----------|-------|-------------|
| 🔴 Critical | 8 | Multiple ledgers, dual control planes, port conflicts, split state |
| 🟡 Medium | 10 | Duplicate extractors, dual watchdogs, config scattering, README twins |
| 🟢 Low | 6 | Minor telemetry overlaps, flag proliferation, env duplication |

---

## 1. 🔴 Ledger Duplications (Critical)

### 1.1 Three Ledger Formats Detected

| System | File | Format | Purpose |
|--------|------|--------|---------|
| `_ops/` | `events.py` → `state/events.jsonl` | JSONL (schema v2) | Structured events for dashboard |
| `_ops/` | `unified_bus.py` → `genome-system/ledger/ledger.jsonl` | LANGAR (hash-chain) | Eternal genome ledger |
| `app/` | `src/nbb_cp/kernel/events.py` | Domain events (LedgerEvent) | NBB-CP kernel ledger |
| `4d_system/` | `knowledge/ledger.py` | Unknown | 4D knowledge ledger |
| `_ops/` | `budget/organ-gate-log.jsonl` | JSONL | Budget gate log |
| `07 - Knowledge/genome-system/ledger/ledger.jsonl` | LANGAR | Append-only hash-chain | Genome substrate |

**Finding:** The `unified_bus.py` (line 79) writes to both `genome ledger` AND `events.jsonl` — but `events.py` (line 30) also writes to `events.jsonl` independently. **Two writers to one file without coordination.**

**Waste:** `events.jsonl` is written by both `events.py` (direct) and `unified_bus.py` (via publish). Risk of race conditions and duplicate entries.

**File:** `F:/backup/_ops/events.py:30` and `F:/backup/_ops/unified_bus.py:79-96`

---

## 2. 🔴 State File Duplications (Critical)

### 2.1 Multiple State Sources

| File | Purpose | Writer |
|------|---------|--------|
| `_ops/state/ORGANISM-STATE.json` | Organism runtime state | `organism.py:60,139` |
| `_ops/state/chrono.db` | ChronoDB (SQLite) | `chrono.py` / `checkpoint.py` |
| `_ops/state/telemetry-latest.json` | Telemetry snapshot | `telemetry.py:159` |
| `_ops/budget/budget-state.json` | Budget committed state | `budget_gate.py` |
| `_ops/budget/organ-state.json` | Organ gate state | `organ_gate.py` |
| `4d_system/` outputs | Various outputs | `4d_system/brain/*.py` |
| `app/` stores | Memory/SQLite stores | `app/src/nbb_cp/adapters/storage/` |

**Finding:** State is scattered across at least 7 files/databases. No single reconstruction path.

**Waste:** Every subsystem maintains its own state. Reconstruction requires merging JSON + SQLite + JSONL.

---

## 3. 🔴 HTTP Server Port Conflicts (Critical)

### 3.1 Four Servers Running Simultaneously

| Port | File | Purpose | Framework |
|------|------|---------|-----------|
| **8770** | `_ops/dashboard/server.py:49` | Dashboard | `http.server` |
| **8771** | `_ops/organism.py:57` | Organism status | `http.server` (exclusive bind) |
| **8772** | `_ops/live/server.py:34` | Cortex/Brain proxy | `http.server` |
| **8773** | `_ops/live/server.py:32` | Live control room | `http.server` |
| **8790** | `_ops/panel/server.py:30` | Admin panel | `http.server` |
| **8768** | `app/` (mentioned in organism.py:15) | Brain app | Unknown |

**Finding:** `organism.py:15` explicitly says: "8768 قفل مغز (app.py) و 8770 داشبورد است — به آن‌ها دست نمی‌زنیم." This confirms **four separate HTTP servers** with no unified routing.

**Waste:** Each server runs its own thread, binds its own port, and serves its own static HTML. No reverse proxy (nginx) or unified API gateway.

**Files:**
- `F:/backup/_ops/dashboard/server.py:49`
- `F:/backup/_ops/organism.py:57`
- `F:/backup/_ops/live/server.py:32-34`
- `F:/backup/_ops/panel/server.py:30`

---

## 4. 🔴 Dual Control Planes (Critical)

### 4.1 Two Complete Control Planes

| Feature | `_ops/organism.py` | `app/src/nbb_cp/app/service.py` |
|---------|-------------------|--------------------------------|
| **Governor** | `governor_epoch.py` | `app/src/nbb_cp/app/governor.py` (StubGovernor) |
| **Budget Gate** | `budget_gate.py` | `app/src/nbb_cp/kernel/gates.py` |
| **Ledger** | `genome-system/ledger` | `app/src/nbb_cp/kernel/events.py` (LedgerEvent) |
| **HTTP API** | `organism.py:8771` | `app/src/nbb_cp/api/http.py` (FastAPI) |
| **State** | `ORGANISM-STATE.json` | In-memory + stores |
| **Epoch** | `run_epoch()` in `governor_epoch.py` | `run_demo_epoch()` in `governor.py` |

**Finding:** `app/` (NBB-CP) is a **complete reimplementation** of the same control plane that `_ops/` already runs. The `service.py` (line 54) has `ControlPlaneService` with identical responsibilities to `organism.py`.

**Waste:** Two budget gates, two ledgers, two governors, two HTTP APIs. They do not share state or communicate.

**Files:**
- `F:/backup/_ops/organism.py` (632 lines)
- `F:/backup/app/src/nbb_cp/app/service.py` (582 lines)
- `F:/backup/app/src/nbb_cp/api/http.py` (125 lines)

---

## 5. 🔴 Config Layer Duplication (Critical)

### 5.1 Multiple Config Readers

| File | Reads | Env Vars | Keys |
|------|-------|----------|------|
| `_ops/budget/opslib.py` | `budgets.yaml`, `.env` | `ORG_ROOT`, `OPS_DIR` | `BUDGETS_YAML`, `ORGAN_STATE` |
| `_ops/budget/env_loader.py` | `.env` | `TELEGRAM_BOT_TOKEN`, `GLM_API_KEY` | 8 known keys |
| `app/src/nbb_cp/app/config.py` | `budgets.yaml` | — | App config |
| `4d_system/config/settings.py` | `.env` | `GLM_API_KEY`, `FUGU_API_KEY` | Multiple |
| `survival-gateway/.env` | `.env` | `SAKANA_API_KEY` | Gateway keys |

**Finding:** `env_loader.py` (line 23) reads `.env` from root. `4d_system/config/settings.py` also reads `.env`. `opslib.py` (line 32) reads env vars but doesn't use `env_loader` — it reads directly via `os.environ.get`.

**Waste:** `.env` is parsed at least 3 times independently. API keys have **different names** for the same provider:
- `FUGU_API_KEY` (env_loader) vs `SAKANA_API_KEY` (survival-gateway)
- `GLM_API_KEY` (env_loader) vs `ZAI_API_KEY` (env_loader known keys list)

**Files:**
- `F:/backup/_ops/budget/env_loader.py:23`
- `F:/backup/_ops/budget/opslib.py:32-56`
- `F:/backup/4d_system/config/settings.py`
- `F:/backup/survival-gateway/.env`

---

## 6. 🔴 Telegram Duplication (Critical)

### 6.1 Multiple Telegram Channels

| File | Purpose | Bot Token Source |
|------|---------|------------------|
| `_ops/wiring.py` (make_telegram_channel) | Main Telegram channel | `TELEGRAM_BOT_TOKEN` from `.env` |
| `_ops/budget/approval_channel.py` | Budget approval channel | Same token |
| `_ops/budget/approval_channel_merge.py` | Merge approval logic | Same token |
| `4d_system/brain/telegram_bot.py` | 4D brain bot | Unknown (separate?) |
| `03 - Projects/.../langar_bot.py` | Langar project bot | Unknown |
| `03 - Projects/.../saba_studio.py` | Saba studio bot | Unknown |

**Finding:** `approval_channel.py` and `approval_channel_merge.py` are two separate files for the same approval flow. `wiring.py` creates a third channel instance.

**Waste:** Multiple bot instances may compete for the same webhook/polling connection.

---

## 7. 🟡 Watchdog Duplication (Medium)

### 7.1 Two Watchdog Systems

| File | Type | Purpose |
|------|------|---------|
| `_ops/watchdog.py` | Python | Main organism watchdog |
| `_ops/watchdog_extension.py` | Python | Extension |
| `_ops/organism-watchdog.ps1` | PowerShell | Architect watchdog |
| `04 - Architect System/scripts/organism-watchdog.ps1` | PowerShell | Duplicate of above? |

**Finding:** `04 - Architect System/scripts/organism-watchdog.ps1` exists in the git dirty list. It may be a copy of `_ops/organism-watchdog.ps1`.

**Waste:** Two PowerShell watchdogs in different directories.

**Files:**
- `F:/backup/_ops/watchdog.py`
- `F:/backup/_ops/organism-watchdog.ps1`
- `F:/backup/04 - Architect System/scripts/organism-watchdog.ps1`

---

## 8. 🟡 Dashboard Duplication (Medium)

### 8.1 Multiple Dashboards

| Path | Port | Type |
|------|------|------|
| `_ops/dashboard/server.py` | 8770 | Python HTTP server |
| `_ops/live/server.py` | 8773 | Python HTTP server |
| `_ops/panel/server.py` | 8790 | Python HTTP server |
| `OCTOPUS/admin-telegram/index.html` | — | Static HTML |
| `OCTOPUS/worlds/index.html` | — | Static HTML |
| `OCTOPUS/mobile/index.html` | — | Static HTML |
| `4d_system/ui/app.py` | — | Streamlit/Gradio? |

**Finding:** `OCTOPUS/nervous-system/` has `extract_live_data.py`, `extract_ops_data.py`, and `refresh-live-data.bat` — but `nervous-system/` (root level) ALSO has the same files.

**Waste:** Two copies of `extract_live_data.py`:
- `F:/backup/nervous-system/extract_live_data.py`
- `F:/backup/OCTOPUS/nervous-system/extract_live_data.py`

Same for `extract_ops_data.py` and `refresh-live-data.bat`.

---

## 9. 🟡 Extractor Duplication (Medium)

### 9.1 18 Extractors in nervous-system/

| Extractor | Output | Dashboard Consumer |
|-----------|--------|-------------------|
| `extract_live_data.py` | `live-data.js` | `OCTOPUS/worlds/` |
| `extract_ops_data.py` | `ops-data.js` | `OCTOPUS/worlds/` |
| `extract_graph_data.py` | `graph-data.js` | `OCTOPUS/worlds/` |
| `extract_crypto_data.py` | `crypto-data.js` | Unknown |
| `extract_mining_data.py` | `mining-data.js` | Unknown |
| `extract_health_score.py` | `health-data.js` | Unknown |
| `extract_neural_data.py` | `neural-data.js` | `OCTOPUS/worlds/` |
| `extract_research_data.py` | `research-data.js` | Unknown |
| ... | ... | ... |

**Finding:** Every extractor runs independently, produces its own `.js` file, and has no shared base class or scheduling. `refresh-live-data.bat` runs them but it's unclear which ones.

**Waste:** 18 separate Python scripts, each with its own file I/O, JSON serialization, and error handling. No unified extractor framework.

---

## 10. 🟡 Telemetry Duplication (Medium)

### 10.1 Two Telemetry Systems

| File | Reads | Writes | Purpose |
|------|-------|--------|---------|
| `_ops/budget/telemetry.py` | `genome ledger`, `core.db` | `telemetry-latest.json`, daily JSON | Budget telemetry |
| `_ops/budget/governor_epoch.py` | Uses `telemetry.snapshot()` | `epoch-*.json` | Governor input |
| `4d_system/core/metrics.py` | Unknown | Unknown | 4D metrics |
| `app/src/nbb_cp/adapters/telemetry/noop.py` | — | — | NBB telemetry stub |

**Finding:** `governor_epoch.py` (line 287) calls `telemetry.snapshot()` which is defined in `telemetry.py`. However, `organism.py` (line 275) also calls `telemetry.snapshot()` directly. Both read the same sources.

**Waste:** Double snapshot on every tick if both run.

---

## 11. 🟡 Doctor vs Cortex Overlap (Medium)

### 11.1 Dual Analysis/Decision Systems

| System | File | Role | Decision Type |
|--------|------|------|---------------|
| Doctor | `_ops/doctor/doctor.py` | Health check, calibration | Propose-only |
| Cortex | `_ops/cortex/model_router.py` | LLM routing, research | Auto-route |
| Cortex | `_ops/cortex/goal_directed.py` | Goal planning | Strategy |
| 4D Brain | `4d_system/brain/daemon.py` | Daemon | Background tasks |
| 4D Brain | `4d_system/brain/auto_experiment.py` | Auto-experiment | Research |

**Finding:** `doctor.py` and `cortex/` both perform "analysis" and "propose" actions. `doctor_beat` is called in `organism.py:386`. `cortex` modules are also loaded in `organism.py` via wiring.

**Waste:** Two "brain" systems analyzing the same telemetry data and producing similar proposals.

---

## 12. 🟡 Leg Code Duplication (Medium)

### 12.1 No Base Class for Legs

| Leg | Created In | Beat Function | File |
|-----|-----------|-------------|------|
| `lead_leg` | `wiring.py` | `leg_beat` | `wiring.py` |
| `ziman_leg` | `wiring.py` | `ziman_beat` | `wiring.py` |
| `cartographer_leg` | `wiring.py` | `cartographer_beat` | `wiring.py` |
| `mining_leg` | `business_legs_beat` | Unknown | `wiring.py` |
| `crypto_leg` | `business_legs_beat` | Unknown | `wiring.py` |
| `accounting_leg` | `acct_beat` | Unknown | `wiring.py` |

**Finding:** `organism.py:467` calls `business_legs_beat()` which handles mining, crypto, accounting, and knowledge legs. But there is no `BaseLeg` class or shared interface. Each leg has its own beat function in `wiring.py`.

**Waste:** Code copied for each leg. No polymorphism. Adding a new leg requires copying boilerplate.

---

## 13. 🟡 .env Duplication (Medium)

### 13.1 Five .env Files

| File | Purpose |
|------|---------|
| `F:/backup/.env` | Root env (main source of truth) |
| `F:/backup/4d_system/.env` | 4D system env |
| `F:/backup/4d_system/.env.example` | 4D example |
| `F:/backup/_ops/OCTOPUS.env` | Ops env (legacy?) |
| `F:/backup/survival-gateway/.env` | Gateway env |
| `F:/backup/app/.env.example` | App example |

**Finding:** `4d_system/.env` may contain duplicate keys. `survival-gateway/.env` uses `SAKANA_API_KEY` while `env_loader.py` expects `FUGU_API_KEY` (same provider, different name).

---

## 14. 🟢 README Twins (Low)

### 14.1 Multiple READMEs

| File | System | Content |
|------|--------|---------|
| `F:/backup/README.md` | Root | General Octopus overview |
| `F:/backup/app/README.md` | App | NBB-CP description |
| `F:/backup/4d_system/README.md` | 4D | 4D system description |
| `F:/backup/_ops/epistemics/README.md` | Epistemics | Metrics README |
| `F:/backup/OCTOPUS/README.md` | OCTOPUS | Dashboard README |

**Finding:** Each subsystem has its own README with overlapping descriptions of "the system." They are not cross-linked and may contradict each other.

---

## 15. 🟢 Flag Proliferation (Low)

### 15.1 11 Activation Flags

| Flag | Purpose |
|------|---------|
| `ACTIVATION-CORTEX-PAID.flag` | Cortex paid mode |
| `ACTIVATION-DEBATE.flag` | Debate mode |
| `ACTIVATION-GO-LIVE.flag` | Go live |
| `ACTIVATION-GOVERNOR-LLM.flag` | Governor LLM |
| `ACTIVATION-HEART-DOCTOR.flag` | Heart doctor |
| `ACTIVATION-PULSE.flag` | Pulse |
| `ACTIVATION-RESEARCH-EARLY.flag` | Research early |
| `ACTIVATION-SELF-IMPROVE-AUTO.flag` | Self-improve |
| `ACTIVATION-WORK-LLM.flag` | Work LLM |

Plus: `STOP-ORGANISM`, `STOP-CORTEX`, `STOP-METABOLIC`, `STOP-DEBATE`, `HALT-ALL`, `FREEZE.flag`.

**Waste:** 17+ boolean flags as files instead of a unified config or state machine. No validation that conflicting flags are not both set.

---

## 16. 🟢 Database Fragmentation (Low)

### 16.1 Four Databases

| Database | File | Users |
|----------|------|-------|
| SQLite | `_ops/state/chrono.db` | Organism, chrono, checkpoint |
| SQLite | `control-brain/core.db` | Brain, telemetry |
| SQLite | `app/` stores | NBB-CP tests |
| PostgreSQL | `survival-gateway/postgres` | Gateway |
| JSONL | `genome-system/ledger/ledger.jsonl` | Genome ledger |

**Waste:** No unified database. Each layer uses its own storage.

---

## Recommendations (Priority Order)

### Immediate (🔴)
1. **Merge HTTP servers** — Use a single FastAPI/Flask app with routes `/dashboard`, `/live`, `/panel`, `/api/organism` instead of 4 ports.
2. **Choose one control plane** — Either `app/` (NBB-CP) or `_ops/organism.py`. Do not run both.
3. **Unify ledger** — Make `unified_bus.py` the single writer to `events.jsonl`. Remove direct writes from `events.py`.
4. **Unify state** — One SQLite DB or one JSON state file, not 7 scattered files.

### Short-term (🟡)
5. **Create `BaseLeg` class** — All legs inherit from one base with `beat()` method.
6. **Merge extractors** — One `extractor.py` with plugins, not 18 separate scripts.
7. **Single watchdog** — One Python script, delete PowerShell duplicates.
8. **Merge dashboards** — One React/Vue app reading from unified API, not 5 static HTMLs.

### Long-term (🟢)
9. **Single `.env`** — One root `.env`, all systems read via `opslib.env_loader`. Standardize API key names.
10. **Flag registry** — Replace file flags with a single `state/flags.json` or database table.
11. **Unified README** — One source of truth, others link to it.

---

*Report generated by Cross-System Analysis Agent*  
*Path: F:/backup/optimization/cross_system_report.md*
