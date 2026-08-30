# 01 Scope and Method — A02 Runtime Investigator (CONSOLIDATED)

## Scope

Determine what is actually **executing** versus merely installed/documented, non-invasively:

1. Process, port, bus, queue, database and scheduled-job snapshot; map each live process to entry point, repo, commit and config source.
2. Observe ≥3 heartbeat cycles with no state regression and no observer writes.
3. Provenance of beat / coherence / identity_health / arbiter (+ runtime_state, readiness_state, bus_state, acquisition_state, safety_state) — live-computed, state-file, cached, defaulted or mocked.
4. Verify propose-only, money lock, destructive-action disablement, legs, OFF heartbeats — at runtime level, without exercising actions.
5. Config precedence; zombies/duplicates/orphans/stale PIDs; clock/timezone/timestamp audit; liveness-vs-readiness gaps.

Out of scope (covered by A04): attack-surface and injection-boundary auditing. Out of scope (A03): dataflow/contract/bitemporality verdicts beyond runtime liveness.

## Dual-observer note

Two independent READ_ONLY A02 instances worked this directory in overlapping windows (parallel: 23:48–23:54; primary: 23:44–23:59 +10:00). Methods were independently designed and are both documented; findings merged in `02_FINDINGS.md` (R-* parallel, F-* primary) and `03_EVIDENCE.jsonl` (observer-tagged).

## Method — all read-only

| Step | Tool/Command | Notes |
|---|---|---|
| Process snapshot | `powershell Get-CimInstance Win32_Process` (PID/PPID/Name/CreationDate/ExecutablePath/CommandLine) | full JSON kept in `raw/processes_snapshot1.json` (339 processes); no signaling, no handle inspection |
| Port snapshot | `netstat -ano` (LISTENING) | `raw/netstat_snapshot1.txt`; PIDs cross-referenced to processes |
| Scheduled jobs | `Get-ScheduledTask` + `Get-ScheduledTaskInfo` (script `raw/tasks.ps1`) | 12 OCTOPUS-related tasks mapped |
| Heartbeat observation | read-only sampler `raw/sampler.py`: stat + JSON-read of `ORGANISM-STATE.json`, `pulse/beat-state.json`, `pulse/arbiter-latest.json`, `chrono.db-wal`, `events.jsonl`, `_memory/HEARTBEAT.md`, 11×30 s | zero writes to observed files (writes only into this report dir); parallel observer sampled 3 points ≥60 s apart + `chrono.db` WAL mtime |
| Ledger liveness | `sqlite3` URI `mode=ro` on `_ops/state/chrono.db` — table list, row counts, PRAGMA table_info (parallel observer) | read-only URI; no writes |
| Config provenance | `_ops/state/flags-loaded-organism.json` (boot snapshot written by OCTOPUS itself, pid-tagged); launcher `.bat`/`.ps1` reads; `.env` key **names only** | secret values never read, printed or stored; loader redacts secrets itself |
| Code-to-runtime mapping | `grep -n` read-only on entry files + gates; two delegated read-only code-audit subagents (value provenance; safety enforcement) with file:line citations, spot-checked against live state | no tests executed, no imports of live modules |
| Git state | `git rev-parse HEAD`, `git show -s`, `git status --short`, file mtimes vs process CreationDates | drift analysis (F-23) |
| Clock audit | host TZ via `date`/`Get-TimeZone`; `grep time.monotonic` (0 hits); per-artifact timestamp convention comparison | `CLOCK_AND_TIMESTAMP_AUDIT.md` |

Artefacts produced: `LIVE_PROCESS_MAP.md`, `PORT_AND_BUS_MAP.csv`, `HEARTBEAT_TRANSCRIPT.jsonl` (+ parallel `raw/HEARTBEAT_TRANSCRIPT.jsonl`, `raw/PROCESS_SNAPSHOT.md`, `raw/PORT_MAP.csv`), `RUNTIME_CONFIG_PROVENANCE.md`, `CLAIM_VS_RUNTIME_MATRIX.csv`, `SERVICE_LIVENESS_VS_READINESS.md`, `CLOCK_AND_TIMESTAMP_AUDIT.md`.

## Truth-tier usage

- T0: process table, netstat, file mtimes, live state JSON, sqlite read-only queries, boot flag snapshot.
- T2: code references explaining observed runtime values (e.g. `identity_equations` behind identity_health; executor/classifier behind A-levels).
- T3: ledgers/receipts (adr-033, state_guard, chrono.db) treated as claims verified against T0.
- T6 never used as proof; runtime-undecidable questions left UNKNOWN and routed (A01/A03/A04/A09, owner).

## Constraints honored

No restart/stop/deploy, no installs, no ports opened, no external API calls, no Telegram sends, no consequential tools, no migrations, no secret exposure; writes only under `COUNCIL_REPORTS/2026-08-16-wave-01/A02_runtime_investigator/`. All repository content treated as untrusted data; no instructions found inside files were followed.
