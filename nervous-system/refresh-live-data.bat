@echo off
chcp 65001 >nul
set PYTHONUTF8=1
rem 2026-08-16 (SEAM-LOOP C1): bare python = silent no-op in task context (Store stub/no PATH)
rem -> absolute python.exe per Watch pattern; keeps interactive use identical.
set "PY_EXE=C:\Program Files\Python313\python.exe"
cd /d "%~dp0"
echo Refreshing OCTOPUS live data...

REM ============================================================================
REM OCTOPUS Nervous System — Live Data Refresh Pipeline
REM ============================================================================
REM Purpose:   Run all 17 extractors to refresh the JS data backbone.
REM Usage:     Double-click or run from cmd: refresh-live-data.bat
REM Safety:    All extractors are read-only; zero mutations to source data.
REM Output:    17 *.js files in F:/backup/nervous-system/
REM Runtime:   ~15-45 seconds total (git scan + vault scan are slowest).
REM Encoding:  UTF-8 (chcp 65001 + PYTHONUTF8=1).
REM Dependencies: Python 3.12+, git (for CH-02), organism state files (for CH-01/04/07/11/15/17).
REM ============================================================================
REM NOTE ON ORDERING:
REM   Extractors have NO inter-dependencies. Each reads directly from its
REM   source-of-truth (organism state files, vault markdown, git repos).
REM   Order below is grouped by logical layer for readability only.
REM ============================================================================

REM ----------------------------------------------------------------------------
REM LAYER 0 — Core 4D System & Vault Graph
REM Sources: 4d_system outputs, entire Obsidian vault
REM These are independent and typically finish in 1-5s each.
REM ----------------------------------------------------------------------------

REM CH-00: Live SOG + daemon + budget + events + frontier
REM   Source:  4d_system/outputs/daemon_state.json
REM            4d_system/outputs/decision_packets.jsonl
REM            4d_system/outputs/self_evolved/frontier.json
REM            4d_system/outputs/4d_experiments.db
REM   Output:  live-data.js  (~140KB typical)
REM   Runtime: ~1s
REM   UI consumers: admin-telegram Vitals panel, OCTOPUS worlds
"%PY_EXE%" extract_live_data.py

REM CH-01: Organism state (money, time, wiring flags)
REM   Source:  _ops/state/ORGANISM-STATE.json
REM            _ops/state/fitness-latest.json
REM            _ops/state/cardiac-budget.json
REM   Output:  ops-data.js  (~1KB)
REM   Runtime: ~1s
REM   UI consumers: admin-telegram Vitals panel, OCTOPUS Cockpit
"%PY_EXE%" extract_ops_data.py

REM CH-03: Vault graph scanner (wiki-links between all markdown files)
REM   Source:  Entire F:/backup vault (*.md only; skips _Archive, _Duplicates, .git, etc.)
REM   Output:  graph-data.js  (~108KB)  → also mirrored to OCTOPUS/worlds/graph-data.js
REM   Runtime: ~3-5s (scans thousands of files; capped at 300 nodes + edges)
REM   UI consumers: OCTOPUS 02-ontology world, admin-telegram (future)
"%PY_EXE%" extract_graph.py

REM ----------------------------------------------------------------------------
REM LAYER 1 — Organism Telemetry, Health & Governance
REM Sources: _ops/state/*, _ops/governor/*, _ops/neural/*
REM These compute derived scores from organism telemetry. All independent.
REM ----------------------------------------------------------------------------

REM CH-11: Audit trail (events, traces, genome ledger)
REM   Source:  _ops/state/events.jsonl
REM            _ops/state/traces.jsonl
REM            _ops/state/ledger-fallback.jsonl
REM            07 - Knowledge/genome-system/ledger/ledger.jsonl
REM   Output:  audit-data.js  (~11KB)
REM   Runtime: ~1-2s
REM   UI consumers: OCTOPUS 04-twin world, admin-telegram (future)
REM   Features: freshness check (>45min = stale), delta detection vs last run
"%PY_EXE%" extract_audit_data.py

REM CH-07: Composite health score (system + fitness + telemetry)
REM   Source:  _ops/state/ORGANISM-STATE.json
REM            _ops/state/fitness-latest.json
REM            _ops/state/telemetry-latest.json
REM            _ops/governor/governor-alerts.md
REM   Output:  health-data.js  (~1-2KB)
REM   Runtime: ~1s
REM   UI consumers: admin-telegram Health panel, OCTOPUS 08-risk world
REM   Weights: system 40% + fitness 35% + telemetry 25% (override via health-weights.json)
"%PY_EXE%" extract_health_score.py

REM CH-17: Watchdog alerts & organism liveness
REM   Source:  _ops/state/ORGANISM-STATE.json
REM            _ops/governor/governor-alerts.md
REM            _ops/state/events.jsonl
REM   Output:  watchdog-data.js  (~15KB)
REM   Runtime: ~1s
REM   UI consumers: admin-telegram (future), OCTOPUS 01-cockpit badge
REM   Thresholds: state stale >60min, critical alerts score -15 each, STOP flags -30
"%PY_EXE%" extract_watchdog_data.py

REM CH-16: Neural telemetry (rhythm, circadian, hebbian, consolidation)
REM   Source:  _ops/neural/hebbian.json
REM            _ops/neural/consolidation.json
REM            _ops/neural/circadian.py  (imported module)
REM            _ops/chrono_rhythm/rhythm.py  (imported module)
REM            _ops/state/ORGANISM-STATE.json
REM   Output:  neural-data.js  (~1-2KB)  → also mirrored to OCTOPUS/worlds/neural-data.js
REM   Runtime: ~1-2s (imports Python modules; fail-soft if modules missing)
REM   UI consumers: admin-telegram Neural panel, OCTOPUS 06-time world
"%PY_EXE%" extract_neural_data.py

REM CH-04: Unified approval queue (HITL / owner-gate)
REM   Source:  _ops/state/unified-approval-queue.json
REM   Output:  queue-data.js  (~300B-2KB)
REM   Runtime: ~1s
REM   UI consumers: admin-telegram Queue panel, OCTOPUS 01-cockpit badge
REM   Schema: Q.queue.items[], Q.queue.counts{}, Q.queue.badge (pending count)
"%PY_EXE%" extract_queue_data.py

REM ----------------------------------------------------------------------------
REM LAYER 2 — External Channels, Scouts & Vault Scans
REM Sources: vault folders, git subprocesses, API caches
REM These are the slowest; git scan can take 5-15s.
REM ----------------------------------------------------------------------------

REM CH-01: Research / scout digests
REM   Source:  00 - Inbox/scout-digests/*.md
REM            00 - Inbox/scout-digests/_TRIAGE-BOARD.md
REM   Output:  research-data.js  (~4KB)
REM   Runtime: ~1-2s
REM   UI consumers: admin-telegram Research panel, OCTOPUS 01-cockpit
REM   Coverage: 23 canonical scouts; health score based on staleness + synthesis age
"%PY_EXE%" extract_research_data.py

REM CH-05: Obsidian task queue (FULL VAULT SCAN — heaviest I/O)
REM   Source:  All .md files under F:/backup (skips _Archive, _Duplicates, .git, node_modules, etc.)
REM   Output:  task-data.js  (~650KB)  ← LARGEST PAYLOAD
REM   Runtime: ~3-5s (scans thousands of markdown files; parses frontmatter + checkboxes)
REM   UI consumers: admin-telegram Task Queue panel
REM   NOTE:    For dashboard use, task-summary-data.js (built in Wave 5) is loaded
REM            by default. Full task-data.js is lazy-loaded on user request.
REM            See PAYLOAD-SIZE-REPORT.md for metrics.
"%PY_EXE%" extract_obsidian_tasks.py

REM CH-05b: Task summary (lightweight dashboard payload — depends on CH-05 above)
REM   Source:  task-data.js (output of extract_obsidian_tasks.py)
REM   Output:  task-summary-data.js  (~1.5KB)
REM   Runtime: ~0.5s
REM   UI consumers: admin-telegram Task Queue panel (default load)
"%PY_EXE%" extract_task_summary.py

REM CH-02: Git status across all repos (SLOWEST — multiple subprocess calls)
REM   Source:  .git/ directories under F:/backup (discovered via os.walk, max depth 6)
REM   Output:  git-data.js  (~5KB)
REM   Runtime: ~5-15s (spawns git status --porcelain=2 --branch per repo)
REM   UI consumers: admin-telegram Git Status panel
REM   Limitations: caps file list at 50 per repo; skips nested submodules gracefully
"%PY_EXE%" extract_git_status_data.py

REM CH-08: Wallet / eToro governance
REM   Source:  _ops/budget/wallet-state.json  (and related wallet source files)
REM   Output:  wallet-data.js  (~1-2KB)
REM   Runtime: ~1s
REM   UI consumers: admin-telegram Wallet panel, OCTOPUS 03-money world
REM   Schema: WL.gate{}, WL.portfolio{}, WL.budget{}
"%PY_EXE%" extract_wallet_data.py

REM CH-06: Mining fleet monitor
REM   Source:  _ops/state/mining-status.json
REM            coin_hunter_cache (if present)
REM   Output:  mining-data.js  (~7KB)
REM   Runtime: ~1s
REM   UI consumers: admin-telegram Mining panel, OCTOPUS 03-money world
REM   Schema: M.fleet{}, M.readiness{}, M.security.gates{}, M.coins.top_candidates[]
"%PY_EXE%" extract_mining_data.py

REM CH-09: Crypto market signals
REM   Source:  _ops/state/crypto-state.json
REM            lunarcrush cache (if present)
REM            cryptoquant cache (if present)
REM   Output:  crypto-data.js  (~4KB)
REM   Runtime: ~1s
REM   UI consumers: admin-telegram Crypto panel, OCTOPUS 03-money world
REM   NOTE:    LunarCrush data may be stale if API rate-limits hit.
REM            Staleness is flagged in C.lunarcrush.stale{} with emoji + label.
"%PY_EXE%" extract_crypto_data.py

REM CH-13: Project index (03 - Projects/)
REM   Source:  03 - Projects/*/PROJECT.md, MANIFEST.yaml, OpenQuestions.md
REM   Output:  project-data.js  (~4KB)
REM   Runtime: ~1-2s
REM   UI consumers: admin-telegram Project Index panel, OCTOPUS 01-cockpit
REM   Health: computed from doc presence, activity age, blockers, todos, status
"%PY_EXE%" extract_project_index.py

REM CH-12: Ideas backlog (00 - Inbox/)
REM   Source:  00 - Inbox/*.md (frontmatter + H1 + strategic scoring heuristic)
REM   Output:  ideas-data.js  (~80KB)
REM   Runtime: ~1-2s
REM   UI consumers: admin-telegram Ideas Backlog panel
REM   Scoring: type base + status multiplier + tag/title/path bonuses + freshness
"%PY_EXE%" extract_ideas_backlog.py

REM CH-15: Telegram control channel
REM   Source:  _ops/state/channel-status.json
REM            _ops/state/telegram_offset.json
REM            _ops/state/pulse/telegram-poll.json
REM            _ops/state/telegram/approvals/approvals.jsonl
REM            _ops/state/unified-approval-queue.json
REM            _ops/budget/budget-state.json
REM   Output:  telegram-data.js  (~2KB)
REM   Runtime: ~1s
REM   UI consumers: admin-telegram Telegram Control panel
REM   Health: live(40%) + offset fresh(20%) + queue drained(20%) + budget open(20%)
"%PY_EXE%" extract_telegram_control.py

REM CH-15b: Telegram command registry (Wave 6)
REM   Source:  _ops/telegram_center/center.py
REM            _ops/budget/approval_channel.py
REM            _ops/state/telegram/center-config.json
REM            _ops/state/telegram_offset.json
REM            _ops/state/pulse/telegram-poll.json
REM   Output:  telegram-commands-data.js  (~6KB)
REM   Runtime: ~1s
REM   UI consumers: admin-telegram Telegram Control panel (command list + mode badges)
REM   Schema: commands[], modes, safety labels, wiring status, masked owner chat ID
"%PY_EXE%" extract_telegram_commands.py

REM CH-18: Audit trail (Wave 6)
REM   Source:  _ops/state/action-audit.jsonl
REM   Output:  audit-trail-data.js  (~2-5KB)
REM   UI consumers: admin-telegram Audit panel
"%PY_EXE%" extract_audit_trail.py

echo Done.

REM ============================================================================
REM OPTIONAL: CI / Drift Gate (Wave 6)
REM   Uncomment the line below to run schema + UI contract verification after refresh.
REM   This exits non-zero if any extractor output is malformed or UI contract broken.
REM   Recommended for automated pipelines; safe to skip for manual refreshes.
REM ============================================================================
REM python run_ci.py
REM if errorlevel 1 echo CI GATE FAILED — check schema or UI contract errors above
REM ============================================================================
REM Next steps after refresh:
REM   1. Open OCTOPUS/admin-telegram/index.html in browser to verify panels.
REM   2. Check nervous-system/*.js file sizes if preview.html feels slow.
REM   3. If any extractor failed, run it individually (see EXTRACTOR-RUNBOOK.md).
REM ============================================================================
