---
type: spec
project: OCTOPUS
wave: 6
status: implemented
created: 2026-07-12
updated: 2026-07-13
tags: [octopus, wave-6, ci, drift-guard, schema, ui-contract]
---

# Wave 6 · CI & Drift Gate Spec

## Objective
Transition from "observable control surface" to "gated, testable, replayable, owner-aware action-ready control plane" WITHOUT removing existing safety posture.

## Deliverables

### 1. verify_schema.py
- **Path:** `nervous-system/verify_schema.py`
- **Purpose:** CI-grade validator for all extractor JS outputs
- **Checks:**
  - Each `.js` starts with `window.VAR_NAME = ` and ends with `;`
  - JSON is parseable
  - Required keys exist per schema contract
  - No NaN / Infinity / null where numeric expected
  - File sizes within budget
- **Contracts:** 19 files verified (live, ops, health, queue, crypto, mining, wallet, research, git, task-summary, task, ideas, project, telegram, telegram-commands, audit-trail, neural, watchdog, graph)
- **Exit code:** 0 = pass, 1 = fail

### 2. verify_ui_contract.py
- **Path:** `nervous-system/verify_ui_contract.py`
- **Purpose:** Validates `admin-telegram/index.html` against JS data
- **Checks:**
  - Every `window.VAR_NAME` data reference has matching `<script src>`
  - No orphaned script tags (loaded but unused)
  - Every `.panel` has a mode-label span
  - `actAll()` has explicit "not implemented" warning
  - System banner has freshness indicator
- **Exit code:** 0 = pass, 1 = fail

### 3. run_ci.py
- **Path:** `nervous-system/run_ci.py`
- **Purpose:** Orchestrates both verifiers sequentially
- **Integration:** Added as optional (commented) last step in `refresh-live-data.bat`
- **Exit code:** 0 = all pass, 1 = any failure

### 4. refresh-live-data.bat
- **Path:** `nervous-system/refresh-live-data.bat`
- **Wave 6 additions:**
  - `extract_telegram_commands.py` (CH-15b)
  - `extract_audit_trail.py` (CH-18)
  - Optional CI step at end (commented out by default)

## Schema Contracts (Summary)

| JS File | Var | Required Keys | Size Budget |
|---|---|---|---|
| live-data.js | LIVE_DATA | sog, budget, daemon, events | 2MB |
| health-data.js | HEALTH_DATA | overall, subscores.{system,fitness,telemetry} | 500KB |
| queue-data.js | QUEUE_DATA | queue.items, queue.counts | 500KB |
| crypto-data.js | CRYPTO_DATA | composite.score, project.security_gate | 1MB |
| mining-data.js | MINING_DATA | readiness.score, fleet.nodes_running | 1MB |
| wallet-data.js | WALLET_DATA | gate.security_gate, portfolio.positions | 500KB |
| research-data.js | RESEARCH_DATA | pipeline.total_digests, fleet.active_scouts | 1MB |
| git-data.js | GIT_DATA | repos | 500KB |
| task-summary-data.js | TASK_SUMMARY_DATA | summary.open_tasks, summary.by_priority | 5KB |
| task-data.js | TASK_DATA | summary.open_tasks | 1MB |
| ideas-data.js | IDEAS_DATA | summary.total_ideas, backlog.ready_to_build | 500KB |
| project-data.js | PROJECT_DATA | summary.total_projects, projects | 500KB |
| telegram-data.js | TELEGRAM_DATA | channel.live, health.score | 500KB |
| telegram-commands-data.js | TELEGRAM_COMMANDS_DATA | commands | 100KB |
| audit-trail-data.js | AUDIT_TRAIL_DATA | stats, stats.total_actions, recent_actions | 500KB |

## Safety Rules Enforced
- NO unbounded live execution
- NO hidden silent control paths
- NO batch approval without hard safeguards
- NO fake "implemented" claims
- NO hardcoded secrets
- Owner verdict required for all actions
- Dry-run/shadow mode default for new control paths

## How to Run
```batch
cd F:\backup\nervous-system
python run_ci.py
```

## Verification Log
- **2026-07-13:** 19/19 schema files pass; UI contract passes; security scan 0 findings.
