# INDEPENDENT POST-C6 AUDIT — واقعیت بعد از گزارش ایجنت

Date: 2026-07-23 · Auditor: independent read-only architecture pass · Root: `F:\backup`

## حکم کوتاه

Phase-0 و C1–C4 دارای کد و wiring واقعی‌اند؛ C2 عمداً دو زخم continuity باز دارد؛ C5 فقط یک موتور scheduler آزمایشگاهی است و هنوز به organهای واقعی `organism.py` وصل نشده؛ C6 یک harness تستی proposal-only است، نه یک research service قابل‌اجرای production. بنابراین عبارت «all landed» در سطح **کد موجود** عمدتاً درست، ولی در سطح **ارگانیسم یکپارچه و زنده** نادرست/زودرس است.

Live truth اکنون:

- `STOP-METABOLIC` موجود: billed AU$0.06 در برابر telemetry AU$0.00.
- `ORGANISM-STATE.json`: `halted=STOP-METABOLIC`, `frozen=true`.
- C1 flags ON: verdict outcome + spine.
- C3 flags ON: memory gate + lead outcome.
- External effect flags remain disarmed.
- One-heartbeat has no live state file and no production registration evidence.

## Verdict by mission

| Mission | Code exists | Production wiring | Live proof | Independent verdict |
|---|---:|---:|---:|---|
| Phase-0 | yes | yes | deploy log + chrono v4 state | KEEP, test result itself not rerun by this auditor |
| C1 circulation | yes | yes (`verdict_recorder`, flags ON) | outcomes/spine DBs exist | REAL, but live Telegram human E2E was not exercised in C1 report |
| C2 resurrection | yes | partial | restart battery is synthetic | PARTIAL: proposal callback/deferral done; money/RFC cards remain RAM-only |
| C3 learning | yes | yes on owner-accept path | memory/receipt DBs exist | REAL substrate; content-quality learning remains unmeasured |
| C4 one spine | yes | partial | adapter parity test exists | STAGED: compat flag still not activated/soaked; multiple event projections remain by design |
| C5 heartbeat | yes | **no real organ registration** | no beat-state artifact found | HARNESS ONLY, not a living one-heartbeat migration |
| C6 research | yes | **no production entrypoint** | no C6 research ledger/mission evidence found | HARNESS ONLY; restart semantics and acceptance invariants need hardening |

## Confirmed incomplete Brain-Core organs

### S1 — C5 scheduler is not connected to the body

Evidence:
- `_ops/beat_scheduler.py` exists.
- `_ops/tests/test_beat_scheduler.py` registers only mock handlers.
- `organism.py` has no production `BeatScheduler` initialization/registration/tick path in the inspected source.
- `OCTOPUS-flags.cmd` contains neither `OCTOPUS_ONE_HEARTBEAT` nor ACT_ARMED.
- no `state/pulse/beat-state.json` found.

Required fix:
1. add a production composition root, preferably `_ops/brain_core.py` or a small factory in `wiring.py`;
2. register **read-only adapters first**: health/perception, cortex advisory, doctor advisory;
3. run scheduler in shadow with legacy loops authoritative;
4. record comparable old/new outputs with shared correlation ID;
5. 24h parity before any legacy loop retirement;
6. ACT remains unregistered or hard dry-run.

### S1 — pending money approval and RFC cards die on restart

Evidence:
- `approval_channel.py` initializes `_pending={}` and `_pending_rfc={}` in RAM.
- C2 report explicitly lists A3/A4 OPEN.
- money truth exists in `chrono.gated_effect`; RFC truth exists in persisted `rfcs.json`.

Required fix:
- rebuild money cards from `gated_effect` rows in approvable pending/reconcile-safe states;
- mint fresh owner-bound tokens on boot; never persist raw callback tokens;
- rebuild RFC cards from persisted submitted status;
- durable delivery marker for anti-spam/dedupe;
- old token replay must fail; approval binding must match exact content/action/target.

### S1 — C3 live learning can commit memory without a DecisionReceipt

Evidence:
- `verdict_recorder.record_verdict_durably()` calls `learning_gate.learn_from_outcome(...)` without passing `receipt_store`.
- `learning_gate.learn_from_outcome()` still returns `learned=True` when `receipt_store is None`, with `receipt_id=None`.
- This contradicts the C3 claim that every learned artifact has both memory and receipt.

Required fix:
- instantiate/use the canonical receipts DB on the live owner-verdict learning path;
- make `learned=True` conditional on durable memory **and** durable receipt ID;
- if receipt write fails, retract/quarantine the just-written memory or use a transactional admission/outbox protocol;
- test restart between memory commit and receipt commit; no uncited live memory may survive as admitted.

### S1 — C6 research journal is written but not recovered

Evidence:
- research loop writes `state/journal/research-journal.jsonl`.
- `journal_recovery.boot_recovery()` reads only `run-journal.jsonl` through default durable journal path.

Required fix:
- one canonical journal API with `lane`/`mission_type`, or boot scan of both files;
- recover contract ID, last completed step, budget spent and experiment index;
- resume from next safe step, never rerun an experiment blindly.

### S1 — C6 can claim accepted without durable learning artifact

Evidence:
- `run_experiment()` can return `verdict="accepted"` while `memory_gate`/`outcome_store` are None or learning fails; `memory_id` remains None.
- Report claims memory-only-via-gate, but the return invariant does not enforce it.

Required fix:
- distinguish `verified_proposal` from `accepted_learned`;
- `accepted` requires durable outcome + receipt + memory_id + ledger append success;
- otherwise verdict must be `quarantined` or `verified-not-admitted`;
- append failures may not be swallowed for acceptance-critical artifacts.

### S1 — heartbeat persistence is fail-soft when identity requires fail-closed

Evidence:
- `BeatScheduler._persist()` swallows all exceptions.
- `tick()` advances in memory and reports success even if beat-state was not durably committed.
- after crash, previous durable beat can be repeated.

Required fix:
- two-phase beat identity: reserve/commit or append-only beat ledger;
- ACT is forbidden unless beat reservation and effect idempotency are durable;
- persistence failure marks beat `degraded`, emits alert, and prevents ACT/LEARN commit.

### S2 — content quality of learned memory is not measured

Evidence:
- C3 report honestly says held-out is a system safety circuit breaker, not a per-lesson content oracle.

Required fix:
- build a small owner-labeled frozen dataset;
- compare decisions with/without cited memory;
- admit memory as capability-improving only after measured lift and no regression;
- keep owner preference and real-world outcome as different labels.

### S2 — C4 single producer surface is not yet activated

Evidence:
- `OCTOPUS_SPINE_VIA_ADAPTER` is staged default 0 and absent from current flags.

Required fix:
- shadow parity on real traffic;
- flip adapter flag only after parity;
- remove direct branch only in a later owner-approved archive/refactor window.

### S2 — Telegram center lifecycle not independently proven

C2 report names tg-center auto-restart as remaining continuity gap. The embedded Telegram poll thread exists in organism, but independent tg-center/watchdog health, single poller/no-409 and recovery after crash need a live canary.

## Lower-priority described-but-not-alive items (do not prioritize over S1)

- sprint: UI itself says `stub — built, never ticked`;
- doctor evolution report: UI says not persisted;
- school afferent status: UI says transient/not persisted (despite some SchoolBridge persistence paths; reconcile claim with real SoT);
- crypto summary: UI says not wired;
- doctor box persistence may be absent depending on runtime artifact;
- Archive Packet items remain intentionally unmoved until owner approval.

## Required implementation order

1. **Do not clear STOP-METABOLIC blindly.** Reconcile AU$0.06 first.
2. Continuity slice C2.1: restore pending money/RFC projections.
3. C3 receipt atomicity on the live owner-verdict learning path.
4. C6 invariant hardening + canonical research journal recovery.
5. C5 composition root + real read-only organ adapters in shadow.
6. 24h parity soak while legacy remains authoritative.
7. C4 real adapter soak/flip.
8. Per-lesson held-out dataset and measured learning lift.
9. Only then real research mission; still proposal-only.

## Tests that must be added

- restart with pending money approval → one fresh card, exact binding, old token rejected;
- restart with submitted RFC → one fresh card; consumed/denied/merged never reappears;
- research crash after experiment before verify → resume verify, no experiment repeat;
- acceptance artifact failure → never `accepted`;
- beat-state write failure → ACT/LEARN blocked;
- real `organism.py` shadow composition test with cortex/doctor adapters;
- 24h parity collector and deterministic mismatch report;
- STOP-METABOLIC/HALT throughout all new paths.

## Final status vocabulary

Use only:
- `IMPLEMENTED` = code + focused tests;
- `WIRED` = production caller exists;
- `SHADOW-LIVE` = running over real inputs, no authority;
- `LIVE` = soak green + rollback + truthful UI;
- `HARNESS` = callable in tests/CLI only.

Current honest labels:
C1 WIRED · C2 WIRED/PARTIAL · C3 WIRED · C4 STAGED · C5 HARNESS · C6 HARNESS.

---

## C7 FIX STATUS (agent, 2026-07-23, branch `claude/c7-continuity`)

> Fixes for the audit findings. Branch off live HEAD; STOP-METABOLIC untouched; external flags disarmed;
> OCTOPUS_ONE_HEARTBEAT + OCTOPUS_SPINE_VIA_ADAPTER remain default OFF. Authoritative suite re-run.

| audit finding | fix | commit | truthful label |
|---|---|---|---|
| A3/A4 pending cards RAM-only | `pending_card_recovery` rebuilds money cards from chrono.gated_effect (pending/releasable only; never terminal/EXECUTING/RECONCILE) + RFC from rfcs.json (submitted only); stateless HMAC token full-binding; durable dedup; exactly-once RFC verdict; HALT metadata-only-no-action. Money authorization untouched. Boot hook wired. | `b383304` | **WIRED** |
| #3 live learning without receipt | verdict_recorder passes canonical receipts.db; learning_gate atomic — no receipt_store OR receipt-fail ⇒ retract memory ⇒ learned=False; real dr_ receipt_id exposed | `f5ca23e` | **WIRED** |
| #4 C6 accepted w/o artifact | accepted now requires receipt+outcome+memory(admitted)+strict fsync ledger; else verified-not-admitted/quarantined; ledger errors not swallowed | `e33f7be` | **WIRED** |
| #5 research journal not recovered | journal_recovery.boot_recovery now scans research-journal.jsonl | `e33f7be` | **WIRED** |
| #6 beat persist swallowed | beat identity persisted (fsync) BEFORE phases; _persist returns bool; persist-fail ⇒ degraded, DECIDE/PROPOSE/ACT/LEARN blocked, beat_counter not advanced (no double-effect) | `e33f7be` | **WIRED** |
| #1 BeatScheduler not composed | `brain_core.build_shadow_scheduler` wires REAL read-only adapters (SENSE/RECORD/THINK/HEAL, zero ACT, no second paid loop); organism owns one scheduler ticked in-loop behind flag; ParityTracker + truthful status | `d91f48d` | **SHADOW-LIVE-ready (flag OFF)** |
| C4 single path | soak telemetry; flag default OFF; dual_write not retired; truthful vocab | `d91f48d` | **STAGED** |

Tests: +test_pending_card_recovery(8), test_learning_loop→11, test_research_loop→11, test_beat_scheduler→9, +test_brain_core(5), test_spine_single_surface→6. Authoritative suite: see EXECUTION-LOG.

Honest labels: **C5 not LIVE** (flag OFF; needs real 24h parity soak). **C6 not LIVE** (no real research mission run yet). **STOP-METABOLIC** still requires owner AU$0.06 reconciliation. This branch awaits owner review/merge to master.
