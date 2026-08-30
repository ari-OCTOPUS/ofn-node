# DESIGN — Tick Decoupling (M2.2, speed)

Status: PROPOSE-ONLY draft. Nothing here is applied to the live organism at `F:\backup`.
Author: read-only architect. Verified against live code 2026-07-24.

Supersedes: the stub named in the mission brief (`F:\backup\_ops\DESIGN-tick-decoupling.md`)
**does not exist on disk** — verified by glob over `F:\backup\_ops\**\DESIGN-tick*.md` (no
files found). This document is therefore the first real design for M2.2.

---

## 0. Verified reality (ground truth, cited)

Every claim below was confirmed by reading the live files, not hearsay.

- **One thread does everything.** `organism.py` runs a single `while True:` loop
  (`F:\backup\_ops\organism.py:388`) with `TICK_SECONDS = 300`
  (`organism.py:58`). The same thread does kill-check, telemetry, *and* every brain/organ
  beat, then `time.sleep(_sleep_s)` at the bottom (`organism.py:884`).
- **The heavy work is all inline.** Between the kill-check (`organism.py:424-430`) and the
  final state write (`organism.py:820-841`), the loop runs ~30 organ beats inline:
  neural/protective (`:471-502`), epoch (`:506-511`), stale-effect sweep (`:513-523`),
  daily fitness/replication/ledger-verify/reconcile/fisher/c6 (`:525-578`),
  doctor (`:581-585`), doctor self-knowledge (`:590-593`), consolidation (`:596-601`),
  cockpit/tg-exec (`:603-610`), afferent (`:614-630`), publish_tick_signals (`:635-643`),
  leg (`:648-653`), ziman (`:657-664`), proposal router (`:672-684`),
  cartographer (`:689-695`), business_legs (`:701-706`), asset_map (`:711-716`),
  acct (`:721-726`), email (`:729-733`), harvest (`:738-742`), lead_discovery (`:747-752`),
  legs_cultivation (`:757-763`), scheduler_seed (`:766-771`), idea (`:774-778`),
  epistemics (`:781-785`), heart (`:789-793`), nudges/digests (`:796-812`).
- **Isolation already exists.** Every organ call is already wrapped in its own
  `try/except ... opslib.alert([...])` (fail-soft, charter §4). We reuse this pattern
  unchanged — the decoupling adds a second layer (per-task + per-thread), it does not
  replace the per-organ layer.
- **A background beat thread already exists.** The chrono `Pacemaker` already runs in its
  own daemon thread via `chrono.start_pacemaker_thread(...)` (`organism.py:371-376`;
  `chrono.py:1377-1391`, loop `chrono.py:1361-1370`) with its own `PERIOD_S≈60s`. So a
  second worker thread is idiomatic here, not novel.
- **A pub/sub substrate already exists.** `UnifiedBus.subscribe/publish/_notify`
  (`unified_bus.py:50-97`) delivers advisory events to in-process subscribers; `ChronoBus`
  also broadcasts (`chrono.py:515-522`). Both already swallow subscriber exceptions.
- **A correlation-id substrate already exists.** The loop mints one run-scoped
  correlation id per tick via `_events.begin_run()/end_run()`
  (`organism.py:402`, `:849-853`). `EventSpine.publish` *requires* a
  `correlation_id/trace_id` (`spine/event_spine.py:101-106`).
- **State is single-writer to disk.** Only `_write_state` writes
  `ORGANISM-STATE.json`, through `opslib.LockedJson` (`organism.py:166-192`), and it
  already has a `merge_prev` "freeze last-known block while ts advances" mode
  (`organism.py:174-187`).
- **Restart-safety is boot-time and disk-based.** `journal_recovery.boot_recovery()`
  (`organism.py:305-318`), `boot_certificate.emit_birth_certificate()` (`:319-336`),
  and `pending_card_recovery` (`:338-358`) all run once at boot, before the loop.
  Durable state lives in `chrono.db`, the genome ledger, and journals — never in loop
  memory.
- **Kill/restart semantics.** Clean exit on `STOP-ORGANISM`, `master_halted()`, or the
  `RESTART-REQUESTED` marker (`organism.py:424-430`); the launcher clears only
  `RESTART-REQUESTED` and never the owner's `STOP-ORGANISM` (`organism.py:420-423`).
- **Effector safety is independent of the loop.** `EffectorGate` re-checks
  `force_closed()` (STOP/HALT/FREEZE) on *every* release/settle/execute call
  (`chrono.py:560-569, 624-626, 694-699, 781-786, 807-812, 845-855`) and is
  CAS/idempotent (`chrono.py:571-609, 688-751, 803-874`). Moving a beat to a worker
  thread cannot weaken this — the gate guards itself.
- **Governance boundary.** `SELF_IMPROVEMENT_FORBIDDEN` =
  `{edit_constitution, edit_verifier, expose_heldout_answers, alter_acceptance_criteria,
  acquire_credentials, replicate, resist_shutdown, conceal_failures, merge_or_deploy}`
  (`F:\backup\PRE-0\governance.py:59-63`). This design takes **none** of these actions:
  it re-arranges *how* existing beats are scheduled, changes no verifier/constitution, and
  adds no new effector. Kill remains supreme; `resist_shutdown` is impossible because the
  metabolic core owns kill-check and workers are daemon threads joined on stop.

---

## 1. Problem

The base tick is 300s and everything shares one thread. Consequences:

1. **Latency floor.** Any task queued for the organism waits up to 300s for the next
   tick — e.g. an owner Telegram command is only consumed by `cockpit_requests_beat`
   (`organism.py:603-610`) once per tick.
2. **Head-of-line blocking.** A slow beat (network harvest, doctor LLM self-knowledge,
   a stalled organ) delays *everything after it in the tick*, including the next
   kill-check. Under the charter, the kill-switch must be honored promptly; today a slow
   organ can push the next `STOP` check out by the length of the slow beat.
3. **Coupling of cadence and safety.** The 5-minute cadence of productive work is welded
   to the cadence of the metabolic vitals (kill-check, telemetry, state write, heartbeat).

## 2. Goal

Split the one loop into two concerns:

- **(A) Metabolic core** — a *thin* tick every N seconds that does **only**:
  kill-check → telemetry snapshot/reconcile → germline staleness (safety-vital, cheap)
  → chrono status read → state write → hourly heartbeat → emit one tick event.
  It **never** runs brain/organ-heavy work and **never blocks** on it.
- **(B) Brain workers** — event-driven worker thread(s) fed by an in-process queue
  (thin wrapper over the existing `queue.Queue`; conceptually the same "one bus" idea as
  `UnifiedBus`). They run the ordered organ pipeline, each cycle under its own
  correlation id, each organ + each task + each worker thread isolated so nothing they do
  can kill the metabolic core.

Non-negotiables preserved: worker crash ≠ core death; restart-from-disk resume; clean
`STOP`/`RESTART-REQUESTED`; genome/kill-switch/boot-path untouched except via owner-gate.

---

## 3. Architecture

```
                          ┌──────────────────────────────────────────────┐
                          │  METABOLIC CORE  (organism.py main thread)     │
                          │  every N s (cardiac/heart period logic kept):  │
   STOP/HALT/RESTART ───► │   1. kill-check  → clean exit (authoritative)  │
                          │   2. telemetry.snapshot() + reconcile()        │
                          │   3. germline staleness enrich (cheap, vital)  │
                          │   4. chrono.status() read (cheap)              │
   ORGANISM-STATE.json ◄──│   5. _write_state( base + latch.snapshot() )   │
                          │   6. hourly organism=ok heartbeat              │
                          │   7. latch.workers_alive? else alert           │
                          │   8. pool.submit_tick(ctx)  ── put_nowait ──┐  │
                          │   9. time.sleep(period)                     │  │
                          └─────────────────────────────────────────────┼──┘
                                                                         │ (bounded queue;
                                       coalesce/drop if full, never block│  put_nowait)
                          ┌──────────────────────────────────────────────▼─┐
                          │  BRAIN WORKER POOL  (brain_worker.py, daemons)  │
                          │  supervisor restarts a dead worker (breaker)    │
                          │  worker loop:                                   │
                          │    task = queue.get()                           │
                          │    with events.begin_run()/end_run():  ← corr id│
                          │      try: dispatch(task)   except: alert (soft)  │
                          │                                                 │
                          │  dispatch("tick")  → TickPipeline.run(ctx):     │
                          │    (self-gated on kill + protective)            │
                          │    neural/protective → prot_state → latch       │
                          │    epoch, sweep, daily, doctor, consolidation,  │
                          │    cockpit, afferent, publish, leg, ziman,      │
                          │    proposals, cartographer, business, asset,    │
                          │    acct, email, harvest, lead, cultivation,     │
                          │    scheduler_seed, idea, epistemics, heart,     │
                          │    nudges/digests  → each block into latch      │
                          │  dispatch("cockpit") → cockpit_requests_beat    │
                          │    (immediate; the latency payoff — see §7)     │
                          └─────────────────────────────────────────────────┘
```

Two shared objects connect the halves, both thread-safe, both in-memory only:

- **`WorkQueue`** — a bounded `queue.Queue`. The core is the producer (`put_nowait`); if
  full (previous cycle still running = overloaded), the tick event is **coalesced/dropped**
  with an alert. Dropping a cadence tick is harmless: beats are cadence-gated by
  `beat % N` and idempotent, and durability lives in chrono.db/ledger, not the queue.
  This is the property that guarantees the core **never blocks** on brain work.
- **`StateLatch`** — a `dict` behind a `Lock`. Workers only ever write their own organ
  *block* into it (e.g. `latch.set("leg", status)`). The metabolic core reads a snapshot
  (`latch.snapshot()`) and merges it into the single disk write. This preserves the
  single-writer-to-disk invariant and the existing "freeze last-known block while ts
  advances" behavior (`organism.py:174-187`).

### Why threads, not asyncio

The whole codebase is thread-based (chrono pacemaker, telegram poll, doctor
self-knowledge all use `threading.Thread(daemon=True)`), `chrono.db` is a single-writer
SQLite guarded by an `RLock` with `check_same_thread=False` (`chrono.py:252-255,427-435`),
and everything is stdlib-only/$0. A `threading` + `queue.Queue` design drops straight into
the existing model with no new dependency and no event-loop rewrite.

### Worker count

Default **1 worker** (`OCTOPUS_BRAIN_WORKERS=1`). One worker draining the queue is enough
to hit the goal: the metabolic cadence is decoupled and a tick event is picked up
immediately instead of waiting for the next 300s boundary. One worker also keeps the tick
pipeline strictly ordered (afferent→publish, legs→proposal router — real intra-cycle
dependencies, `organism.py:614-684`) and adds **zero** new `chrono.db` write contention.

`OCTOPUS_BRAIN_WORKERS=N (>1)` is supported for running *auxiliary* event kinds
(e.g. immediate `cockpit`) concurrently with a tick cycle. A `tick_lock` guarantees only
one `tick` cycle runs at a time even with N>1, so ordering is never violated. N>1 is an
optimization, off by default.

---

## 4. Exact beat map — what moves, what stays

| Current in-loop beat (organism.py) | Lines | Destination | Rationale |
|---|---|---|---|
| `RESTART/STOP/HALT` kill-check + clean exit | 420-430 | **STAY (core)** | Authoritative kill must be prompt & synchronous |
| `telemetry.snapshot()` + `telemetry.reconcile()` | 431-432 | **STAY (core)** | Mission: metabolic vitals; feeds ctx to workers |
| `chrono.status()` read (`_cstat`) | 438-441 | **STAY (core)** | Cheap read; supplies `beat` to state + ctx |
| germline staleness enrich | 446 | **STAY (core)** | Safety-vital staleness sensor, cheap, no organ work |
| hourly `organism=ok` heartbeat | 813-819 | **STAY (core)** | Cheap append; liveness signal |
| `_write_state(...)` | 820-841 | **STAY (core)** | Single disk writer; merges latch blocks |
| cardiac/heart period + `time.sleep` | 854-884 | **STAY (core)** | Sets the metabolic cadence itself |
| rhythm/circadian + `neural_beat` + `protective_override` | 452-502 | **MOVE (worker, pipeline step 1)** | Brain work; self-gates the rest of the cycle |
| `governor_epoch.run_epoch` + stale-effect sweep | 506-523 | **MOVE** | Shadow epoch = organ work |
| daily fitness/replication/ledger-verify/reconcile/fisher/c6 | 525-578 | **MOVE** | Heaviest block; runs ≤1×/day, cadence-gated |
| `doctor_beat` | 581-585 | **MOVE** | Organ |
| `doctor_selfknowledge_beat` (already spawns its own daemon) | 590-593 | **MOVE** | Organ; keep its internal thread |
| `consolidation_beat` | 596-601 | **MOVE** | Organ |
| `cockpit_requests_beat` (tg-exec) | 603-610 | **MOVE** + also `cockpit` event | The latency win (§7) |
| `afferent_beat` (updates `_last_afferent_ratio`) | 614-630 | **MOVE** | Organ; carry-state now owned by pipeline |
| `publish_tick_signals` | 635-643 | **MOVE** | Bus fan-out, advisory |
| `leg_beat` / `ziman_beat` / `cartographer_beat` | 648-695 | **MOVE** | Limbs |
| proposal router + `proposal_metrics` | 672-684 | **MOVE** | Depends on limb beats (order kept in pipeline) |
| business_legs / asset_map / acct / email / harvest / lead_discovery / legs_cultivation | 701-763 | **MOVE** | Organs; several do network/IO — prime blockers |
| `scheduler_seed_beat` | 766-771 | **MOVE** | Organ |
| `idea_beat` / `epistemics_beat` / `heart_beat` | 774-793 | **MOVE** | Organs |
| needs/discovery/heartbeat_summary/cortex_vitals/doctor|brain|heart digests | 796-812 | **MOVE** | Telegram IO — blockers |
| per-tick `events.begin_run/end_run` | 402,849-853 | **MOVE** (per task in worker) | One correlation id per *cycle*, now per task |

### Carry-state migration

Five loop-locals persist across ticks today:
`last_daily` (`:379`), `next_epoch_at` (`:378`), `_last_sigma` (`:384`),
`_last_afferent_ratio` (`:385`), `_ziman_last` (`:386`). All five belong to the brain
cycle, not the metabolic core, so they become **instance fields of `TickPipeline`** (the
worker owns them). The metabolic core no longer references them at all.

### Protective-halt: fully inside the pipeline

Today `_protective_skip` is computed *and* consumed within the same tick body
(`organism.py:389,471-502` set it; `:506,525,581,...` read it). In the decoupled model,
neural/protective is **step 1 of `TickPipeline.run`** and every subsequent organ in the
same cycle self-gates on `self.protective_skip` — byte-for-byte the same gating logic,
just relocated. The metabolic core does **not** need the protective decision (it does no
productive work to gate); it only reflects `prot_state`/`protective_skip` in the state
write, which the pipeline publishes into the latch. This is what lets the metabolic tick be
"kill-check + telemetry + state + heartbeat ONLY," honoring the mission strictly.

Kill remains doubly enforced: the metabolic core's kill-check is authoritative and
synchronous, **and** `publish_tick_signals`/`EffectorGate`/each beat still re-check
`STOP/halt` independently (`wiring.py:335`, `chrono.py:560-569`), so a queued tick event
that starts running just as `STOP` lands is refused by those inner gates.

---

## 5. Failure isolation (worker crash must NOT kill core)

Three nested layers, the inner two already exist and are reused verbatim:

1. **Per-organ** — each organ call keeps its existing
   `try/except → opslib.alert` (charter §4). One organ failing does not stop the cycle.
2. **Per-task** — the worker wraps each dequeued task in `try/except → alert`. A task
   raising does not stop the worker.
3. **Per-thread (supervisor)** — if a worker thread escapes its loop entirely, a
   supervisor restarts a fresh worker, with a **circuit-breaker** (≤3 restarts / 300s,
   mirroring the chrono self-heal breaker at `chrono.py:1220-1254`). If the breaker trips,
   `latch["workers_down"]=reason` is surfaced in `ORGANISM-STATE.json` + an alert fires.

Crucially, the metabolic core runs on a **different thread**. Even if *every* worker dies,
the core keeps doing kill-check + telemetry + state write + heartbeat, so the organism
stays visibly alive and killable, and the dead-workers condition is observable — it never
degrades to a silent stall (the exact failure mode the charter §4 forbids).

---

## 6. Restart-safety & kill/restart

- **Boot recovery unchanged and ordered-first.** `journal_recovery.boot_recovery`,
  `boot_certificate`, and `pending_card_recovery` still run once at boot *before* the loop
  (`organism.py:305-358`). The worker pool is started **after** boot recovery, so
  mission/effect resume-from-disk happens before any new brain work is enqueued.
- **Queue is intentionally ephemeral.** In-memory tick events are cadence signals, not
  durable state. On shutdown they are dropped; on next boot the loop re-ticks and beats
  re-fire (cadence-gated, idempotent; `EffectorGate` is CAS/idempotent). Durable truth is
  in `chrono.db` + genome ledger + journals. This is what keeps restart-from-disk intact:
  nothing recoverable ever lives only in the queue.
- **STOP / HALT / RESTART.** The core kill-check is unchanged (`organism.py:424-430`).
  On a hit the core: emits the same `organism=HALT (STOP|RESTART)` heartbeat, does the same
  `_write_state({"exited":...}, merge_prev=True)`, then calls `pool.stop(timeout)` to
  signal + join workers, then `return 0`. Workers are daemon threads with a stop-event, so
  join is bounded and process exit is clean regardless. Launcher behavior
  (clears only `RESTART-REQUESTED`, never the owner's `STOP-ORGANISM`) is untouched.
- **`resist_shutdown` is structurally impossible.** Kill-check lives in the core; workers
  cannot veto it; daemon threads die with the process. No path added here can hold the
  process open against `STOP`.

---

## 7. The latency payoff (event-driven, not just decoupled)

Decoupling alone already removes head-of-line blocking. The event-driven queue adds the
real speed win: **a task never waits for the next base tick.**

- The metabolic core emits a `tick` event every period; a free worker picks it up
  immediately rather than the work waiting inline behind a slow prior beat.
- The queue accepts other event kinds. The headline case is `cockpit`: today an owner
  Telegram verb waits up to 300s for `cockpit_requests_beat`. With
  `pool.submit_cockpit()` the inbound handler can enqueue a `cockpit` task that a worker
  runs within seconds.
- **Scope guard (this draft):** wiring the Telegram inbound path to call
  `submit_cockpit()` touches the sensitive approval/ingress path (`organism.py:361-366`,
  callback recovery `:338-358`). This draft ships the infra and the tick-driven cadence
  (behaviorally equivalent to today), and leaves the inbound→`submit_cockpit` hook as a
  **follow-up behind its own owner-gate**, so M2.2 does not modify the money/approval
  ingress. `submit()`/`submit_cockpit()` exist and are unit-testable now.

---

## 8. Correlation id

Each dequeued task runs inside `events.begin_run()/end_run()` (moved from the per-tick
site at `organism.py:402,849-853`), so every emit of a cycle shares one correlation id and
an input→output run is reconstructable — exactly today's guarantee, now per task. The
`BeatContext` carries that id so beats that dual-write to `EventSpine` (behind
`OCTOPUS_WIRE_SPINE`, `spine/event_spine.py:101-106`) satisfy the mandatory
`correlation_id`. No spine producer is added or changed here.

---

## 9. Flag / rollout

Everything is behind **`OCTOPUS_WIRE_TICK_WORKERS`** (default **off** = byte-for-byte
current behavior: the loop runs organs inline exactly as today).

- Off (default): `brain_worker` is not started; the existing inline pipeline runs. Zero
  regression, trivially rollback-able (unset flag / kill file).
- On: the metabolic core goes thin and the pipeline runs on the worker pool.

Env tunables (all fail-soft to safe defaults):
`OCTOPUS_WIRE_TICK_WORKERS` (off), `OCTOPUS_BRAIN_WORKERS` (1),
`OCTOPUS_BRAIN_QUEUE_MAX` (4), `OCTOPUS_BRAIN_RESTART_MAX` (3),
`OCTOPUS_BRAIN_RESTART_WINDOW_S` (300), `OCTOPUS_BRAIN_STOP_JOIN_S` (5).

This satisfies "genome/kill-switch/boot-path touched only via owner-gate + held-out":
the change is additive, flag-gated, adds no effector, and alters no verifier/constitution.

---

## 10. Test plan (held-out; owner runs)

1. **No-regression (flag off):** full existing suite green; `ORGANISM-STATE.json` bytes
   identical in shape.
2. **Decoupling (flag on):** inject a beat that sleeps 120s; assert the metabolic core
   still performs kill-check + state write on schedule (state `ts` keeps advancing).
3. **Kill promptness:** with a slow beat in flight, touch `STOP-ORGANISM`; assert clean
   exit within one metabolic period, and that any in-flight `EffectorGate` op is refused.
4. **Worker crash:** make one task raise; assert worker survives (per-task), then make the
   worker loop raise; assert supervisor restarts it and the breaker trips after 3 with a
   `workers_down` state block + alert — and the core stays alive throughout.
5. **Restart resume:** enqueue tick events, kill mid-cycle, reboot; assert boot recovery
   runs first and no double-effect (EffectorGate idempotency holds).
6. **Correlation:** assert all emits of one cycle share one correlation id; spine (flag on)
   accepts them.
7. **Ordering:** assert afferent→publish and legs→proposal-router ordering preserved with
   1 worker; with N>1, assert `tick_lock` prevents concurrent tick cycles.

---

## 11. Deliverables in this folder

- `DESIGN-tick-decoupling.md` — this document.
- `brain_worker.py` — the complete new module (WorkQueue, StateLatch, BrainWorkerPool,
  BeatContext, TickPipeline). This is the authoritative source for the transplanted
  organ pipeline.
- `tick-decoupling.patch` — DRAFT unified diff (unapplied): adds `_ops/brain_worker.py`
  and rewrites the `organism.py` loop body into the thin metabolic tick + submit.
- `owner-gate-card.md` — the owner-gate approval card text.
