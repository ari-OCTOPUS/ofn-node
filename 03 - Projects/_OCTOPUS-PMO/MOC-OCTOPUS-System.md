---
type: moc
project: OCTOPUS
status: active
wave: 5
tags: [octopus, moc, system, pmo]
created: 2026-07-12
updated: 2026-07-13
---

# OCTOPUS System · MOC

> **What this is:** A navigational hub for all OCTOPUS system documentation in the vault.
> **Scope:** Channels, architecture, build waves, registries, and code references for the built system.
> **Last synced:** 2026-07-13 with filesystem evidence. Wave 5 complete. Wave 6 CI & drift guard complete.

---

## System at a Glance

| Metric | Value |
|---|---|
| **Channels** | 16 implemented + 2 Wave 6 |
| **Extractors** | 20 Python files |
| **Admin panels** | 13 |
| **Cockpit worlds** | 10 + hub |
| **JS data files** | 19 + graph |
| **Current wave** | Wave 6 complete ✅ (control plane hardening) |

---

## Unified Registries (Wave 6)

| Registry | Description | Link |
|---|---|---|
| **Channel Registry** | All 16+ channels with sources, outputs, status | [[OCTOPUS-CHANNEL-REGISTRY]] |
| **Extractor Registry** | All 20 extractors with schemas, sizes, issues | [[OCTOPUS-EXTRACTOR-REGISTRY]] |
| **Dashboard Map** | All 13 admin panels → data sources | [[OCTOPUS-ADMIN-DASHBOARD-MAP]] |
| **Known Risks** | Risk register with severity + mitigation | [[OCTOPUS-KNOWN-RISKS]] |
| **Wave 6 Spec** | CI, drift guard, audit, command surface | [[WAVE6-CI-DRIFT-GATE-SPEC]] |

---

## Channel Specifications (16 Channels)

### P1 Channels (Wave 2)

| Channel | Name | Status | Quick Link |
|---|---|---|---|
| **CH-04** | Telegram Bot Unified | ✅ Implemented | [[Channels/CH-04\|CH-04]] |
| **CH-07** | Health Score Composite | ✅ Implemented | [[Channels/CH-07\|CH-07]] |
| **CH-10** | Git Watcher + Self-Evolution | ✅ Implemented | [[Channels/CH-10\|CH-10]] |
| **CH-11** | Tracer + Audit Dashboard | ✅ Implemented | [[Channels/CH-11\|CH-11]] |
| **CH-14** | HITL Queue | ✅ Implemented | [[Channels/CH-14\|CH-14]] |
| **CH-16** | Neural Vitals | ✅ Implemented | [[Channels/CH-16\|CH-16]] |
| **CH-17** | Watchdog Alerts | ✅ Implemented | [[Channels/CH-17\|CH-17]] |

### Wave 3–4 Channels

| Channel | Name | Status | Detail |
|---|---|---|---|
| **CH-01** | Research Scout Fleet | ✅ Implemented | [[OCTOPUS-CHANNEL-REGISTRY\|Registry]] |
| **CH-02** | Git Status | ✅ Implemented | [[OCTOPUS-CHANNEL-REGISTRY\|Registry]] |
| **CH-03** | Vault Graph Scanner | ✅ Implemented | [[OCTOPUS-CHANNEL-REGISTRY\|Registry]] |
| **CH-05** | Obsidian Task Queue | ✅ Implemented | [[OCTOPUS-CHANNEL-REGISTRY\|Registry]] |
| **CH-08** | Crypto / eToro + Wallet | ✅ Implemented | [[OCTOPUS-CHANNEL-REGISTRY\|Registry]] |
| **CH-09** | Mining Fleet Monitor | ✅ Implemented | [[OCTOPUS-CHANNEL-REGISTRY\|Registry]] |
| **CH-12** | Ideas Backlog | ✅ Implemented | [[OCTOPUS-CHANNEL-REGISTRY\|Registry]] |
| **CH-13** | Project Architecture Index | ✅ Implemented | [[OCTOPUS-CHANNEL-REGISTRY\|Registry]] |
| **CH-15** | Telegram Control Surface | ✅ Implemented | [[OCTOPUS-CHANNEL-REGISTRY\|Registry]] |

---

## Architecture

| Topic | Description | Link |
|---|---|---|
| **Dataflow** | Source → Transform → Sink pipeline | [[Architecture/Dataflow\|Dataflow]] |
| **Backbone** | Shared JS data layer (`octo-data.js`, `shared-ui.js`) | [[Architecture/Backbone\|Backbone]] |
| **Admin-UI** | Mobile-first Telegram admin dashboard | [[Architecture/Admin-UI\|Admin-UI]] |

---

## Build Waves

| Wave | Goal | Status | Link |
|---|---|---|---|
| **Wave 1** | Nervous system foundation (3 extractors) | ✅ Done | [[Build Waves/Wave-1\|Wave-1]] |
| **Wave 2** | 7 P1 channels | ✅ Done | [[Build Waves/Wave-2\|Wave-2]] |
| **Wave 3** | Cockpit worlds + preview | ✅ Done | [[Build Waves/Wave-3\|Wave-3]] |
| **Wave 4** | Full channel fleet (16 channels, 17 extractors) | ✅ Done | [[Build Waves/Wave-4\|Wave-4]] |
| **Wave 5** | Hardening: stability, observability, control | ✅ Done | [[OCTOPUS-WAVE5-HARDENING-PLAN\|Wave-5 Plan]] |
| **Wave 6** | Control plane: gated, testable, replayable, owner-aware | ✅ Done | [[Build Waves/Wave-6\|Wave-6 Note]] |

---

## Code Reference

| System | Key Files | Purpose |
|---|---|---|
| **Extractors** | `nervous-system/extract_*.py` (17 files) | Data pipeline |
| **Task Summary** | `nervous-system/extract_task_summary.py` | Lightweight summary for dashboard |
| **Telegram Bot** | `4d_system/brain/telegram_bot_unified.py` | Unified HITL interface |
| **Approval Merge** | `_ops/budget/approval_channel_merge.py` | Cross-system approval bridge |
| **Approval Queue** | `_ops/budget/approval_queue_unified.py` | Unified HITL queue |
| **Tracer** | `_ops/observability/tracer.py` | Content-free telemetry |
| **Git Watcher** | `4d_system/brain/git_watcher.py` | Self-evolution trigger |
| **Orchestrator** | `nervous-system/refresh-live-data.bat` | 17-extractor runner |
| **Admin UI** | `OCTOPUS/admin-telegram/index.html` | 13-panel mobile dashboard |
| **Preview** | `OCTOPUS/admin-telegram/preview.html` | Self-contained offline preview |
| **Hub** | `OCTOPUS/worlds/index.html` | 10-world navigation hub |
| **Cockpit** | `OCTOPUS/worlds/01-cockpit/index.html` | Mission control |

---

## External References

| Document | Role | Path |
|---|---|---|
| **Program Charter** | Governance baseline | [[PROGRAM-CHARTER\|PROGRAM-CHARTER]] |
| **RACI** | Roles & responsibilities | [[RACI\|RACI]] |
| **Decision Register** | Unified decisions | [[UNIFIED-DECISION-REGISTER\|UNIFIED-DECISION-REGISTER]] |
| **SOT Matrix** | Source of truth mapping | [[SOURCE-OF-TRUTH-MATRIX\|SOURCE-OF-TRUTH-MATRIX]] |
| **Policy Register** | Active policy status | [[POLICY-STATUS-REGISTER\|POLICY-STATUS-REGISTER]] |

---

## Related Vault Areas

- **04 - Architect System/** — Build prompts, architecture maps, SOG synthesis
- **05 - Agents/** — Agent registry, ratified tasks, scout fleet
- **06 - Architecture Maps/** — System maps, ecosystem, HEART neuro-map
- **07 - Knowledge/genome-system/** — Ledger, genome, tests
- **OCTOPUS/** — Built HTML/JS dashboards (not vault notes)
- **nervous-system/** — Python extractors + JS data files

---

## How to Use This MOC

1. **Find a channel:** Use the channel table above, the [[OCTOPUS-CHANNEL-REGISTRY]], or search `CH-XX`
2. **Understand data flow:** Read [[Architecture/Dataflow\|Dataflow]]
3. **Check build status:** Read [[Build Waves/Wave-4\|Wave-4]]
4. **Navigate to code:** Use the Code Reference table, then open files in `nervous-system/` or `_ops/`
5. **Check risks:** Read [[OCTOPUS-KNOWN-RISKS]]
6. **See panel mapping:** Read [[OCTOPUS-ADMIN-DASHBOARD-MAP]]

---

> **Steward note:** This MOC is updated by the Obsidian Steward agent when the filesystem changes. Last verification: 2026-07-13 (Wave 6 complete).
