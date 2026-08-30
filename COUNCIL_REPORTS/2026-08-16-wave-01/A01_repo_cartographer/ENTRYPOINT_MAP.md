# ENTRYPOINT MAP — A01 Repository Cartographer (2026-08-16)

## 1. The exact executable that begins the main organism runtime

**`F:\backup\_ops\RUN-ORGANISM.bat`** → calls `OCTOPUS-flags.cmd` (non-secret env flags) → `python -X utf8 organism.py`

`organism.py` (in `_ops/`) is the single always-on metabolic loop. Live proof: PID 29028,
started 2026-08-16T12:53:10, state file `_ops/state/ORGANISM-STATE.json` (ts 2026-08-16T23:49:11, beat 38507).

Its startup chain:
```
organism.py
  ├─ sys.path += _ops/budget  → imports opslib, telemetry, governor_epoch, fitness, replication
  ├─ optional: chrono, events, tick_timing (additive; loop survives if absent)
  ├─ binds 127.0.0.1:8771 (single-instance lock)
  └─ tick loop: kill-check → telemetry reconcile (FREEZE on mismatch) → governor epoch (shadow)
                → daily fitness/replication (shadow) → hourly heartbeat → state json
```
Most heavier subsystems are NOT started by organism.py directly; they are wired lazily through
**`_ops/wiring.py`** (4,347 lines), the composition root imported/invoked from the organism loop.

## 2. All executable entry points (repo F:/backup)

| # | Entry | Kind | Starts | Live? |
|---|-------|------|--------|-------|
| 1 | `_ops/RUN-ORGANISM.bat` → `organism.py` | .bat | organism loop (port 8771) | **YES** PID 29028 |
| 2 | `_ops/RUN-CORTEX.bat` / RESTART-CORTEX.ps1 → `cortex/cortex.py` | .bat/.ps1 | cortex controller (port 8772) | **YES** PID 11144 |
| 3 | `_ops/RUN-LIVE.bat` / run-live-headless.bat → `live/server.py` | .bat | live control room (port 8773) | **YES** PID 7852 |
| 4 | `_ops/telegram_center/RUN-TG-CENTER.bat` → `telegram_center/center.py` | .bat | telegram cockpit hub | **YES** PID 11724 |
| 5 | `_ops/board_cp/server.py` | .py | board command queue | **YES** PID 23464 |
| 6 | `_ops/telegram_center/miniapp_gateway.py` | .py | telegram web-app gateway | **YES** PID 19076 |
| 7 | `_ops/dashboard/RUN-DASHBOARD.bat` → `dashboard/server.py` | .bat | status dashboard (port 8770) | not observed |
| 8 | `_ops/RUN-CODE-AUTONOMY.bat`, `RUN-ZIMAN-OCTOPUS-TESTS.bat`, `now_moves/RUN-*.bat` | .bat | aux tasks | not observed |
| 9 | Watchdogs: `organism-watchdog.ps1`, `cortex-watchdog.ps1`, `live-watchdog.ps1`, `miniapp-watchdog.ps1`, `register-tg-center-watchdog.ps1` | .ps1 | keep-alive restarts | scheduled (schtasks) |
| 10 | `RESTART-ALL.bat/.ps1`, `RESTART-BOARDCP.ps1`, `RESTART-PROCESS.ps1`, `stop-organism.ps1` | .bat/.ps1 | lifecycle control | manual |
| 11 | `4d_system/run.py` | .py | CLI self-test OR `streamlit run run.py` dashboard | not observed running |
| 12 | `4d_system/start.bat` | .bat | **STALE** — cds to `C:\Users\Armin\Desktop\4d_system` which does NOT exist | broken |
| 13 | `4d_system/nbb-cp-kre/start.bat`, `run_dashboard.bat`, `run_quick_scan.bat` | .bat | KRE mini-app | not observed |
| 14 | `03 - Projects/NBB-Control-Plane/run.py` + `run_observatory.py` | .py | shadow-epoch demo; observatory updater | not observed in F:; observatory exists as schtasks |
| 15 | Desktop `OCTOPUS-NBB-CP-WORKING/nbb-control-plane/run.py`, `update_status.py`, `octopus_sync.py` | .py | separate repo; today 16:02 commit added status updater | dev-active |
| 16 | `07 - Knowledge/genome-system/run.py`, `research_loop.py` | .py | nested repo runner | not observed |
| 17 | `generate_report.py`, `generate_cover.py`, `merge_and_qa.py` (root) | .py | one-off AGI report generators | dormant |
| 18 | Windows Task Scheduler `OCTOPUS-*` (10 tasks) | OS | consolidation tick, poisoning watch, observatory hourly, cockpit-brain, doctor-day, 4 watchdogs | **Ready** (schtasks T0) |
| 19 | `nervous-system/refresh-live-data.bat` | .bat | refresh static dashboard data | not observed |
| 20 | `.claude/worktrees/*` (5 dirs) | git worktrees | agent working copies | exist |

## 3. Stale/phantom entry points

- `organism.py` docstring claims "8768 = brain lock (app.py)" — **no `app.py` exists anywhere in `_ops`**; port 8768 has no owner today. Stale lore embedded in live code comments.
- `4d_system/start.bat` points to non-existent `C:\Users\Armin\Desktop\4d_system`.
- Cortex registry member `fourd_system` is opt-in observe-only (`OCTOPUS_OBSERVE_4D`), marked DEPRECATED-disconnected until today.

## 4. Source directories imported during startup (organism cold start)

From `organism.py` + `wiring.py` static import scan:
`_ops/budget` (opslib, telemetry, governor_epoch, fitness, replication, approval_channel),
`_ops` root (chrono, events, tick_timing, wiring → doctor, suite_runner, unified_bus, leg, lead_leg,
cartographer_leg, live_loop, self_knowledge, sense, rhythm, circadian, sprint, reconcile,
approval_actuator, cardiac, epoch_guard, germline, fourd_access, lead_boundary_http,
lead_quote, invoice, deferral_rebuild, epistemics, spectral, neural_driver, hebbian,
consolidation, policy.policy_gate, spine adapters…),
`_ops/cortex` (registry, model_router — own process), `_ops/chord`, `_ops/neural`, `_ops/heart` via wiring.

Not imported at startup: `4d_system/**` (except via fourd_access observe lane), `nbb_cp` (no live process found),
`octopus_v3` (WIRED=False), genome-system code (only ledger file is written to by budget bridge).
