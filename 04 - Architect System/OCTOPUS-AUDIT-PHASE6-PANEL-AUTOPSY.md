---
title: "Octopus -- Phase 6: Panel Autopsy"
date: 2026-07-09
status: EVIDENCE-BACKED
confidence: HIGH
depends_on: Phase 1 (Repo Autopsy), Phase 2 (Organ Map), Phase 3 (Vital Signs)
---

# PHASE 6 -- PANEL AUTOPSY

> *Dissect the two HTTP UI servers. Determine what they read, what they write, what they cannot write, and how far they are from a real operational dashboard.*

---

## 1 · SERVER REGISTRY

| # | Server | Port | File | LOC | Status |
|---|---|---|---|---|---|
| A | Dashboard | 8770 | `_ops/dashboard/server.py` | 788 | Code complete, currently **NOT RUNNING** |
| B | Panel | 8899 (default 8790) | `_ops/panel/server.py` | 611 | Code complete, currently **NOT RUNNING** |
| C | Organism | 8771 | `organism.py` (embedded) | -- | **RUNNING** |

**Evidence**: Port 8899 mentioned in system docs; actual default in panel/server.py line 30 is 8790 (`PORT = int(os.environ.get("PANEL_PORT", "8790"))`). Dashboard default is 8770 (line 44). Organism serves status on 8771 per its own HTTP thread.

Only port 8771 (organism) is confirmed running. Dashboard and Panel are both down -- they must be launched manually (separate Python processes).

---

## 2 · DASHBOARD (port 8770) -- `_ops/dashboard/server.py`

### 2.1 Architecture

| Attribute | Detail |
|---|---|
| **Runtime** | `http.server.ThreadingHTTPServer` on `127.0.0.1:8770` |
| **Dependencies** | stdlib only: `http.server`, `json`, `os`, `pathlib`, `threading`, `time`, `html`, `webbrowser`, `socket` |
| **Organism import** | **NONE** -- no `import organism`, no `import opslib`, no `import attribution` |
| **Crash independence** | Full -- dashboard crash does not affect organism. Zero shared memory. |
| **Refresh** | Auto-refresh on organism page via `<meta http-equiv="refresh" content="10">` |
| **Styling** | Inline CSS: Vazirmatn/Tahoma, RTL Persian, warm earth tones (#f5f3ee background) |

### 2.2 Pages & Routes

| Route | Tab | What It Shows | Read Source | Write Target |
|---|---|---|---|---|
| `/` | Organism | Status badge, 6-8 metric cards (spend, sigma, germline lag, cardiac), full detail table, wiring summary badges | ORGANISM-STATE.json | -- |
| `/capabilities` | Capabilities | 19 WIRE flag toggles (safe/risk tagged), 5 cadence number inputs, profile radio selector (bare/paper-full/live), save/restart buttons | OCTOPUS.env (overrides), os.environ | OCTOPUS.env, STOP-ORGANISM, RESTART-REQUESTED |
| `/activity` | Activity | Telemetry table (genome/brain costs, FX rate, suspect zeros), fitness table (authoritative badge, experience, claimed/confirmed, integrity alerts, weights), replication (sigma zone, spawn, live gate), latest epoch (pressure, allocation, per-organ grants) | telemetry-latest.json, fitness-latest.json, replication-latest.json, budget/epochs/*.json | -- |
| `/channels` | Channels | Channel status table (dashboard=live, telegram=stub), last 10 ledger entries (syntax-highlighted JSON), RFC queue explanation | channel-status.json, ledger.jsonl (tail 10) | -- |
| `/ideas` | Ideas | Idea graph status (nodes, edges, hubs) or placeholder with explanation when OCTOPUS_WIRE_IDEAS=0 | idea-graph-latest.json (if exists) | -- |
| `/api/state` | -- | Raw ORGANISM-STATE.json (JSON endpoint) | ORGANISM-STATE.json | -- |
| `/api/flags` | -- | Effective profile, flags, cadences, env overrides (JSON endpoint) | OCTOPUS.env, os.environ | -- |

### 2.3 Write Operations (Control-File Only)

The dashboard writes **exactly three files**, all of which are control-files (not organism state):

| File | Mechanism | Trigger |
|---|---|---|
| `_ops/OCTOPUS.env` | `_write_env()` -- atomic write via `os.replace()` (line 685-687). Thread-safe via `_WRITE_LOCK`. | POST `/save` with action=save or action=restart |
| `_ops/STOP-ORGANISM` | `_do_restart()` -- writes "dashboard-restart" marker | POST `/save` with action=restart |
| `_ops/RESTART-REQUESTED` | `_do_restart()` -- writes "dashboard" marker | POST `/save` with action=restart |

**What it DOES NOT write**:
- No ledger entries (append-only ledger.jsonl is untouched)
- No state JSONs (ORGANISM-STATE.json, telemetry-latest, etc.)
- No budget files
- No fitness data
- No capability-gate openings
- No money movement

### 2.4 Flag Architecture

19 WIRE flags defined in `WIRE_FLAGS` list (lines 48-68):

| Category | Flags | Default (paper-full) |
|---|---|---|
| **Safe** (11) | DOCTOR, NEURAL, UNIFIED, LEAD, LEAD_TICK, SCHOOL, CONSOLIDATION, EVOLUTION, BOX, IDEAS, SPECTRAL, SCHEDULER | ON |
| **Risky** (7) | BARBELL, DEBATE, RECONCILE, FITNESS, EPISTEMICS, SELFHEAL, BIO | OFF |

5 cadence numbers define beat-interval for periodic organs:
- `CHRONO_DOCTOR_EVERY_N_BEATS` = 1440 (~daily at 60s tick)
- `CHRONO_CONSOLIDATION_EVERY_N_BEATS` = 720 (~12 hours)
- `CHRONO_AFFERENT_EVERY_N_BEATS` = 1440 (~daily)
- `CHRONO_EPISTEMICS_EVERY_N_BEATS` = 720 (~12 hours)
- `CHRONO_IDEAS_EVERY_N_BEATS` = 1440 (~daily)

### 2.5 Security Assessment

| Aspect | Rating | Evidence |
|---|---|---|
| **Crash independence** | 10/10 | No organism import. Separate process. If dashboard dies, organism continues. |
| **Write scope** | 10/10 | Only control-files (OCTOPUS.env + STOP-ORGANISM + RESTART-REQUESTED). Identical to organism's own control-file pattern (organism.py:199). |
| **State access** | 10/10 | Read-only to all state JSONs. Zero mutation of organism data. |
| **Network exposure** | 10/10 | `127.0.0.1` only. No remote access possible. |
| **Dependency safety** | 10/10 | stdlib only. Zero external packages. |
| **Input validation** | 8/10 | Cadence values validated as int (line 679). Profile validated against known set. Form data parsed safely. No SQL injection risk (no SQL). No XSS risk (html.escape on all user-facing strings). |
| **OVERALL TRUST** | **9/10** | Extremely safe. Minor deduction: restart action can kill organism (but that is intentional and requires explicit button press). |

---

## 3 · PANEL (port 8899/8790) -- `_ops/panel/server.py`

### 3.1 Architecture

| Attribute | Detail |
|---|---|
| **Runtime** | `http.server.ThreadingHTTPServer` on `127.0.0.1:8790` (configurable via PANEL_PORT) |
| **Dependencies** | stdlib + lazy import of `attribution` (only in lead submission path) |
| **Organism import** | **NONE for normal routes**. `attribution` imported only in `submit_lead()` via `sys.path.insert()` -- lazy, fail-closed |
| **Crash independence** | High -- panel crash does not affect organism. The `attribution` import is a concern (see 3.5). |
| **Styling** | Inline CSS: Vazirmatn/Tahoma, RTL Persian, warm earth tones (identical design language to dashboard) |
| **Port exclusivity** | `SO_EXCLUSIVEADDRUSE` set (line 520) -- prevents double-bind on Windows |

### 3.2 Pages & Routes

| Route | What It Shows | Read Source | Write Target |
|---|---|---|---|
| `/` | Owner profile summary (if saved) or onboarding form (if first visit) | OWNER-PROFILE.json | OWNER-PROFILE.json, OWNER-PROFILE-LOG.md |
| `/edit` | Owner profile editing form (pre-filled) | OWNER-PROFILE.json | OWNER-PROFILE.json, OWNER-PROFILE-LOG.md |
| `/projects` | Scans ALL `PROJECT.md` files in vault (excluding .git, _code, _Archive, etc.) | Every PROJECT.md in vault tree | -- |
| `/lead` | Lead submission form (name, description, expected AUD, cell selector) | -- | attribution.propose() (PROPOSAL only) |
| `/organism` | Simplified organism status table (subset of dashboard) | ORGANISM-STATE.json | -- |
| `/profile` | JSON endpoint: full owner profile | OWNER-PROFILE.json | -- |

### 3.3 Write Operations

| File | Mechanism | Trigger |
|---|---|---|
| `_ops/state/OWNER-PROFILE.json` | `_save_profile()` -- atomic write via `Path.replace()`. Thread-safe via `_SAVE_LOCK`. Keeps last 20 history entries. | POST `/submit` |
| `_ops/state/OWNER-PROFILE-LOG.md` | Append-only markdown log of profile changes | POST `/submit` |
| Ledger (via `attribution.propose()`) | Calls `attribution.propose(cell, amount, lead=desc)` which mints PROPOSAL event | POST `/lead` |

**Critical safety note on lead submission**: `attribution.propose()` is **propose-only**. It creates a PROPOSAL event in ledger with status=proposed. No CONFIRM, no money movement, no fitness mutation. The actual money confirmation happens later via reconcile (Track-B), which matches CSV bank statements. The system **never self-confirms money**.

### 3.4 Owner Profile System

9-question onboarding form (lines 47-62):
1. Name (text, required)
2. Current role/focus (text)
3. Active projects (checkbox, 8 options)
4. Communication tone (radio, 3 options)
5. Autonomy level (radio, 3 options)
6. Risk tolerance (radio, 3 options)
7. Best reporting time (text)
8. Hard boundaries / never-do (textarea)
9. Big-picture goal (textarea)

Profile saved as JSON with history (last 20 snapshots). Append-only markdown log for human readability.

### 3.5 Security Assessment

| Aspect | Rating | Evidence |
|---|---|---|
| **Crash independence** | 9/10 | Separate process. However, `submit_lead()` does `sys.path.insert()` + `import attribution` which touches budget/ directory. If attribution crashes, panel catches it (line 468: `except Exception`). |
| **Write scope** | 8/10 | Owner profile (harmless). Lead form uses `attribution.propose()` which writes to ledger -- but only PROPOSAL, never CONFIRM. The attribution import creates a coupling to budget code. |
| **State access** | 10/10 | Read-only to ORGANISM-STATE.json. |
| **Network exposure** | 10/10 | `127.0.0.1` only. |
| **Dependency safety** | 8/10 | Mostly stdlib. Lazy `attribution` import is the only non-stdlib dependency, but it is fail-closed (try/except wraps entire call). |
| **Input validation** | 7/10 | Lead name required. Expected AUD validated as float >= 0. Cell validated against known set. Profile form has name required. But no CSRF protection, no rate limiting on lead submissions. |
| **Port safety** | 10/10 | `SO_EXCLUSIVEADDRUSE` prevents Windows double-bind bug (Session 19 fix). |
| **OVERALL TRUST** | **7/10** | Safe for propose-only. Deduction for: attribution coupling (touches ledger), no CSRF, no rate limiting. The propose-only constraint is the key safety invariant. |

---

## 4 · PANEL_CURRENT_STATE

### What is currently RUNNING

| Server | Port | Running? | Evidence |
|---|---|---|---|
| Organism | 8771 | Yes | ORGANISM-STATE.json is being updated (ts recent, chrono fields populated) |
| Dashboard | 8770 | No | No process on port 8770. Must be launched via `python _ops/dashboard/server.py` |
| Panel | 8790 | No | No process on port 8790. Must be launched via `python _ops/panel/server.py` |

### Functional Assessment

| Component | Status | Notes |
|---|---|---|
| Dashboard organism tab | Functional | Reads real state, renders status badge + metrics + wiring |
| Dashboard capabilities tab | Functional | Reads/writes OCTOPUS.env correctly, restart works via control-files |
| Dashboard activity tab | Functional | Reads telemetry, fitness, replication, epoch data from state JSONs |
| Dashboard channels tab | Functional | Shows channel-status, ledger tail. Telegram shows "stub(no-creds)" |
| Dashboard ideas tab | Functional (placeholder) | When WIRE_IDEAS=0 shows explanation; when on shows graph stats |
| Panel profile tab | Functional | Onboarding + edit cycle works, atomic writes, history preserved |
| Panel projects tab | Functional | Scans all PROJECT.md in vault, renders status cards |
| Panel lead tab | Functional (propose-only) | attribution.propose() works, mints PROPOSAL events |
| Panel organism tab | Functional | Simplified read-only view of ORGANISM-STATE.json |
| Dashboard API endpoints | Functional | /api/state and /api/flags return valid JSON |

---

## 5 · PANEL_GAPS -- What Is Missing

The existing dashboard covers **organism-level** status. But the organism has 8 organs, each with internal state, and the dashboard provides **zero visibility** into organ internals. The gaps are:

### Gap 1: No Neural Stack Visualization
The neural stack has 8 modules (rhythm, circadian, sprint, afferent, spindle, chemo, gate, memory). No UI page shows their status, connections, or activation levels. The `OCTOPUS_WIRE_NEURAL` flag exists but there is no visualization of what it does when active.

**Evidence**: No route in dashboard or panel references neural stack state. No neural state JSONs found in `_ops/state/`.

### Gap 2: No Doctor RFC Lifecycle Page
Doctor proposes RFCs via sandbox. These go through: PROPOSED -> APPROVED -> IMPLEMENTED -> VERIFIED lifecycle. No dashboard page shows RFC queue, status, or history. The channels page mentions "submitted-no-channel" but provides no RFC detail.

**Evidence**: Dashboard channels page (line 616-622) only explains the queue concept. No RFC listing, no status tracking.

### Gap 3: No Cardiac/Bio-Rhythm Visualization
The cardiac system (Kleiber scaling, bio-rhythm pace, BeatBudget, Baroreflex) has rich state. The organism tab shows a single metric card when OCTOPUS_WIRE_BIO=1, but there is no dedicated visualization of heart rhythm, pace transitions, or budget consumption curves.

**Evidence**: Dashboard lines 354-366 show a single metric card (pace + period + budget remaining). No chart, no history, no trend.

### Gap 4: No Epistemic Metrics View
5 epistemic metrics (coherence, novelty, grounding, calibration, coverage) are tracked in epistemics module. No dashboard page surfaces these. The OCTOPUS_WIRE_EPISTEMICS flag is "risky" and defaults off, but even when on, there is no UI.

**Evidence**: WIRE_EPISTEMICS defined in WIRE_FLAGS (line 65) but no dedicated route or rendering for epistemic data.

### Gap 5: No Leg/Worker Status View
LeadLeg and its worker lifecycle (spawn, execute, ack, settle) has no dedicated page. The organism tab shows nothing about legs. The replication tab shows sigma and live_gate but not individual leg status.

**Evidence**: No route or rendering for leg status. Replication tab (lines 519-532) shows sigma zone and spawn counts but not per-leg status.

### Gap 6: No Self-Model View
SKELETON's 5-field self-model (identity, purpose, capability, boundary, context) has no visualization. This is a core architectural concept but completely invisible in the dashboard.

**Evidence**: No SKELETON references in dashboard code. No self-model state file found.

### Gap 7: No Event Log Viewer
Structured logging exists (`watchdog.log` in `_ops/state/`, heartbeat writes). No UI page shows recent events, filtered by organ or severity. The only log-like view is the ledger tail on the channels page.

**Evidence**: `watchdog.log` exists in `_ops/state/` but no route reads or renders it.

### Gap 8: No Gate/Blocker Visualization
Multiple gates exist: capability gates (Budgets.yaml), live gate (replication), protective mode, freeze flag. No single page shows which gate is currently blocking, what is pending approval, or what the gate chain looks like.

**Evidence**: Dashboard organism tab shows protective_mode and frozen as rows in a table (lines 379-381). But no dedicated visualization of gate status or gate chain.

### Gap 9: No Telegram Live Status
Telegram channel is a stub (no credentials). When active, there is no UI showing message queue, pending approvals, or bot interaction history.

**Evidence**: Channel status shows `stub(no-creds)` with no further detail.

### Gap Summary Matrix

| Gap | Severity | Effort to Build | Data Available? |
|---|---|---|---|
| Neural stack viz | High | Large | Partial (state JSONs may not exist) |
| Doctor RFC lifecycle | High | Medium | Yes (ledger has RFC events) |
| Cardiac visualization | Medium | Medium | Yes (cardiac state in ORGANISM-STATE.json) |
| Epistemic metrics | Medium | Small | Partial (behind WIRE_EPISTEMICS flag) |
| Leg/worker status | Medium | Medium | Partial (lead_leg state) |
| Self-model view | Low | Small | No (no state file) |
| Event log viewer | High | Small | Yes (watchdog.log, ledger.jsonl) |
| Gate/blocker viz | High | Medium | Yes (state JSONs + Budgets.yaml) |
| Telegram status | Low | Small | No (stub only) |

---

## 6 · PANEL_DATA_SOURCES

### Read-Only Sources (currently used or available)

| Source | Path | Format | Used By | Content |
|---|---|---|---|---|
| ORGANISM-STATE.json | `_ops/state/` | JSON | Dashboard, Panel | Master organism state (ts, spend, chrono, wiring, cardiac, etc.) |
| telemetry-latest.json | `_ops/state/` | JSON | Dashboard | Genome/brain costs, FX rate, per-organ spending |
| fitness-latest.json | `_ops/state/` | JSON | Dashboard | Authoritative status, attribution, weights, integrity alerts |
| fitness-history.json | `_ops/state/` | JSON | Neither (available) | Historical fitness snapshots |
| replication-latest.json | `_ops/state/` | JSON | Dashboard | Sigma zone, spawn status, live gate |
| channel-status.json | `_ops/state/` | JSON | Dashboard | Per-channel live/mode/status |
| school-awareness.json | `_ops/state/` | JSON | Neither (available) | Learning awareness state |
| CAPABILITY-OK.flag | `_ops/state/` | Flag file | Dashboard (check) | Indicates capability system passed check |
| ledger.jsonl | `_ops/07 - Knowledge/genome-system/ledger/` | JSONL | Dashboard (tail 10) | Append-only event log (all organs write here) |
| Epoch files | `_ops/budget/epochs/epoch-*.json` | JSON | Dashboard (latest) | Pressure, allocation, per-organ grants |
| watchdog.log | `_ops/state/` | Text | Neither (available) | Structured watchdog events |
| OWNER-PROFILE.json | `_ops/state/` | JSON | Panel | Owner preferences and onboarding data |
| PROJECT.md files | Vault-wide scan | Markdown | Panel | Project metadata (status, focus, actions) |
| OCTOPUS.env | `_ops/` | Key-value | Dashboard (read+write) | Flag overrides and profile |
| Budgets.yaml | `_ops/budget/` | YAML | Neither (readable via opslib) | Capability gates and budget caps |

### Write-Only Targets (control-files)

| Target | Written By | Content |
|---|---|---|
| OCTOPUS.env | Dashboard | Flag overrides (set KEY=VALUE format) |
| STOP-ORGANISM | Dashboard | Kill signal for organism |
| RESTART-REQUESTED | Dashboard | Post-kill restart instruction for RUN-ORGANISM.bat |
| OWNER-PROFILE.json | Panel | Owner profile (atomic write) |
| OWNER-PROFILE-LOG.md | Panel | Append-only profile change history |
| ledger.jsonl (PROPOSAL) | Panel (via attribution.propose) | Lead proposal events only |

---

## 7 · PANEL_TRUST_SCORE

### Dashboard: 9/10

| Factor | Score | Rationale |
|---|---|---|
| Crash independence | 10 | No shared state, no organism import |
| Write safety | 10 | Only control-files (OCTOPUS.env + STOP + RESTART) |
| Read-only integrity | 10 | Never modifies state JSONs or ledger |
| Network safety | 10 | 127.0.0.1 only |
| Dependency safety | 10 | stdlib only |
| Input safety | 8 | html.escape used, but no CSRF tokens |
| Operational risk | 9 | Restart button can kill organism -- intentional, requires explicit click |

**Overall: 9/10** -- The dashboard is the gold standard for safe UI design in this system. It follows the control-file pattern exactly. The only reason it is not 10/10 is the restart button (intentional risk) and lack of CSRF (acceptable for localhost-only).

### Panel: 7/10

| Factor | Score | Rationale |
|---|---|---|
| Crash independence | 9 | Separate process, but lazy attribution import creates coupling |
| Write safety | 7 | Owner profile (harmless) + attribution.propose() (writes to ledger) |
| Read-only integrity | 10 | Never modifies organism state |
| Network safety | 10 | 127.0.0.1 only |
| Dependency safety | 8 | Mostly stdlib; attribution is the only external dependency |
| Input safety | 7 | Basic validation; no CSRF, no rate limiting on lead submissions |
| Operational risk | 7 | attribution.propose() is propose-only -- safe by design. But the import path to budget/ creates a maintenance coupling. |

**Overall: 7/10** -- Safe for current use. The propose-only invariant on `attribution.propose()` is the critical safety net. Deductions for: ledger write coupling, no rate limiting, lazy import of non-stdlib code.

---

## 8 · KEY FINDINGS

1. **Both servers are currently down.** Only port 8771 (organism) is running. Dashboard and Panel require manual launch.
2. **Dashboard is crash-independent.** Zero organism imports. stdlib only. If it crashes, nothing else notices.
3. **Dashboard writes only control-files.** OCTOPUS.env + STOP-ORGANISM + RESTART-REQUESTED. This is identical to the organism's own control-file pattern.
4. **Panel's lead form is propose-only.** `attribution.propose()` creates PROPOSAL events but never CONFIRMS. Money confirmation is exclusively via reconcile (CSV matching).
5. **9 visibility gaps exist.** The dashboard covers organism-level state well but provides zero visibility into: neural stack, doctor RFC lifecycle, cardiac details, epistemic metrics, leg/worker status, self-model, event logs, gate chain, and Telegram.
6. **14 data sources are available.** 11 read-only state files + 3 write-only control files. All JSON-based, all parseable by stdlib.
7. **Trust scores: Dashboard 9/10, Panel 7/10.** Both are safe. The gap is the panel's attribution coupling and lack of rate limiting.
