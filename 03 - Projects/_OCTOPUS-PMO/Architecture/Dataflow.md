---
type: architecture
status: implemented
wave: 1-2
tags: [octopus, dataflow, architecture, nervous-system]
created: 2026-07-12
updated: 2026-07-12
---

# Architecture · Dataflow

> **Pattern:** Source → Transform → Sink (read-only extractors)
> **Runtime:** `refresh-live-data.bat` orchestrates 9 extractors

---

## Layer Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    SOURCE LAYER                              │
│  _ops/              4d_system/           07 - Knowledge/      │
│  ─────              ─────────           ──────────────       │
│  ORGANISM-STATE     daemon_state.json   genome ledger        │
│  fitness-latest     4d_experiments.db   ledger.jsonl         │
│  telemetry-latest   frontier.json                          │
│  cardiac-budget     outputs/                               │
│  events.jsonl       self_evolved/                          │
│  traces.jsonl                                              │
│  governor-alerts                                           │
│  unified-approval-queue                                    │
│  neural/*.json                                             │
└────────────────────────┬────────────────────────────────────┘
                         │  read-only (no mutation)
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                   TRANSFORM LAYER                            │
│           nervous-system/  (9 extractors)                    │
│  ─────────────────────────────────────────                   │
│  extract_live_data.py     ← 4d_system outputs → live-data.js │
│  extract_ops_data.py      ← _ops/state        → ops-data.js  │
│  extract_graph.py         ← vault notes       → graph-data.js│
│  extract_audit_data.py    ← events+traces     → audit-data.js│
│  extract_health_score.py  ← org+fit+tel       → health-data.js│
│  extract_watchdog_data.py ← org+alerts        → watchdog-data.js│
│  extract_neural_data.py   ← neural stack      → neural-data.js│
│  extract_queue_data.py    ← approval queue    → queue-data.js│
└────────────────────────┬────────────────────────────────────┘
                         │  JS data files
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                     SINK LAYER                               │
│  OCTOPUS/                                                    │
│  ───────                                                     │
│  admin-telegram/index.html  ← 7 × .js (live, ops, health,    │
│                               queue, neural, watchdog, octo) │
│  worlds/index.html          ← octo-data.js + shared-ui.js    │
│  worlds/01-cockpit/         ← live-data.js + queue badge     │
│  worlds/04-twin/            ← audit-data.js                  │
│  worlds/06-time/            ← neural-data.js (circadian)     │
│  worlds/08-risk/            ← health + watchdog              │
└─────────────────────────────────────────────────────────────┘
```

---

## Extractor Registry

| # | Extractor | Source | Sink | Wave | Channel |
|---|---|---|---|---|---|
| 1 | `extract_live_data.py` | `4d_system/outputs/` | `live-data.js` | 1 | — |
| 2 | `extract_ops_data.py` | `_ops/state/` | `ops-data.js` | 1 | — |
| 3 | `extract_graph.py` | Vault notes graph | `graph-data.js` | 1 | — |
| 4 | `extract_audit_data.py` | `events.jsonl` + `traces.jsonl` | `audit-data.js` | 2 | CH-11 |
| 5 | `extract_health_score.py` | `ORGANISM-STATE` + fitness + telemetry | `health-data.js` | 2 | CH-07 |
| 6 | `extract_watchdog_data.py` | `ORGANISM-STATE` + alerts + events | `watchdog-data.js` | 2 | CH-17 |
| 7 | `extract_neural_data.py` | `_ops/neural/` + `chrono_rhythm/` | `neural-data.js` | 2 | CH-16 |
| 8 | `extract_queue_data.py` | `unified-approval-queue.json` | `queue-data.js` | 2 | CH-14 |
| 9 | `extract_graph.py` *(extended)* | Vault graph | `graph-data.js` | 2 | — |

---

## Orchestration

`nervous-system/refresh-live-data.bat`:
```batch
@echo off
chcp 65001 >nul
set PYTHONUTF8=1
cd /d "%~dp0"
echo Refreshing OCTOPUS live data...
python extract_live_data.py
python extract_ops_data.py
python extract_graph.py
python extract_audit_data.py
python extract_health_score.py
python extract_watchdog_data.py
python extract_neural_data.py
python extract_queue_data.py
echo Done.
```

**Execution time:** ~5-15 seconds total (all stdlib-only, offline).

---

## Contract

- **Read-only:** No extractor mutates source files
- **Fail-soft:** Missing source → default/empty output, never crash
- **Content-free:** No secrets, PII, or API keys in JS outputs
- **Idempotent:** Re-running produces same output given same input
- **Self-contained:** Each extractor can run standalone

---

## Related

- [[Backbone]] — shared JS data layer consumed by sinks
- [[Admin-UI]] — primary sink (admin-telegram/index.html)
- [[Wave-1]] — first three extractors
- [[Wave-2]] — P1 channel extractors
