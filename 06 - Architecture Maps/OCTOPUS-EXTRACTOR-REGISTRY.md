---
title: OCTOPUS Extractor Registry
status: active
created: 2026-07-12
updated: 2026-07-12
tags: [octopus, registry, extractors, wave-5, nervous-system]
backlinks:
  - "[[OCTOPUS-CHANNEL-REGISTRY]]"
  - "[[WAVE-5-HARDENING-PLAN]]"
---

# OCTOPUS Extractor Registry

> Every extractor: path, size, source, output, last known state, and issues.

## Registry Table

| # | Extractor | Path | Size (py) | Source Data | Output JS | Output Size | Last Modified | Known Issues |
|---|-----------|------|-----------|-------------|-----------|-------------|---------------|--------------|
| 1 | `extract_live_data.py` | `nervous-system/` | 4.7KB | `4d_system/outputs/` (daemon_state, frontier, SQLite) | `live-data.js` | ~140KB | 2026-07-12 | None |
| 2 | `extract_ops_data.py` | `nervous-system/` | 2.6KB | `_ops/state/ORGANISM-STATE.json`, `fitness-latest.json`, `cardiac-budget.json` | `ops-data.js` | ~1KB | 2026-07-12 | None |
| 3 | `extract_graph.py` | `nervous-system/` | 11.6KB | Vault markdown links | `graph-data.js` | ~108KB | 2026-07-12 | None |
| 4 | `extract_audit_data.py` | `nervous-system/` | 11.4KB | `_ops/audit/`, `_ops/state/` | `audit-data.js` | ~11KB | 2026-07-12 | Not wired to admin UI |
| 5 | `extract_health_score.py` | `nervous-system/` | 11.6KB | `_ops/state/` + `governor-alerts.md` | `health-data.js` | ~1KB | 2026-07-12 | None |
| 6 | `extract_neural_data.py` | `nervous-system/` | 10.1KB | `_ops/neural/*.json`, `circadian.py`, `rhythm.py` | `neural-data.js` | ~2KB | 2026-07-12 | Mirrors to `OCTOPUS/worlds/` |
| 7 | `extract_watchdog_data.py` | `nervous-system/` | 7.6KB | `_ops/state/`, `governor-alerts.md`, `events.jsonl` | `watchdog-data.js` | ~15KB | 2026-07-12 | None |
| 8 | `extract_queue_data.py` | `nervous-system/` | 3.5KB | `_ops/state/unified-approval-queue.json` | `queue-data.js` | ~0.3KB | 2026-07-12 | None |
| 9 | `extract_research_data.py` | `nervous-system/` | 11.4KB | `00 - Inbox/scout-digests/*.md` | `research-data.js` | ~4KB | 2026-07-12 | None |
| 10 | `extract_git_status_data.py` | `nervous-system/` | 10.3KB | Git repos under `F:/backup` | `git-data.js` | ~5KB | 2026-07-12 | None |
| 11 | `extract_wallet_data.py` | `nervous-system/` | 6.8KB | `03 - Projects/Crypto - etoro/` + `_ops/state/` | `wallet-data.js` | ~2KB | 2026-07-12 | None |
| 12 | `extract_mining_data.py` | `nervous-system/` | 14.3KB | `03 - Projects/Mining/` + `_ops/state/` | `mining-data.js` | ~7KB | 2026-07-12 | None |
| 13 | `extract_crypto_data.py` | `nervous-system/` | 14.8KB | `03 - Projects/Crypto - etoro/` | `crypto-data.js` | ~4KB | 2026-07-12 | LunarCrush data stale (June 2026) |
| 14 | `extract_project_index.py` | `nervous-system/` | 11.3KB | `03 - Projects/` subfolders | `project-data.js` | ~4KB | 2026-07-12 | None |
| 15 | `extract_ideas_backlog.py` | `nervous-system/` | 11.9KB | `00 - Inbox/` | `ideas-data.js` | ~84KB | 2026-07-12 | None |
| 16 | `extract_telegram_control.py` | `nervous-system/` | 9.9KB | `_ops/state/telegram/` | `telegram-data.js` | ~2KB | 2026-07-12 | Telegram stub mode (no creds) |
| 17 | `extract_obsidian_tasks.py` | `nervous-system/` | 8.0KB | Vault `.md` files | `task-data.js` | ~678KB | 2026-07-12 | Very large payload |
| 18 | `extract_task_summary.py` | `nervous-system/` | 3.6KB | `task-data.js` (derived) | `task-summary-data.js` | ~1.5KB | 2026-07-12 | Must run after #17 |
| 19 | `extract_telegram_commands.py` | `nervous-system/` | 12KB | `_ops/telegram_center/` | `telegram-commands-data.js` | ~7KB | 2026-07-13 | Wave 6 — safe command registry |
| 20 | `extract_audit_trail.py` | `nervous-system/` | 4KB | `_ops/state/action-audit.jsonl` | `audit-trail-data.js` | ~1.5KB | 2026-07-13 | Wave 6 — audit log display |

## Schema Verification Status

All 20 extractors inspected in Wave 6. **CI drift guard active: 19/19 JS outputs pass schema contract; UI contract verified.**

- JS variable names match UI destructuring: `L, O, H, Q, N, W, C, M, WL, R, G, TK, I, P, T, TC, AT`
- `TK` aliases `TASK_SUMMARY_DATA || TASK_DATA` for lightweight loading.
- New vars: `TC` = `TELEGRAM_COMMANDS_DATA`, `AT` = `AUDIT_TRAIL_DATA`.

## Dependency Graph

```
Group A (core organism)
  live_data ─┬─► ops_data
             ├─► health_score
             ├─► neural_data
             └─► watchdog_data

Group B (project channels)
  research ──► independent
  git ───────► independent
  wallet ────► independent
  mining ────► independent
  crypto ────► independent
  project ───► independent
  ideas ─────► independent
  telegram ──► independent
  queue ─────► independent

Group C (derived)
  obsidian_tasks ──► task_summary
```

## Maintenance Notes

- **refresh-live-data.bat** runs all extractors in dependency order.
- Total runtime: ~20-40 seconds.
- If one extractor fails, others continue (bat does not use `&&`).
- All extractors use stdlib only (no external pip dependencies).
