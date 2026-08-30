# C7 INDEPENDENT REVIEW — MERGE BLOCKERS

Date: 2026-07-23 · Branch: `claude/c7-continuity` @ `efa0412` · master: `a1c3ff6`

## VERDICT: BLOCKED — DO NOT MERGE YET

The 274/274 suite is useful, but several tests validate the wrong semantics. C7 contains real progress, yet its strongest continuity and parity claims are not currently true.

## Repository-state warning

`F:\backup\.git\HEAD` currently points to `refs/heads/claude/c7-continuity`.
Therefore the live working directory itself is checked out on the candidate branch. The master ref is untouched, but this is not an isolated worktree. Keep `STOP-METABOLIC` and all external flags disarmed. Do not switch branches while a process is running from this tree.

## B1 — Money-card dedup recreates the original amnesia

Evidence:
- `_dedup_marker()` permanently records `money|effect_id|status`.
- first boot reconstructs `_pending` in RAM and writes the marker;
- second boot sees the marker and does not reconstruct `_pending`;
- `_pending` is a fresh empty dict after restart.
- test `t_double_boot_no_dup` explicitly expects the second boot to rebuild **zero** cards, thereby validating loss rather than continuity.

Required semantics:
- every fresh process must reconstruct pending projection in RAM;
- anti-spam controls Telegram delivery, not projection reconstruction;
- a delivery lease/marker must include status/version and a resend policy, but may never prevent local reconstruction.

## B2 — Rebuilt money card has no buttons

Evidence:
- `rebuild_money_cards()` calls `channel.send_text(text)` without `reply_markup`.
- it inserts `_pending` metadata, but owner receives no approve/deny/later callback controls.

Required:
- use one canonical card renderer/sender shared with `request_approval_card`, accepting a prebuilt exact binding and token;
- send a real actionable card;
- persist delivery acknowledgment only after send succeeds.

## B3 — Valid pre-restart money token is not necessarily invalidated

Evidence:
- `mint_money_token` is deterministic for the same effect binding and expiry.
- no boot nonce/card generation is present.
- test `t_old_token_replay_rejected` tests an already-expired token only; it does not test a still-valid token minted before restart.

Required:
- either make tokens intentionally stateless and allow still-valid pre-restart tokens with durable single-use approval ID, or include durable card generation/nonce and reject old generations;
- document one model and test it honestly;
- never claim “fresh token invalidates old token” while deterministic token remains identical.

## B4 — HALT can permanently suppress delivery

Evidence:
- under HALT, reconstruction writes the permanent dedup marker but does not send;
- later boot/unhalt sees marker and skips reconstruction/delivery.

Required:
- HALT may suppress send/action but must not mark delivery complete;
- pending projection must remain visible locally;
- after safe resume, one actionable card may be sent.

## B5 — Marker is committed before delivery succeeds

Evidence:
- `_dedup_marker` writes before `send_text`;
- `send_text` result is ignored;
- a failed Telegram send can permanently suppress retries.

Required:
- reserve → send → ack/commit delivery marker;
- failed send remains retryable with bounded backoff;
- boot concurrency needs atomic lease/lock.

## B6 — Amount reconstruction may not match production payload semantics

Evidence:
- code assumes `payload_ref` itself is JSON containing `amount_aud`;
- test fixture encodes JSON directly in `payload_ref`;
- production contract names this field a reference, so exact live representation must be verified.

Required:
- use the authoritative gated-effect binding/amount accessor, not ad-hoc JSON parsing;
- fail closed if exact amount cannot be reconstructed;
- never mint an approval card at fabricated `0.0`.

## B7 — RFC durable exactly-once is not wired into dispatch

Evidence:
- `persist_rfc_verdict()` exists in `pending_card_recovery.py`;
- inspected `_dispatch_rfc()` only mutates `_pending_rfc` RAM status;
- `pop_rfc_verdicts()` marks `consumed` in RAM;
- no durable call is visible in the production verdict path.

Required:
- persist verdict atomically before acknowledging callback;
- rebuild excludes durable decided entries;
- doctor consumption has a durable consumed state or idempotent receipt;
- restart after click-before-consume and consume-before-crash must not duplicate or lose verdict.

## B8 — Research recovery detects the wrong journal but computes resume from run journal

Evidence:
- research incomplete rows are appended to `inc`;
- the resume loop calls `dj.resume_point(..., path=jpath)` for every row;
- `jpath` is `run-journal.jsonl`, not `research-journal.jsonl` for research rows.

Required:
- preserve source path/lane per incomplete run;
- compute resume point from its own journal;
- return contract ID, step, experiment index, budget spent and rewrite count;
- current code detects only; it does not resume a real C6 state machine.

## B9 — C6 acceptance failure can leave admitted memory behind

Evidence:
- C6 admits memory before `ledger.append_strict(e)`;
- if final research-ledger append fails, verdict becomes quarantined but the memory and receipt already exist as admitted artifacts;
- no compensating retraction occurs in this branch.

Required:
- final admission requires durable ledger commit too;
- use pending-admission/outbox state or retract memory on final ledger failure;
- test ledger failure and restart between each artifact boundary.

## B10 — C6 recovery/acceptance test coverage is below the claimed contract

Evidence:
- `test_research_loop.py` contains one added `verified-not-admitted` test;
- no observed tests for receipt failure, outcome failure, ledger append failure, crash after experiment, crash after outcome, or duplicate resume;
- current test list is 10 scenarios, not the full required battery.

## B11 — BrainCore parity is not wired

Evidence:
- `ParityTracker` is defined but `build_shadow_scheduler()` does not instantiate or call it;
- adapters return snapshots but no old/new output pair is supplied to `compare()`;
- production `organism.py` calls only `_beat_sched.tick()`;
- therefore a 24h run cannot produce meaningful parity counters.

Required:
- define explicit old-output and shadow-output for each migrated organ;
- shared input snapshot and correlation ID;
- invoke parity comparison in production shadow path;
- distinguish missing input from mismatch;
- prevent `PARITY-GREEN` unless continuous elapsed soak >=24h, enough samples, zero critical mismatch, and no reset/restart gap outside policy.

## B12 — `PARITY-GREEN` is sample-count based, not 24-hour based

Evidence:
- status becomes green at `compared >= 100`, mismatched=0 and missing_new=0;
- no soak start/end time or continuous duration check.

At a 5-minute loop, 100 comparisons can occur well before 24 hours.

## B13 — BrainCore status is not exposed in organism state/API

Evidence:
- scheduler tick result/status is ignored;
- `_write_state()` does not include brain-core status/parity counters;
- “truthful status API” claim is not demonstrated in production.

Required:
- add `brain_core: {mode, beat, degraded, parity, started_at, age}` to ORGANISM-STATE;
- UI must label flag-off as HARNESS, flag-on before soak as SHADOW-LIVE, and only true 24h gate as PARITY-GREEN.

## B14 — Beat reserve/commit is still incomplete

Progress: reserve is fsync'd before phases and commit phases are blocked if reserve fails.

Residual problem:
- reserve writes the new beat as if complete before phase execution;
- crash mid-beat causes restart at beat+1 with no durable `RESERVED/RUNNING/COMMITTED` distinction;
- final `_persist` result is ignored;
- outcome of phase execution can be lost.

Required:
- durable phase/status state (`RESERVED`, `RUNNING`, `COMMITTED`, `DEGRADED`);
- on boot, incomplete reserved beat becomes reconcile/recovery, not silently “completed”;
- no ACT/LEARN until committed identity and operation-level idempotency exist.

## What is good and should be preserved

- canonical C3 receipt store is now wired;
- no-receipt learning is rejected and compensating retraction exists;
- C6 no longer accepts when memory/receipt are absent;
- strict fsync research ledger helper is useful;
- real BrainCore composition root exists with no ACT organ;
- spine soak logic was correctly separated from env-clean adapter;
- STOP-METABOLIC and external disarm remained intact.

## Required verdict after repair

Do not say DONE until:
- focused C7.1 tests pass;
- authoritative full suite passes;
- independent read-only red team checks the repaired semantics;
- branch remains flags OFF;
- a merge packet contains exact diff/commits/rollback;
- live working-tree branch state is handled safely.

---

# C7.1 — REPAIR RESOLUTION (appended; original audit above unchanged)

Date: 2026-07-23 · Branch: `claude/c7-continuity` (C7.1 repair commits on top of `efa0412`).
Every blocker was **reproduced against real code first**, then fixed. Focused tests below all pass;
regression-isolated in a clean worktree (see "Regression isolation" note at end).

## Money-card resurrection (B1-B7) — `pending_card_recovery.py` rewrite + `approval_channel` wiring

Root change: a **durable pending-card store** (`state/pulse/pending-cards.json`) is written at card-creation
by `TelegramApprovalChannel.request_approval_card`/`rfc_card` (real amount + binding + callback token +
integrity tag). Rebuild reads the store, **cross-checks chrono** (only pending/releasable), and separates
**projection reconstruction** (always) from **delivery** (state machine + lease).

- **B1 (dedup recreated amnesia) — RESOLVED.** `_dedup_marker` deleted. Projection is reconstructed on
  *every* boot from the durable store (no gate). Delivery dedup is a separate `delivery` state
  (PENDING -> LEASED -> SENT). Test `t_projection_every_boot_with_buttons` proves boot1 AND boot2 both hold
  the `_pending` projection (the old false-green `t_double_boot_no_dup` that validated loss is deleted).
- **B2 (no buttons) — RESOLVED.** Rebuild sends via the **canonical** `reissue_approval_card` (shared with
  first-send), emitting the real approve/deny/later `inline_keyboard`. Test asserts the 3 callback verbs.
- **B3 (token model) — RESOLVED (Model B, stated).** Token is persisted at creation and **restored
  identically** on rebuild -> the owner's pre-restart button still works. Anti-replay is the money layer's
  existing single-use `approval_id` (`chrono.release_effect` has `NOT EXISTS(... approval_id)`). We no longer
  claim "restart invalidates the token". Test `t_model_b_pre_restart_token_still_valid`.
- **B4 (HALT burns delivery) — RESOLVED.** Under `halted`, rebuild reconstructs projection then continues
  before any send/lease/mark; delivery stays PENDING; after resume it sends. Test
  `t_halt_reconstructs_but_never_sends_then_resume`.
- **B5 (marker before send) — RESOLVED.** Order is lease -> send -> mark SENT only on success; failed send
  reverts to PENDING (retryable). Test `t_failed_send_retried_next_boot`.
- **B6 (fabricated amount) — RESOLVED.** Amount comes from the durable record captured at creation (chrono
  has **no** amount column — confirmed). Unknown amount or integrity-tamper => **fail-closed, no card**. Test
  `t_unknown_amount_and_tamper_fail_closed`. **Note:** without `OCTOPUS_CB_SECRET` the integrity tag cannot
  be minted/verified => money-card rebuild is fail-closed (inert but safe); RFC recovery needs no secret.
- **B7 (RFC exactly-once not wired) — RESOLVED.** `_dispatch_rfc` persists the verdict durably **before**
  the callback ack; `pop_rfc_verdicts` writes a durable **consumed** marker; rebuild re-injects unconsumed
  durable verdicts so doctor still receives them exactly once. Tests
  `t_rfc_verdict_survives_crash_before_consume`, `t_rfc_consume_then_crash_no_duplicate`.
- Atomic concurrent-boot send lease (O_EXCL): `t_concurrent_send_lease`.
- **Money authorization semantics untouched:** `chrono.py` has **0** diff (branch and working tree). Release
  still only via `EffectorGate.release_effect`. `test_telegram_rfc_router` SACRED app:* flow still green.

## Research recovery (B8) + C6 atomicity (B9, B10) — `research_loop.py`, `journal_recovery.py`

- **B8 (resume read wrong journal) — RESOLVED.** `journal_recovery.boot_recovery` now tags each incomplete
  row with its lane/path and computes `resume_point` from **that lane's own journal**; research rows resolve
  against `research-journal.jsonl`. New `research_loop.plan_recovery` returns a structured **DETECTED** plan
  (contract_id, last_completed_step, experiment_index, rewrite_count, budget_spent). Tests
  `t_resume_point_from_research_journal_not_run_journal`, `t_plan_recovery_from_research_journal`.
- **B9 (accepted-then-orphaned memory) — RESOLVED.** If the final `ledger.append_strict` for an accepted
  entry fails, the admitted memory is **retracted** via `learning_gate.rollback_learning` (supersede ->
  invalidate) and the verdict becomes `quarantined`. No accepted memory survives without its durable ledger
  row. Test `t_final_ledger_failure_retracts_memory`.
- **B10 (thin coverage) — RESOLVED.** Added receipt-failure, outcome-failure, final-ledger-failure, and
  idempotent-resume (no duplicate artifacts) tests. Receipt/outcome failure => `verified-not-admitted`
  (never accepted). Idempotency guard `ResearchLedger.find_completed(experiment_key)` prevents re-running a
  completed experiment / duplicating artifacts. Tests `t_receipt_failure_not_accepted`,
  `t_outcome_failure_not_accepted`, `t_completed_experiment_not_rerun`.

## Real parity (B11-B13) — `brain_core.py` rewrite + `organism.py` state exposure

- **B11 (ParityTracker never called) — RESOLVED.** `build_shadow_scheduler` instantiates a `ParityTracker`
  and the SENSE/RECORD organs call `parity.compare(legacy, shadow)` **inside the tick path** with two
  independent sources (SENSE: raw-signal-derived alive vs recorded heartstate; RECORD: `spine.db` count vs
  `events.jsonl` count). THINK/HEAL stay advisory-only (cortex/doctor are **not** re-run -> no self-comparison,
  no second paid loop). missing_old/missing_new are counted distinctly. Test `t_parity_compare_called_in_tick`.
- **B12 (green on sample count) — RESOLVED.** `PARITY-GREEN` now requires continuous soak >= 24 h **plus**
  >= 100 matched, zero mismatch, zero critical mismatch, zero missing_new, and >= per-organ minimum; a restart
  gap > 1 h resets `started_at`. Soak telemetry (started_at/last_sample_at/continuous_elapsed_s/restart_gaps/
  per_organ) is persisted. Tests: `t_under_24h_never_green` (150 matches, still SHADOW-LIVE),
  `t_24h_continuous_green`, `t_critical_mismatch_blocks_green`, `t_restart_gap_breaks_continuity`.
- **B13 (status not exposed) — RESOLVED.** `brain_core.organism_state_block` (mode/flag_on/beat/degraded/
  parity) is written into `ORGANISM-STATE.json` from the main loop each shadow tick. Test
  `t_state_block_exposed`. Zero ACT organ + both flags OFF default preserved.

## Beat state machine (B14) — `beat_scheduler.py`

- **B14 (reserve written as complete; final persist ignored) — RESOLVED.** Explicit lifecycle
  RESERVED/COMMITTED/DEGRADED. `committed_counter` (monotonic) advances **only** on a durable COMMIT; the
  final commit persist result is **checked** (failure => degraded, counter unchanged). On boot, a
  RESERVED-but-not-COMMITTED beat is surfaced via `recovery_state()` as reconcile — never treated as
  complete; a committed beat is never re-run (no double ACT/LEARN). Tests
  `t_crash_after_reserve_reconcile`, `t_final_commit_persist_failure_checked`,
  `t_committed_beat_not_rerun_after_restart`, `t_committed_advances_exactly_once`.

## Regression isolation (important)

Running the full suite against the **live F:\backup working tree** shows a few non-C7.1 failures
(`test_leg_chain_wire`, `test_phase1_envelope`, `test_ziman_*`, `test_cartographer_wiring`). These are
**environmental, not caused by C7.1**: `leg_chain_wire`/`phase1_envelope` flip because of an **untracked**
live activation file (`_ops/ACTIVATION-HEARTSTATE.flag`) that turns a "flag-off => None" no-op non-None;
`ziman_*`/`cartographer` fail identically on the **pure efa0412 baseline** with no C7.1 code. Proven by
copying the 11 changed files into a clean efa0412 worktree (no untracked runtime files): there
`leg_chain_wire` and `phase1_envelope` pass 8/8 and 9/9, and only the pre-existing `ziman_*`/`cartographer`
remain red — identical to the untouched baseline.

## Owner-only items unchanged by C7.1
`STOP-METABOLIC` untouched; `OCTOPUS_ONE_HEARTBEAT` + `OCTOPUS_SPINE_VIA_ADAPTER` remain OFF; six
external-effect flags remain disarmed; no money/network/apply/merge. C5 not LIVE (needs the real 24 h
soak — the parity gate now enforces it); C6 not LIVE (no real research mission run).
