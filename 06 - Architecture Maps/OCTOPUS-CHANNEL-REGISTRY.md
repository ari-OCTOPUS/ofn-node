---
title: OCTOPUS Channel Registry
status: active
created: 2026-07-12
updated: 2026-07-12
tags: [octopus, registry, wave-5, channels, nervous-system]
backlinks:
  - "[[OCTOPUS-EXTRACTOR-REGISTRY]]"
  - "[[ADMIN-TELEGRAM-DASHBOARD-MAP]]"
  - "[[OCTOPUS-KNOWN-RISKS]]"
---

# OCTOPUS Channel Registry

> Unified registry of all 16 data channels feeding the OCTOPUS dashboard and worlds.

| # | Channel | Name (FA) | Source Files | Extractor | JS Output | UI Panel | Status |
|---|---------|-----------|--------------|-----------|-----------|----------|--------|
| CH-00 | Core Vitals | وضعیتِ زنده | `4d_system/outputs/` | `extract_live_data.py` | `live-data.js` | Vitals | ✅ implemented |
| CH-00 | Ops State | عملیات | `_ops/state/` | `extract_ops_data.py` | `ops-data.js` | Vitals (wires) | ✅ implemented |
| CH-01 | Research Scout | اسکاوت / تحقیق | `00 - Inbox/scout-digests/` | `extract_research_data.py` | `research-data.js` | Research | ✅ implemented |
| CH-02 | Git Status | وضعیتِ گیت | `.git/` repos | `extract_git_status_data.py` | `git-data.js` | Git | ✅ implemented |
| CH-05 | Task Queue | صفِ کارها | Vault `.md` files | `extract_obsidian_tasks.py` | `task-data.js` | Tasks | ✅ implemented |
| CH-07 | Health Score | سلامتِ سیستم | `_ops/state/` | `extract_health_score.py` | `health-data.js` | Health | ✅ implemented |
| CH-08 | Wallet / eToro | کیف پول | `03 - Projects/Crypto - etoro/` | `extract_wallet_data.py` | `wallet-data.js` | Wallet | ✅ implemented |
| CH-08 | Crypto Market | کریپتو / eToro | `03 - Projects/Crypto - etoro/` | `extract_crypto_data.py` | `crypto-data.js` | Crypto | ✅ implemented |
| CH-09 | Mining Fleet | ماینینگ | `03 - Projects/Mining/` | `extract_mining_data.py` | `mining-data.js` | Mining | ✅ implemented |
| CH-12 | Ideas Backlog | بک‌لاگِ ایده‌ها | `00 - Inbox/` | `extract_ideas_backlog.py` | `ideas-data.js` | Ideas | ✅ implemented |
| CH-13 | Project Index | ایندکسِ پروژه‌ها | `03 - Projects/` | `extract_project_index.py` | `project-data.js` | Projects | ✅ implemented |
| CH-15 | Telegram Control | کنترلِ تلگرام | `_ops/state/telegram/` | `extract_telegram_control.py` | `telegram-data.js` | Telegram | ⚠️ stub mode |
| CH-15b | Telegram Commands | دستوراتِ تلگرام | `_ops/telegram_center/` | `extract_telegram_commands.py` | `telegram-commands-data.js` | Telegram | ✅ implemented (read-only registry) |
| CH-16 | Neural Stack | شبکهٔ عصبی | `_ops/neural/` | `extract_neural_data.py` | `neural-data.js` | Neural | ✅ implemented |
| CH-17 | Watchdog | نگهبان | `_ops/governor/` | `extract_watchdog_data.py` | `watchdog-data.js` | (implicit) | ✅ implemented |
| CH-18 | Audit Trail | ردپای حسابرسی | `_ops/state/action-audit.jsonl` | `extract_audit_trail.py` | `audit-trail-data.js` | Audit (admin) | ✅ implemented |
| — | Graph Ontology | گرافِ هستی‌شناسی | Vault `.md` links | `extract_graph.py` | `graph-data.js` | Ontology (world 02) | ✅ implemented |
| — | Audit Events | ردپای رویدادها | `_ops/audit/` | `extract_audit_data.py` | `audit-data.js` | (world 04) | ✅ implemented |

## Status Legend

- **✅ implemented**: Extractor runs, JS emits, UI renders, schema verified.
- **⚠️ stub mode**: Extractor runs but source system is not fully operational (e.g. Telegram bot has no credentials → `live=false`).
- **🔄 partial**: Some sub-features missing.
- **⏸️ stale**: Source data outdated (e.g. LunarCrush cache from June 2026).

## Channel → World Mapping

| World | Channels Used |
|-------|---------------|
| 01-cockpit | live, neural, health, research, task-summary, git |
| 02-ontology | graph-data.js |
| 03-money | live, ops |
| 07-decision | live (packets) |
| 08-risk | live (drift, budget, daemon, packets) |
| Hub index | live, neural, task-summary, git, graph |

## Notes

- Total active channels: 18 (16 Wave 1-5 + 2 Wave 6)
- Total extractors: 20 (18 Wave 1-5 + 2 Wave 6)
- All extractors are read-only and fail-soft.
- No extractor mutates source data.
- CI drift guard: `verify_schema.py` + `verify_ui_contract.py` + `run_ci.py` active
