# OWNER-GATE CARD — M2.2 Tick Decoupling

**Mission:** M2.2 (speed) — split the single always-on organism loop into a thin
metabolic tick + event-driven brain workers, so a task never waits up to 300s for the
next base tick and a slow/crashed organ can no longer delay the kill-check.

**Change class:** additive, flag-gated, PROPOSE-ONLY until you approve. No new effector,
no verifier/constitution edit, no boot-path or genome change. Kill stays supreme.

---

## What you are approving

1. **New file** `_ops/brain_worker.py` (the pool + the transplanted organ pipeline).
2. **Rewrite of the `organism.py` main-loop body** into a thin metabolic core that runs
   the organ pipeline either inline (flag off) or on a worker pool (flag on).
3. **New flag** `OCTOPUS_WIRE_TICK_WORKERS` (**default off**). Off = byte-for-byte
   today's behavior (same thread, same order, same effects — pure extract-method).

### What STAYS on the metabolic thread (thin tick)
Kill-check (STOP-ORGANISM / master_halted / RESTART-REQUESTED) · telemetry
snapshot+reconcile · germline staleness · chrono status read · the single
`ORGANISM-STATE.json` write · hourly heartbeat · cardiac/heart sleep-period logic.

### What MOVES to workers (event-driven)
Every productive organ beat: neural+protective, epoch, daily fitness/replication/
ledger-verify, doctor, consolidation, cockpit/tg-exec, afferent, publish, legs (lead/
ziman/cartographer), proposal router, business/asset/acct/email/harvest/lead-discovery/
cultivation, scheduler-seed, idea, epistemics, heart, all nudges/digests.

---

## Safety properties (why this is safe to arm)

- **Worker crash ≠ core death.** Three isolation layers: per-organ try/except (unchanged),
  per-task try/except, and a per-thread supervisor with a ≤3-restarts/300s circuit-breaker
  (mirrors the existing chrono self-heal breaker). If all workers die, the core keeps
  running kill-check + telemetry + state + heartbeat and surfaces `workers_down` in state.
- **Kill stays prompt & supreme.** Kill-check is synchronous on the core thread and can no
  longer be delayed by a slow organ. `resist_shutdown` is structurally impossible (workers
  are daemon threads, joined on stop; they cannot veto exit). `EffectorGate.force_closed()`
  still re-checks STOP/HALT/FREEZE on every release/settle/execute.
- **Core never blocks.** The queue is bounded; the producer uses `put_nowait` and
  coalesces/drops an overflow tick (harmless — beats are cadence-gated + idempotent).
- **Restart-from-disk preserved.** Boot recovery (journal / birth-certificate /
  pending-card) still runs first, before the pool starts. The queue is intentionally
  ephemeral; all durable truth stays in chrono.db + genome ledger + journals.
- **Single-writer state.** Workers only write in-memory blocks to a locked latch; the core
  does the one LockedJson disk write, keeping the "freeze last-known block while ts
  advances" semantics.

---

## The ONE reviewable behavior change (flag ON)

State reflects the **last-completed** brain cycle, not the in-flight one (ts still advances
every metabolic tick). This is the intended decoupling. With `OCTOPUS_BRAIN_WORKERS=1`
(default) the effect is a one-tick lag on organ blocks in `ORGANISM-STATE.json`; kill,
telemetry, and heartbeat are always current. Flag OFF has zero lag (inline).

---

## Held-out verification to run before arming live (owner)

1. Flag OFF: full suite green; state shape unchanged.
2. Flag ON: inject a 120s beat → assert core kill-check + state write keep their cadence.
3. Touch `STOP-ORGANISM` mid-slow-beat → clean exit within one period; in-flight
   EffectorGate op refused.
4. Force a task raise, then a worker-loop raise → worker survives / supervisor restarts /
   breaker trips at 3 with `workers_down` + alert; core alive throughout.
5. Kill mid-cycle, reboot → boot recovery first, no double-effect (idempotency holds).
6. Correlation: all emits of one cycle share one id.

## Rollback

Set `OCTOPUS_WIRE_TICK_WORKERS=0` (or unset) → instant return to inline single-thread
behavior, no restart-of-logic required beyond the normal RESTART-REQUESTED cycle. The new
file is inert when the flag is off. No migration, no schema change, nothing to undo on disk.

## Arming (owner-only; not done here)
Add `OCTOPUS_WIRE_TICK_WORKERS=1` to the untracked `_ops/OCTOPUS-flags.cmd` after the
held-out tests pass. This card does not arm anything.
