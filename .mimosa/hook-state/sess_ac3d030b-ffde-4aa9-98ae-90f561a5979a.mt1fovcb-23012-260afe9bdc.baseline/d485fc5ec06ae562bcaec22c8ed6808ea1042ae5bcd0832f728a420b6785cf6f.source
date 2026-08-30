# C2 — RESURRECTION-SAFE MEMORY — REPORT (2026-07-23)

> North star: بعد از هر خواب، با تمام خاطرات و هویتِ قبلی بیدار شود.
> Base: Phase-0 merge `869a186` + C1 window-A green. Executor: sole shell writer.

## A. RAM-only ledger (BEFORE → AFTER)

Audit method: full sweep of Brain Core (live_loop, telegram_center, approval_channel,
wiring, organism, cortex, doctor/, mission_runner, durable_journal, outbound_worker)
by read-only agent + manual verification. Classification per C2 rule A.

| # | state | loc | class BEFORE | AFTER (this session) |
|---|---|---|---|---|
| A1 | `_proposal_cb` (token→meta) | live_loop.py | **BUG** — approval/callback identity RAM-only; restart = dead buttons | **FIXED (C2-B)**: stateless pb1 HMAC token + durable delivered-registry (outcomes.db); RAM demoted to fast-path cache |
| A2 | deferral tracking (undecided entries of A1) | live_loop.py | **BUG** — deferred cards vanish on restart | **FIXED (C2-C)**: rebuild-on-boot from outcomes.db; durable cross-boot dedupe |
| A3 | `_pending` (money/effect approval cards) | budget/approval_channel.py:230 | **BUG** — in-flight money-approval cards die on restart | **OPEN — LEDGERED**: money-surface change; one-money-slice/session rule. Proposed fix: rebuild-on-boot from chrono gated_effect (pending) + fresh HMAC cards. → C2.1 candidate |
| A4 | `_pending_rfc` (RFC verdict cards) | budget/approval_channel.py:231 | **BUG** — RFC cards die on restart (RFC records themselves durable in rfcs.json) | **OPEN — LEDGERED**: reconstructable from rfcs.json (status=submitted) + re-serve. → C2.1 candidate |
| A5 | `durable_journal` (resume primitive) | durable_journal.py | **ORPHAN** — zero callers | **FIXED (C2-D)**: doctor journals propose/sandbox/submit; boot recovery consumes it |
| A6 | `_proposal_seen` (dedupe set) | live_loop.py | reconstructable-projection | unchanged (legs re-propose; delivered-registry now also durable) |
| A7 | `_proposal_outcomes` (metrics buffer) | live_loop.py | expendable-cache (durable copy in outcomes.db when flag on) | unchanged |
| A8 | `_verdicts` (Ari verdict list) | live_loop.py | reconstructable (brain archive durable) | unchanged |
| A9 | `_advisory_signals` | live_loop.py | expendable-cache | unchanged |
| A10 | telegram offsets/seen/approvals | center.py + approval_store.py + approval_channel `_offset` | durable-truth-already (files) | unchanged |
| A11 | `_EPOCH_STATE` cadence gate | wiring.py:40 | expendable-cache (self-declared, ≤1 re-fire) | unchanged |
| A12 | organism loop scalars, cortex `_obs_last_alert`, doctor `_running` | various | expendable-cache | unchanged |
| A13 | mission_runner state | files (run.json atomic) | durable-truth-already | unchanged |

**Invariant check (rule A):** identity/approval/effect/learning state that remains RAM-only: A3+A4 only — both ledgered as explicit OPEN bugs with reconstruction paths (their durable truths exist: chrono.gated_effect + rfcs.json; only the card/token projections are RAM). Nothing else BUG-class remains.

## B. Callback continuity (GAP-2) — DONE @ `adccf9d`
- Token `pb1.<pid12>.<exp10>.<sig16>` = 44 chars; `prop:later:` + token = 55B ≤ 64B Telegram cap.
- Binding: full proposal_id + expiry + **owner** inside HMAC canon (`pb1|pid|exp|owner`); action/verdict deliberately NOT in token (comes from button; unforgeable without secret). Version = pb1. Nonce-equivalent: single-use enforced by durable idempotency in outcomes.db (stronger than token nonce; spec rule 2).
- Rehydration: durable delivered-registry (event_type=delivered, idem `deliv|pid`) → full meta after restart; fail-closed: bad-format / wrong-pid / expired (honest sentinel) / bad-sig (covers forged + wrong-owner) / unknown-card / already-decided.
- No secret → mint falls back to legacy RAM token + one-time `CB_TOKEN_DEGRADED` advisory; never crash (spec rule 4). **OCTOPUS_CB_SECRET is absent in live .env → live runs degraded-RAM until owner creates it (owner action; module never creates secrets).**
- Tests: 8/8 (`test_stateless_cb_restart.py`), incl. restart-survival, forged/expired/replay/wrong-owner/wrong-verb, ≤64B, defer→restart→decide, registry idempotency.

## C. Deferral recovery (GAP-3) — DONE @ `636d97f`
- SoT: outcomes.db deferred events minus decided minus expired (TTL env `OCTOPUS_DEFER_TTL_S`, default 7d).
- Boot hook: `wire_proposal_buttons` (organism boot) → `deferral_rebuild.rebuild_deferred_cards`; ≤3 full cards, >3 one digest with per-proposal button rows; durable cross-boot dedupe marker `deliv-rebuild|pid|n_deferrals` (new deferral ⇒ one more rebuild allowed).
- Decided/expired never reappear; DB absent → silent skip; UI is projection, never truth.
- Flag note: spec's parenthetical said (PROPOSAL_BUTTONS + WIRE_SPINE); actual data source is outcomes.db ⇒ gated on PROPOSAL_BUTTONS (caller) + VERDICT_OUTCOME (registry module) — recorded as decision D-O1, code-reality wins, no new flag.
- Tests: 6/6 (`test_deferral_rebuild_boot.py`).

## D. Mission/journal recovery — DONE @ `25db21e`
- Doctor journals its 3 steps (propose→sandbox→submit) to `state/journal/run-journal.jsonl` (D-A honored; orphan cured).
- `journal_recovery.boot_recovery()` @ organism boot: (1) `incomplete_runs` scan — **advisory, resume_point exposed, never blind re-run**; (2) first-ever caller of C6 `sweep_stale_executions`: abandoned EXECUTING → **RECONCILE_REQUIRED** (honest — external effect may have happened), never fake terminal, never re-execution. Knob `OCTOPUS_BOOT_RECONCILE_EXEC_H` (default 6h; 0=off, C6 idiom).
- `durable_journal.record` now mkdirs explicit paths (additive fix to the orphan).
- Tests: 5/5 (`test_journal_recovery.py`).

## E. Birth certificate — DONE @ `9fbd95b`
- `system.booted` → spine (domain=system, producer=organism-boot, trust=DETERMINISTIC), payload per Resurrection Protocol: boot_id / prev_boot_id chain / booted_at / uptime_gap_s / halt_state / flags_hash / state_checksums (spine, outcomes, memory, chrono incl. user_version, ledger count+last-line sha12) / recovery extras (journal_incomplete, chrono_reconciled).
- `flags_hash` = sha256(flags.cmd bytes + sorted .env KEY NAMES) — **no .env value is ever read**; test 3 proves value-change ⇒ hash unchanged, key-rename ⇒ hash changed, zero values in payload.
- taxonomy `EVENT_TYPES` += `system.booted` (additive; outcome_store's own narrow tuple untouched).
- Tests: 6/6 (`test_boot_certificate.py`).

## F. Restart battery — DONE
- Composite E2E (`test_restart_battery.py`): deliver 2 → verdict #1 → defer #2 → RESTART → only #2 rebuilt → decided via rebuilt token → replay blocked → HALT file persists & cert reports armed → birth chain continuous → abandoned EXECUTING reconciled → corrupted RAM cache with intact SoT harmless. All 9 mission-F scenarios mapped. PASS.
- **Full sandbox suite: 268/268 PASS** in isolated repo (263 baseline + 5 C2 suites), 0 attempted live-writes, 0 external-network, 0 barrier-install-failures, 280 child-evidence. (Re-verified after red-team fixes.)
- **Read-only red team (14-angle adversarial): no P0/P1.** All safety-claim attacks refuted with evidence (forgery, replay, expiry, wrong-owner stateless path, registry poisoning, secret hygiene, cert .env exposure, message-storm). 4×P2 found and **all fixed** @ `28826bb`:
  - **F1** owner binding was enforced only on the rehydrate path, not the warm-RAM path → moved enforcement to the **channel layer** (`_dispatch_proposal` owner-gates the `prop:` scheme, GOV-P1 pattern) — a non-owner in an allowlisted group can no longer forge an owner verdict.
  - **F2** dead `n_deferrals` dedupe branch → per-pid marker + honest comment.
  - **F3** TypeError-retry double-invoked the hook → arity inspection, call once.
  - **F4** env-owner whitespace could lock the real owner out → normalize (strip) in token canon.
  - +2 tests (channel owner-gate, env-whitespace). Refuted-only, note-level: F5 (48-bit pid12 collision — availability only, ~2^24 bound, impractical).

## G. Safety
- All changes additive + fail-soft; zero schema migration (only additive taxonomy vocab). Rollback = revert the 4 slice commits (`adccf9d`, `636d97f`, `25db21e`, `9fbd95b`) individually or together; no data migration to undo. DB/WAL backups from deploy window remain valid (`chrono.db.pre-v4`, full snapshot).
- External-effect lanes remain DISARMED (6 flags =0). No secret read/printed/committed.

## D8/D12 delta (evidence-based claim)
- **D12 continuity: 4 → 7.** Evidence: verdict+deferral+card-interpretation all survive restart (battery); journal-visible mid-step death; in-flight → RECONCILE (no double effect); boot lineage chain. Remaining gap to 9-10: A3/A4 money/RFC cards + tg-center auto-restart (GAP-6, unaddressed).
- **D8 learning: 2 → 3.** C2 gives learning its restart-safe substrate (verdict measurements now uninterruptible); actual compounding (memory gate + eval harness) is C3's mandate.

## Owner items (non-blocking)
1. Create `OCTOPUS_CB_SECRET` in `.env` (any strong random; owner-only) → arms stateless tokens live. Until then: degraded-RAM mode (honest advisory logged).
2. A3/A4 (money/RFC pending-card persistence) queued as C2.1 — money-surface; wants its own focused slice.
