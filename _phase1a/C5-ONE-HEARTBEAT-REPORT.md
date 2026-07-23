# C5 — ONE HEARTBEAT (Shadow Migration) — REPORT (2026-07-23)

> Goal: all Brain-Core organs under one beat + one HLC/beat_counter, no big-bang. Shadow-first.
> Authoritative: ONE-HEARTBEAT.md. Commit `d569743`. Flag `OCTOPUS_ONE_HEARTBEAT=0` (OFF).

## 1–2. Loop inventory (the "many heartbeats" to converge)
| loop | file:line | own clock | today |
|---|---|---|---|
| organism tick | organism.py main loop | 5-min tick | LIVE |
| chrono pacemaker | chrono.py:1361 `run_forever` (period_s) | own | LIVE |
| cortex cycle | cortex/cortex.py:556 `while True` + sleep(period) | own | LIVE (advisory) |
| doctor cycle | doctor/doctor.py:804 `run_cycle` | tick-driven | LIVE (advisory) |
| governor epoch | budget/governor_epoch.py:316 `run_epoch` | epoch min | LIVE (shadow) |
| approval poller | budget/approval_channel.py:427 `run_forever` | long-poll | (tg-center) |
| work_pump | heart/work_pump.py:184 interval | 300s | LIVE |
| code_autonomy | cortex/code_autonomy.py:407 `run_forever` every_s=300 | own | flag |
| legs (ingest/email/pocketsmith…) | various `while True`/sleep | own | mostly dormant |

→ Each has its own clock/loop → "organs don't know about each other" (the owner's complaint).

## 3. BeatScheduler (built, shadow, flag OFF)
- **One scheduler**, 8 deterministic phases: `SENSE→RECORD→THINK→DECIDE→PROPOSE→ACT→LEARN→HEAL`.
- **Organ contract** (step 5): `name, phase, every_n_beats, budget_ms, read_set, write_set, failure_policy, halt_behavior` — `register_organ(...)`; `contracts()` exposes them.
- **Bounded** (step 10/11): per-organ `budget_ms`; overrun flagged; repeated overrun/fail → **circuit-breaker quarantine** for K beats.
- **Organ failure isolation** (step 11): a throwing organ is caught fail-soft; **the beat never stops** (heart keeps beating when one limb falls).
- **Restart continuity** (step 12/13): `beat_counter` persisted atomically to `state/pulse/beat-state.json`; a fresh scheduler resumes at **beat+1** — never re-runs a prior beat.
- **HALT** (step 15 safety): under HALT only safe phases (`SENSE/RECORD/HEAL`) run; **ACT/effect blocked fail-closed**.
- **Zero double-actuation** (step 9): ACT phase is **dry-run by default** (`OCTOPUS_ONE_HEARTBEAT_ACT_ARMED` OFF) — so while legacy loops still actuate, the beat never issues a competing effect.
- **Events** (step 14): `system.beat`→spine each beat (beat_counter+HLC+provenance); `system.booted` already emitted (C2-E).
- **Watchdog** (step 15): `heartbeat_health()` detects stall/absence from the durable beat-state.

## Tests
- `test_beat_scheduler.py` **8/8** (virtual-time, deterministic): phase order, every_n_beats, budget+circuit-breaker, failure isolation, restart continuity, HALT-safe-phases, ACT dry-run, stall watchdog. Full sandbox suite: 271/271 (re-verifying).

## Migration status (shadow-first, per ONE-HEARTBEAT.md §migration)
- **Step 1 DONE**: BeatScheduler behind flag (OFF) — zero risk, zero live effect. Legacy loops **untouched**.
- **Steps 2–4 NEXT (owner-paced, needs live 24h parity)**: register cortex (advisory, lowest-risk) as the first organ with the legacy cortex loop running in parallel; run **24h parity** (beat-mode output ≡ loop-mode output); then doctor, live_loop, center — each with parity before the legacy loop goes compat.
- **Step 5–6 (APPROVAL)**: retire legacy loops to compat → Archive Packet (owner-gated); events.py/review_bus stay independent projections (C4 D-O4).

## Honest status
The **scheduler and all its safety properties are built and proven in shadow** (one scheduler, deterministic order, bounded, isolated, restart-safe, HALT-safe, no double-actuation). What remains is the **live per-organ shadow migration with 24h parity** — that is inherently a run-it-live-and-measure activity (not a code artifact), and per the mission it is staged, owner-paced, with ACT migrated **last** and dry-run first. So: C5's engineering deliverable (the one heartbeat) is complete and safe; the live parity soak + legacy-loop retirement is the next, owner-gated increment.

## C6 precondition status (owner asked "finish c5 first")
- one-event-spine (C4) ✓ · D8 green (C3, 2→4) ✓ · **one-heartbeat shadow parity: scheduler ready, live 24h parity pending** · HALT+rollback proven (C2/C4) ✓ · external/financial lanes owner-gated (disarmed) ✓ · Reality Battery ≥11/12 and D12 green (C2, 4→7) ✓.
→ The only unmet C6 gate is the **live 24h one-heartbeat parity soak**. C6 should not start until that soak is green (and the live STOP-METABOLIC halt is resolved).

## VERDICT: C5 SHADOW SCHEDULER DONE — live parity soak is the named next step
Rollback = flag stays 0 / revert `d569743`. Zero live effect today.
