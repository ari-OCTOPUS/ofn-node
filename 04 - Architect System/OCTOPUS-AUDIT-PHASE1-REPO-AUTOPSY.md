---
title: "Octopus — Phase 1: Repository Autopsy"
date: 2026-07-09
status: EVIDENCE-BACKED
confidence: HIGH
scope: Full structural map — F:\backup
convention: Every claim grounded in filesystem evidence.
---

# PHASE 1 — REPOSITORY AUTOPSY

> *Go slowly. Start with PHASE 1 only. Do not jump to refactoring until the map is real.*

---

## 1 · TREE_OF_IMPORTANCE

### Classification Legend
- 🟢 **ACTIVE IN PRODUCTION** — running or directly invoked by organism
- 🟡 **ACTIVE / VAULT** — read/written by organism or agents
- 🔵 **INFRASTRUCTURE** — supporting services
- 🟠 **LEGACY** — predecessor system, partially superseded
- ⬜ **ARCHIVE / QUARANTINE** — not in active use
- ⬛ **SKIP** — out of scope (git internals, CHRONOS reference system)

```
F:\backup\                          ← ROOT (Obsidian vault + organism)
│
├── 📄 _PROJECT_INSTRUCTIONS.md      🟡 Agent constitution (136 lines)
├── 📄 CLAUDE.md                     🟡 Claude Code notes
├── 📄 .agentignore                  🟡 Agent deny-list (secrets, _code, _Archive)
├── 📄 .gitignore                    ⬛ Git rules
├── 📄 ROTATION_CHECKLIST.md         🟡 Secrets rotation
├── 📄 Octopus_Heart_Design_v1.md     🟡 Cardiac design doc (29 KB)
├── 📄 CHRONOS-FABLE_OS_Audit*.md    🟡 Audit of reference system
├── 📄 Untitled.base                 ⬜ Obsidian auto-artifact (9 lines)
├── 📄 MycoCardium-Architecture*.docx  🟡 External analysis doc (254 KB)
│
├── 00 - Inbox/                      🟡 ~100+ .md, 3 .py
│   ├── AGENT_QUESTIONS.md           ← permanent keeper
│   ├── scout-digests/               🟡 ~80+ digest files (growing, no triage)
│   ├── build-proposals/             🟡 9 build proposals
│   └── replication-kit/             🟡 Scaffold + seed vault
│
├── 01 - Dashboard/                  🟡 3 .md + .html/.base
│   ├── Home.md, Brain.md, HANDOFF.md  ← Obsidian navigation hub
│   └── [HTML control panels]
│
├── 02 - Life OS/                    🟡 2 .md — personal life mgmt
├── 03 - Projects/                   🟡 14 .py, ~60 .md, 19 .json
│   ├── Accounting/                  🟡
│   ├── Crypto - etoro/              🟡 19 JSON data dumps (LunarCrush/CryptoQuant)
│   ├── Lead-نقاشی/                  🟡
│   ├── Mining/                      🟡
│   ├── Ziman Galerry/               🟡 (typo "Galerry" consistent throughout)
│   ├── اونلی فنز/                    🟡 orchestrator.py
│   └── _Index - Projects.md
│
├── 04 - Architect System/            🟡 ~1596 .py (incl venvs), ~80 .md
│   ├── architect/                    🟡 Massive workspace + _code/ai-farm
│   ├── learning-engine/              🟡 Mutation ledger, contracts, startup
│   ├── octopus-build-prompts/        🟡 P1-Heart through P6 build prompts
│   ├── prompts/                     🟡 Debate + metabolic governor prompt texts
│   ├── scripts/                     🟡 backup.py, validate, governor_shadow
│   └── _intake-photos/
│
├── 05 - Agents/                      🟡 6 .md — agent registry, role defs
├── 06 - Architecture Maps/           🟡 7 .md — ECOSYSTEM, SYSTEM_MAP, etc.
│
├── 07 - Knowledge/                   🟡 38 .py, ~40 .md
│   ├── genome-system/               🟢 STANDALONE GIT REPO
│   │   ├── agents/                   🟡 creativity.py, doctor.py, guardian.py
│   │   ├── ledger/                   🟢 ledger.py (12.6 KB), ledger.jsonl
│   │   ├── perception/               🟡 indexer.py, watcher.py
│   │   ├── genome/                   🟢 gates.yaml, values.yaml, metrics.yaml
│   │   ├── tests/                    🟢 6 test files
│   │   └── scripts/                  🟢 backup.py, crontab.txt
│   ├── school-memory/               🟡 curriculum.py
│   ├── _doctor-research/             🟡 Design research notes
│   ├── _backups/                    🟡 6 tar.gz backups (no cleanup schedule)
│   ├── Time-Architecture/           🟡 Theory, experiments
│   └── هیپنوتیزم و خودآگاهی/        🟡 Hypnosis/self-awareness (PDFs, HTML)
│
├── 08 - Assets/                      🟡 Binary: photos, mining images
├── 09 - People/                      🟡 1 .md — person notes
├── 10 - Telegram processing/         ⬜ EMPTY — no files found at any depth
│
├── _code/                            🟡 Per-project code (separate from _ops)
│   ├── Accounting/                  🟡 Node.js bot
│   ├── Crypto - etoro/               🟡 Scrapers, classifiers
│   ├── Lead-نقاشی/                   🟡 AiFarm-Lead (PDF knowledge base)
│   ├── Mining/                       🟡 QuantumAlphaBot, sentinel + .bat launchers
│   └── Ziman Galerry/                🟡 control-brain Flask app, ziman-agent
│
├── _launchpad/                       🟠 LEGACY — predecessor "second brain"
│   └── second-brain-live/
│       ├── START-HERE.bat            🟠 Setup wizard + venv
│       ├── KILL-ALL-BRAIN.bat        🟠 Kills ALL python.exe (aggressive)
│       ├── control-brain/           🟠 Flask app + adapters + config
│       ├── painting-bot/             🟠
│       ├── accounting-bot/           🟠 Node.js
│       └── panels/                   🟠 state.db (20 KB)
│
├── _memory/                          🟡 13 .md — agent memory/learning
│   ├── HEARTBEAT.md                  🟢 68 lines, last: 2026-07-09T22:08
│   ├── EXPERIENCE-LEDGER.md          🟡 47 KB
│   └── BUILD-PROMPT.md               🟡
│
├── _Templates/                       🟡 6 .md — Obsidian note templates
├── _Duplicates/                      ⬜ ~500+ .md quarantined
│   └── broken-dot-git-*              ⬜ Crash artifacts from failed git ops
│
├── _ops/                             🟢 THE ORGANISM — always-on core
│   ├── organism.py                   🟢 400 lines — THE HEART (always-on loop)
│   ├── wiring.py                     🟢 856 lines — CENTRAL NERVOUS SYSTEM
│   ├── chrono.py                     🟢 638 lines — PACEMAKER + time arch
│   ├── cardiac.py                    🟢 275 lines — Bio-allometry heart laws
│   ├── unified_bus.py                🟢 149 lines — SPINAL CORD (pub/sub)
│   ├── live_loop.py                  🟢 228 lines — BRAIN-BODY coordinator
│   ├── idea_graph.py                 🟢 335 lines — vault-wide idea analysis
│   ├── germline.py                   🟢 155 lines — genome change tracking
│   ├── watchdog.py                   🟢  86 lines — STAY-ALIVE daemon
│   ├── checkpoint.py                 🟡  85 lines — checkpoint system (small)
│   ├── smoke_24h.py                  🟡 116 lines — manual 24h smoke test
│   ├── RUN-ORGANISM.bat              🟢 Production launcher (restart loop)
│   ├── ORGANISM-SPEC.md              🟢 Organism specification
│   │
│   ├── budget/                        🟢 METABOLIC GOVERNOR
│   │   ├── budgets.yaml              🟢 SINGLE SOURCE OF TRUTH (6.9 KB)
│   │   ├── opslib.py                  🟢 285 lines — shared library
│   │   ├── governor_epoch.py         🟢 341 lines — allostatic epoch
│   │   ├── telemetry.py              🟢 205 lines — snapshot + reconciliation
│   │   ├── fitness.py                 🟢 237 lines — fitness function
│   │   ├── attribution.py            🟢 191 lines — money attribution
│   │   ├── replication.py           🟢 134 lines — sigma replication
│   │   ├── money_gate.py             🟢  46 lines — dual-lock spend auth
│   │   ├── organ_gate.py             🟢 178 lines — per-organ gate
│   │   ├── capability_gate.py       🟢 104 lines — capability auth
│   │   ├── approval_channel.py        🟢 881 lines — human approval queue
│   │   ├── human_append_guard.py      🟢 122 lines — prevent unauthorized edits
│   │   ├── env_loader.py             🟢  76 lines — env var loader
│   │   ├── reconcile.py              🟢 122 lines — bank CSV reconciliation
│   │   ├── epochs/                   🟢 45 epoch JSONs (growing, no rotation)
│   │   ├── STAGE1-REPORT.md          🟡
│   │   ├── STAGE3-REPORT.md          🟡
│   │   └── budgets-proposed-diff.md  🟡
│   │
│   ├── doctor/                        🟢 EVOLUTIONARY DOCTOR
│   │   ├── doctor.py                 🟢 754 lines — run_cycle, RFC
│   │   ├── chamber.py                 🟢 192 lines — isolation testing
│   │   ├── evolution.py               🟢 204 lines — tournament, lift/promote
│   │   ├── calibration.py             🟢 126 lines
│   │   ├── spectral.py               🟢 136 lines — multimodal perception
│   │   └── box/                       🟢 BOX OF AGENTS (12 sub-agents)
│   │       ├── box.py                 🟢 147 lines — box orchestrator
│   │       ├── archivist.py           🟢 85 lines
│   │       ├── warden.py              🟢 137 lines
│   │       ├── sensors.py             🟢 149 lines
│   │       ├── dynamics.py            🟢 106 lines
│   │       ├── topology.py            🟢 92 lines
│   │       ├── primitive.py           🟢 115 lines
│   │       ├── null_dreamer.py        🟢 48 lines
│   │       ├── agent_state.py         🟢 118 lines
│   │       ├── falsif_harness.py      🟢 152 lines
│   │       ├── b3_bridge.py           🟢 109 lines — bridge module (B3)
│   │       └── b4_fusion.py           🟢 148 lines — fusion module (B4)
│   │
│   ├── neural/                        🟢 NEURAL STACK (8 modules)
│   │   ├── neural_driver.py           🟢  87 lines — orchestrator
│   │   ├── consolidation.py           🟢  80 lines — canonical memory
│   │   ├── hebbian.py                 🟢 107 lines
│   │   ├── circadian.py               🟢  59 lines — time-of-day awareness
│   │   ├── reflex.py                  🟢  67 lines — automated reactions
│   │   ├── nociceptor.py              🟢  67 lines — pain/damage detection
│   │   ├── signal_hub.py              🟢  70 lines
│   │   ├── sprint.py                  🟢 208 lines — sprint management
│   │   └── hooks.py                   🟢  52 lines
│   │
│   ├── brain/                          🟢 BRAIN COCKPIT
│   │   └── cockpit.py                 🟢 213 lines
│   │
│   ├── legs/                           🟢 ACTUATORS / LEGS
│   │   ├── leg.py                     🟢 220 lines — generic leg
│   │   └── lead_leg.py                🟢 143 lines — HLC + ack
│   │
│   ├── panel/                          🟢 ONBOARDING PANEL
│   │   ├── server.py                  🟢 611 lines — port 8899
│   │   └── RUN-PANEL.bat              🟢
│   │
│   ├── dashboard/                      🟢 LIVE DASHBOARD
│   │   ├── server.py                  🟢 788 lines — port 8770
│   │   └── RUN-DASHBOARD.bat          🟢
│   │
│   ├── afferent/                       🟢 SENSORY INPUT
│   │   ├── ingest_raw.py              🟢 218 lines — crypto/accounting CSVs
│   │   ├── school_bridge.py            🟢 103 lines — school memory bridge
│   │   └── sensory_bus.py             🟢 154 lines — abstract observations
│   │
│   ├── epistemics/                     🟢 EPISTEMOLOGY LAYER
│   │   ├── contracts.py               🟢 5 metrics definitions
│   │   ├── emit.py                    🟢
│   │   ├── metrics.py                 🟢
│   │   ├── readers.py                 🟢
│   │   └── run_offloop.py             🟢 62 lines
│   │
│   ├── debate/                          🟢 LLM DEBATE LOOP
│   │   ├── debate_loop.py             🟢 208 lines
│   │   ├── client.py                  🟢 494 lines — LLM routing client
│   │   └── topics.py                  🟢 119 lines
│   │
│   ├── chrono_rhythm/                  🟢 CHRONO RHYTHM
│   │   └── rhythm.py                  🟢 154 lines — GREEN/AMBER/RED
│   │
│   ├── state/                           🟢 RUNTIME STATE (written every tick)
│   │   ├── ORGANISM-STATE.json         🟢 423 B — live state
│   │   ├── OWNER-PROFILE.json         🟢 4.9 KB
│   │   ├── OWNER-PROFILE-LOG.md       🟢 6.1 KB
│   │   ├── telemetry-latest.json      🟢 773 B
│   │   ├── telemetry/                  🟢 Daily JSONs (3 files)
│   │   ├── fitness-latest.json         🟢 716 B
│   │   ├── fitness-history.json        🟢 2 B — empty `{}`
│   │   ├── replication-latest.json     🟢 718 B
│   │   ├── school-awareness.json       🟢 153 B
│   │   ├── channel-status.json         🟢 1.1 KB
│   │   ├── CAPABILITY-OK.flag          🟢 1.5 KB — 62 test pass list
│   │   └── watchdog.log                🟢 153 B — 2 entries
│   │
│   ├── reconcile/                       ⬜ PLACEHOLDER — only README.md
│   ├── backup/                          🟡 gitwrite.lock (67 B)
│   │
│   └── tests/                           🟢 63 test files + run_all.py
│       ├── run_all.py                 🟢 107 lines — orchestrates all tests
│       ├── harness.py                  🟢 153 lines — test framework
│       └── test_*.py                   🟢 63 test modules
│
├── survival-gateway/                  🔵 LiteLLM proxy + PostgreSQL
│   ├── .env                           🔒 API keys (2 KB)
│   ├── docker-compose.yml             🔵 Docker stack
│   ├── litellm_config.yaml             🔵 Model routing
│   └── data/postgres/                  🔵 Full PG data dir (WAL etc.)
│
├── CHRONOS-FABLE-OS/                  ⬛ SKIP — reference system (separate audit)
│
└── .claude/                           ⬛ SKIP — worktrees
```

---

## 2 · ENTRYPOINT_MAP

### 2.1 · BAT Entry Points (Production)

| # | Path | What It Does | Evidence |
|---|---|---|---|
| **E1** | `_ops\RUN-ORGANISM.bat` | **PRIMARY** — always-on organism loop. `call OCTOPUS.env` → `python organism.py`. Detects `STOP-ORGANISM` + `RESTART-REQUESTED` for clean restart. | File exists, 29 lines. organism.py running on PID 13256 port 8771. |
| **E2** | `_ops\panel\RUN-PANEL.bat` | Launches onboarding panel HTTP server (default 8790, env override 8899) | File exists, 10 lines. |
| **E3** | `_ops\dashboard\RUN-DASHBOARD.bat` | Launches live dashboard HTTP server on port 8770 | File exists, 11 lines. |
| **E4** | `_launchpad\...\START-HERE.bat` | Legacy — venv creation + setup wizard | 1140+ .py siblings suggest full app bundle. |
| **E5** | `_launchpad\...\KILL-ALL-BRAIN.bat` | Legacy — kills ALL python.exe processes | Destructive, not organism-aware. |

### 2.2 · Python `__main__` / Direct Execution

| # | Path | Entry | Purpose | Lines |
|---|---|---|---|---|
| **P1** | `_ops\organism.py` | `main()` → `while True` | THE ORGANISM — tick/epoch/telemetry/fitness/neural/doctor/afferent/idea/epistemics/cardiac + HTTP on :8771 | 400 |
| **P2** | `_ops\panel\server.py` | HTTP server | Onboarding panel — profile, projects, leads, organism status | 611 |
| **P3** | `_ops\dashboard\server.py` | HTTP server | Live dashboard — state, flags, activity, channels, ideas | 788 |
| **P4** | `_ops\smoke_24h.py` | Manual test | 24-hour smoke test (has `__main__`) | 116 |
| **P5** | `_ops\tests\run_all.py` | Test runner | Orchestrates all 63 test modules | 107 |
| **P6** | `_ops\watchdog.py` | Daemon | Revives organism if port 8771 dies (2 entries in log) | 86 |
| **P7** | `_ops\budget\env_loader.py` | Utility | Loads OCTOPUS.env overrides | 76 |
| **P8** | `07 - Knowledge\genome-system\run.py` | Independent | Genome system entry point | 3482 B |

### 2.3 · HTTP Servers

| # | Port | File | Status | Evidence |
|---|---|---|---|---|
| **H1** | **8771** | `organism.py` | 🟢 **RUNNING** (PID 13256) | `netstat` confirms bound. State JSON being written. |
| **H2** | **8770** | `dashboard/server.py` | 🔴 NOT RUNNING | Port not bound. Requires RUN-DASHBOARD.bat. |
| **H3** | **8899** | `panel/server.py` | 🔴 NOT RUNNING | Port not bound. Requires RUN-PANEL.bat + PANEL_PORT env. |

### 2.4 · Scheduled / Cron-Like

| Path | Type |
|---|---|
| `_launchpad\...\autostart\install-daily-content.bat` | Windows Task Scheduler |
| `07 - Knowledge\genome-system\scripts\crontab.txt` | Crontab definition |
| `07 - Knowledge\genome-system\scripts\install_schedule.ps1` | PowerShell schedule installer |

---

## 3 · FILE_ROLE_MAP

### Tier 1 · Organism Core (The Beating Heart)

| # | Path | Role | LOC | Evidence |
|---|---|---|---|---|
| **T1.1** | `_ops\organism.py` | Single always-on metabolic loop — imports wiring, runs epoch/telemetry/fitness/neural/doctor/afferent/idea/epistemics/cardiac per tick. HTTP status on :8771. Writes ORGANISM-STATE.json. | 400 | Reads: ORGANISM-STATE.json, STOP-ORGANISM. Writes: ORGANISM-STATE.json, heartbeat.md, CAPABILITY-OK.flag, watchdog.log. |
| **T1.2** | `_ops\wiring.py` | Central nervous system — creates all subsystem objects based on profile/flags. Single import point for doctor, bus, leg, neural, school, afferent, idea_graph, scheduler, cardiac. | 856 | 19 WIRE_* flags, 5 CHRONO_* cadences, 3 profile levels. |
| **T1.3** | `_ops\chrono.py` | Pacemaker thread + beat counter + time architecture. Drives the organism's sense of rhythm and temporal coordination. | 638 | Owns `beat_seq`, `pacemaker`, `mode_color`. |
| **T1.4** | `_ops\cardiac.py` | Bio-allometry heart laws — bio_rhythm (Kleiber), BeatBudget, Baroreflex. Behind `OCTOPUS_WIRE_BIO` flag. Dynamic tick period. | 275 | Reads: budgets.yaml, ORGANISM-STATE.json. Writes: state/cardiac-budget.json. |
| **T1.5** | `_ops\RUN-ORGANISM.bat` | Production launcher — restart loop with STOP/RESTART flag protocol. Loads `OCTOPUS.env` before each `python` invocation. | 29 | Currently running, PID 13256. |
| **T1.6** | `_ops\budget\opslib.py` | Shared library — state dir resolution, budget loading, halt/freeze detection, heartbeat writes, ledger, alert, time utils. | 285 | Imported by nearly every subsystem. |

### Tier 2 · HTTP Servers & UI

| # | Path | Role | LOC | Evidence |
|---|---|---|---|---|
| **T2.1** | `_ops\dashboard\server.py` | Live dashboard — 5 tabs (organism/capabilities/activity/channels/ideas) + 2 JSON APIs. Writes OCTOPUS.env + STOP-ORGANISM + RESTART-REQUESTED. | 788 | stdlib-only. No organism import (crash independence). |
| **T2.2** | `_ops\panel\server.py` | Onboarding panel — owner profile form, project scanner, lead registration/minting, organism status page. | 611 | Port 8899, SO_EXCLUSIVEADDRUSE. |
| **T2.3** | `_ops\dashboard\RUN-DASHBOARD.bat` | Dashboard launcher — sets UTF-8, auto-opens browser. | 11 | |
| **T2.4** | `_ops\panel\RUN-PANEL.bat` | Panel launcher. | 10 | |

### Tier 3 · Budget & Metabolic Governance

| # | Path | Role | LOC | Evidence |
|---|---|---|---|---|
| **T3.1** | `_ops\budget\budgets.yaml` | **SINGLE SOURCE OF TRUTH** — monthly cap AU$200, 4 projects, per-organ floors, barbell allocation, 6 LLM routing slots. | 6.9 KB | Read by opslib.py → governor_epoch.py. |
| **T3.2** | `_ops\budget\governor_epoch.py` | Allostatic epoch governor — pressure-based budget allocation, epoch scheduling. | 341 | Writes epoch-*.json (45 files so far). |
| **T3.3** | `_ops\budget\telemetry.py` | Telemetry snapshot + reconciliation — reads genome/brain data, detects conflicts, writes telemetry-latest.json. | 205 | |
| **T3.4** | `_ops\budget\fitness.py` | Fitness function — authoritative computation (locked ~4 weeks), integrity alerts. | 237 | Writes fitness-latest.json. Authoritative=false since ~Jun 2026. |
| **T3.5** | `_ops\budget\attribution.py` | Money attribution — propose/confirm lifecycle, cell tracking, barbell attribution. | 191 | |
| **T3.6** | `_ops\budget\money_gate.py` | Hard money gate — dual-lock spending authorization. | 46 | Fail-closed: both attribution + approval required. |
| **T3.7** | `_ops\budget\organ_gate.py` | Per-organ spending gate — floor enforcement. | 178 | |
| **T3.8** | `_ops\budget\capability_gate.py` | Capability authorization — checks CAPABILITY-OK.flag before actions. | 104 | |
| **T3.9** | `_ops\budget\approval_channel.py` | Human approval queue — Telegram-first, 881 lines (largest gate). | 881 | Requires TELEGRAM_BOT_TOKEN (currently missing → queue stub). |
| **T3.10** | `_ops\budget\human_append_guard.py` | Prevents unauthorized human edits to ledger. | 122 | |
| **T3.11** | `_ops\budget\env_loader.py` | Environment variable loader — reads OCTOPUS.env into os.environ. | 76 | |
| **T3.12** | `_ops\budget\replication.py` | Sigma replication — spawn evaluation, live_gate locked until 2026-07-21. | 134 | |

### Tier 4 · Doctor & Neural

| # | Path | Role | LOC | Evidence |
|---|---|---|---|---|
| **T4.1** | `_ops\doctor\doctor.py` | Evolutionary doctor — run_cycle, RFC generation, mutation proposals. | 754 | |
| **T4.2** | `_ops\doctor\box\box.py` | Box of agents — orchestrates 12 specialized sub-agents. | 147 | 12 sub-agents: archivist, warden, sensors, dreamer, dynamics, topology, primitive, null_dreamer, agent_state, falsif_harness, b3_bridge, b4_fusion. |
| **T4.3** | `_ops\doctor\evolution.py` | Evolution engine — tournament, lift/promote. | 204 | |
| **T4.4** | `_ops\doctor\chamber.py` | Doctor chamber — isolation testing. | 192 | |
| **T4.5** | `_ops\doctor\calibration.py` | Calibration module. | 126 | |
| **T4.6** | `_ops\doctor\spectral.py` | Spectral analysis — multimodal perception. | 136 | |
| **T4.7** | `_ops\neural\neural_driver.py` | Neural stack driver — orchestrates 8 neural modules. | 87 | Modules: consolidation, hebbian, circadian, reflex, nociceptor, signal_hub, sprint, hooks. |
| **T4.8** | `_ops\neural\sprint.py` | Sprint runner — sprint management. | 208 | |
| **T4.9** | `_ops\brain\cockpit.py` | Brain cockpit — cognitive coordination. | 213 | |

### Tier 5 · Afferent, Epistemics, Debate

| # | Path | Role | LOC | Evidence |
|---|---|---|---|---|
| **T5.1** | `_ops\afferent\ingest_raw.py` | Raw data ingestion — crypto/accounting CSVs. | 218 | |
| **T5.2** | `_ops\afferent\school_bridge.py` | Bridge to school memory system. | 103 | |
| **T5.3** | `_ops\afferent\sensory_bus.py` | Sensory bus — abstract observations from snapshots. | 154 | |
| **T5.4** | `_ops\epistemics\run_offloop.py` | Epistemics off-loop runner — 5 metrics. | 62 | |
| **T5.5** | `_ops\epistemics\contracts.py` | Epistemics contracts — metric definitions. | 75 | |
| **T5.6** | `_ops\debate\debate_loop.py` | LLM debate loop. | 208 | |
| **T5.7** | `_ops\debate\client.py` | LLM routing client — multi-provider support. | 494 | |

### Tier 6 · Support

| # | Path | Role | LOC | Evidence |
|---|---|---|---|---|
| **T6.1** | `_ops\unified_bus.py` | Spinal cord — pub/sub for all subsystems. | 149 | |
| **T6.2** | `_ops\live_loop.py` | Brain-body coordinator — subscribes to bus. | 228 | |
| **T6.3** | `_ops\idea_graph.py` | Idea graph engine — vault-wide note analysis. | 335 | |
| **T6.4** | `_ops\germline.py` | Genome change tracking — staleness detection. | 155 | |
| **T6.5** | `_ops\watchdog.py` | Stay-alive daemon — revives organism on port death. | 86 | 2 revival entries in log. |
| **T6.6** | `_ops\chrono_rhythm\rhythm.py` | Rhythm mode — GREEN/AMBER/RED based on budget stress. | 154 | |
| **T6.7** | `_ops\legs\leg.py` | Generic leg — autonomous HLC (Heuristic Local Controller). | 220 | |
| **T6.8** | `_ops\legs\lead_leg.py` | Lead leg — HLC + ack for leads. | 143 | |

### Tier 7 · State Stores (Runtime Artifacts)

| # | Path | Size | Role |
|---|---|---|---|
| **S1** | `_ops\state\ORGANISM-STATE.json` | 423 B | Live organism state (written every tick ~5 min) |
| **S2** | `_ops\state\telemetry-latest.json` | 773 B | Latest telemetry snapshot |
| **S3** | `_ops\state\fitness-latest.json` | 716 B | Fitness snapshot (authoritative=false) |
| **S4** | `_ops\state\replication-latest.json` | 718 B | Sigma=0.0, zone=pre-replication |
| **S5** | `_ops\state\channel-status.json` | 1.1 KB | 4 channels: dashboard=live, others=stub |
| **S6** | `_ops\state\school-awareness.json` | 153 B | 6 cells, mean=0.0417 |
| **S7** | `_ops\state\CAPABILITY-OK.flag` | 1.5 KB | 62 test modules pass list + SHA-256 |
| **S8** | `_ops\state\OWNER-PROFILE.json` | 4.9 KB | Owner profile |
| **S9** | `_ops\state\watchdog.log` | 153 B | 2 revival entries |
| **S10** | `_memory\HEARTBEAT.md` | 19 KB | 68 lines, last: 2026-07-09T22:08 |
| **S11** | `07 - Knowledge\genome-system\ledger\ledger.jsonl` | — | Append-only event ledger |
| **S12** | `_ops\budget\epochs\` (45 files) | ~90 KB total | Hourly epoch snapshots (growing, no rotation) |

### Tier 8 · Environment & Config

| # | Path | Keys | Risk |
|---|---|---|---|
| **C1** | `survival-gateway\.env` | LITELLM_MASTER_KEY, POSTGRES_*, ANTHROPIC_API_KEY, OPENAI_API_KEY, GEMINI_API_KEY, DEEPSEEK_API_KEY, ZAI_API_KEY, SAKANA_* | 🔒 2 KB — must verify gitignored |
| **C2** | `_launchpad\...\control-brain\.env` | TELEGRAM_TOKEN, OWNER_CHAT_ID, DEEPSEEK_API_KEY, SAKANA_API_KEY, ANTHROPIC_API_KEY, LLM_MODEL, PANEL_PORT, KEEPASS_* | 🔒 Legacy system |
| **C3** | `_ops\OCTOPUS.env` | **DOES NOT EXIST** — created dynamically by dashboard `/save` | — |
| **C4** | `_ops\budget\budgets.yaml` | global cap, projects, loop, allocation, routing (6 LLM slots) | 🟡 Single source of truth for budget |

---

## 4 · UNKNOWN_OR_SUSPICIOUS_FILES

### 4.1 · Orphaned / Purpose-Unclear

| File | Issue | Confidence |
|---|---|---|
| `Untitled.base` (root) | Obsidian auto-artifact, 9 lines, table view config. No organic purpose. | HIGH |
| `_ops\backup\gitwrite.lock` | 67-byte lock file. No organism code creates/clears this. Likely stale. | MEDIUM |
| `_ops\reconcile\README.md` | Only file in reconcile/. Actual reconcile logic lives in `budget/reconcile.py`. This dir is a ghost. | HIGH |
| `_ops\checkpoint.py` | 85 lines. Small module — unclear if integrated or stub. | LOW |
| `_ops\smoke_24h.py` | Has `__main__` — manual test script left in production dir. Not harmful but not part of organism loop. | MEDIUM |

### 4.2 · Potential Duplications

| Pattern | Details | Confidence |
|---|---|---|
| `_code\Ziman Galerry\control-brain\` vs `_launchpad\...\control-brain\` | Two copies of control-brain. `_code/` has Flask `app.py`; `_launchpad/` has full structure with core/, adapters/, config/, evolution/. Which is canonical? | HIGH |
| `_code\Mining\...\Ai bots\` vs `04 - Architect System\architect\_code\ai-farm\` | Mining bot code in both locations. | MEDIUM |
| `_memory\HEARTBEAT.md` vs `_memory\EXPERIENCE-LEDGER.md` | Both track organism experience. Overlap with ledger system. | LOW |

### 4.3 · Growing Accumulations (No Rotation)

| Location | Count | Growth Rate | Risk |
|---|---|---|---|
| `00 - Inbox\scout-digests\` | ~80+ files | Active growth | Low (vault hygiene) |
| `_ops\budget\epochs\` | 45 files, ~90 KB | ~1/hour when running | MEDIUM (unbounded) |
| `_ops\state\telemetry\` | 3 daily JSONs | ~1/day | LOW |
| `07 - Knowledge\_backups\` | 6 tar.gz | Manual | LOW |
| `03 - Projects\Crypto - etoro\*.json` | 19 JSON data dumps | Historical | LOW |

### 4.4 · Security-Concerning

| File | Issue | Action Needed |
|---|---|---|
| `survival-gateway\.env` | 2 KB, contains 11+ API keys | Verify `.gitignore` covers it |
| `_launchpad\...\control-brain\.env` | Contains TELEGRAM_TOKEN, KEEPASS_DB, KEEPASS_KEYFILE | Verify gitignored |
| `_code\Ziman Galerry\control-brain\SECRETS.md` | Named SECRETS.md — verify contents and gitignore | Investigate |

### 4.5 · Naming Oddities

| File | Issue |
|---|---|
| `03 - Projects\Ziman Galerry\` | Typo "Galerry" (should be "Gallery"). Consistent throughout repo — intentional or legacy. |
| `_Duplicates\broken-dot-git-2026-07-06-nul\` | `-nul` suffix = Windows NUL device artifact. Failed copy/move. |
| `_ops\doctor\box\b3_bridge.py` | "B3" — unclear if build phase or bug reference. |
| `_ops\doctor\box\b4_fusion.py` | "B4" — same pattern. |
| `04 - Architect System\architect\_code\ai-farm\AI-sume\langar\__deltest` | Literal name `__deltest` — deletion test artifact. |

### 4.6 · Empty / Shell Directories

| Directory | Issue |
|---|---|
| `10 - Telegram processing\` | Completely empty at all scanned depths. Placeholder or abandoned. |
| `_ops\backup\` | Contains only gitwrite.lock. Name suggests more. |

---

## 5 · EVIDENCE GROUNDING SUMMARY

### What We Can Prove

| Fact | Evidence |
|---|---|
| Organism is running | PID 13256, port 8771 bound, ORGANISM-STATE.json written 2026-07-09T22:53 |
| All kill switches absent | Filesystem check: no STOP-ORGANISM, STOP-METABOLIC, STOP-DEBATE, FREEZE.flag anywhere |
| Zero real spending | ORGANISM-STATE: month `{musd:0, usd:0.0, aud:0.0}` |
| Only dashboard channel live | channel-status.json: dashboard=live, telegram=stub(no-creds), whatsapp=NotWiredStub, email=NotWiredStub |
| Fitness locked | fitness-latest.json: authoritative=false (locked ~4 weeks), claimed=0, confirmed=0 |
| Replication locked | replication-latest.json: sigma=0.0, live_gate until 2026-07-21 |
| 63 tests green | CAPABILITY-OK.flag lists 62 passing modules (run_all.py + harness = 63 tests) |
| Epochs growing unbounded | 45 epoch JSONs, no rotation/cleanup code found |
| No OCTOPUS.env yet | File does not exist; created dynamically by dashboard |

### What We Cannot Prove (Unknowns)

| Question | Status |
|---|---|
| Which Telegram credentials are real vs placeholder | Cannot read .env (security), no organism logs to confirm successful sends |
| survival-gateway PostgreSQL content | sqlite3 not available; PG data dir exists but not queryable |
| `__pycache__` / venv contents | Excluded from scan; may contain stale compiled modules |
| Windows Task Scheduler registered tasks | Not inspectable from this shell |
| Total .md/.json count outside .git | `find` returned 0 — likely due to path quoting; vault file count is estimated |

---

**PHASE 1 COMPLETE.**

*Next: PHASE 2 — Organ Map (15 candidate organs, maturity classification, alive/dormant/broken).*
