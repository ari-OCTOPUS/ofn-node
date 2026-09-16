---
title: CI / Drift Gate Spec
status: active
created: 2026-07-12
updated: 2026-07-12
tags: [octopus, ci, schema, drift-guard, wave-6, testing]
backlinks:
  - "[[WAVE-6-WORKING-NOTE]]"
  - "[[OCTOPUS-EXTRACTOR-REGISTRY]]"
---

# CI / Drift Gate Spec

> Automated verification that the nervous system data backbone and UI contract remain intact after changes.

## verify_schema.py

**Purpose:** Verify every `.js` data file matches its schema contract.

**Checks:**
1. File starts with `window.VAR_NAME = `
2. File ends with `;`
3. JSON is parseable
4. Required keys exist per contract:
   - `LIVE_DATA`: `.sog`, `.budget`, `.daemon`, `.events`
   - `HEALTH_DATA`: `.overall`, `.subscores.system/fitness/telemetry`
   - `QUEUE_DATA`: `.queue.items`, `.queue.counts`
   - `CRYPTO_DATA`: `.composite.score`, `.project.security_gate`
   - `MINING_DATA`: `.readiness.score`, `.fleet.nodes_running`
   - `WALLET_DATA`: `.gate.security_gate`, `.portfolio.positions`
   - `RESEARCH_DATA`: `.summary.digest_count`, `.summary.scout_count`
   - `GIT_DATA`: `.repos[].branch`, `.repos[].dirty_files`
   - `TASK_SUMMARY_DATA`: `.summary.open_tasks`, `.summary.by_priority`
   - `IDEAS_DATA`: `.summary.total_ideas`, `.backlog.ready_to_build`
   - `PROJECT_DATA`: `.summary.total_projects`, `.projects[].health`
   - `TELEGRAM_DATA`: `.channel.live`, `.health.score`
   - `TELEGRAM_COMMANDS_DATA`: `.commands`, `.commands[].mode`
   - `AUDIT_TRAIL_DATA`: `.stats.total_actions`, `.recent_actions`, `.freshness`
5. No NaN, no Inf, no null where numeric expected
6. File sizes within budget (largest: task-data.js < 1MB)

**Status:** 19/19 passing

## verify_ui_contract.py

**Purpose:** Verify `admin-telegram/index.html` UI contract.

**Checks:**
1. All `window.VAR_NAME` data references have matching `<script src>` tags
2. No orphaned script tags (loaded but not used)
3. Mode labels exist on all 13 panels
4. `actAll()` shows explicit "not implemented" warning
5. System banner has mode indicator + freshness

**Status:** Passing (1 warning: `octo-data.js` loads `OCTO_DATA` but not referenced — expected)

## run_ci.py

**Purpose:** Run both verifiers and exit non-zero on failure.

**Usage:**
```bash
cd nervous-system
python run_ci.py
```

**Integration:**
- Added to `refresh-live-data.bat` as optional last step (commented out by default)
- Uncomment to enable automated CI after every data refresh

## File References

- `nervous-system/verify_schema.py` — Schema contract verification
- `nervous-system/verify_ui_contract.py` — UI contract verification
- `nervous-system/run_ci.py` — CI runner
- `nervous-system/refresh-live-data.bat` — Data refresh pipeline
