---
type: proposal
project: "[[04 - Architect System/architect/PROJECT]]"
status: implemented
tags: [octopus, prompt, build, heart, chrono]
created: 2026-07-08
updated: 2026-07-08
created_by: agent
---

# PROMPT — Octopus Build · Phase 1: THE HEART (Chrono substrate)

> **برای آری:** مهم‌ترین و بی‌کدترین بخش. این پرامپت قلبِ Octopus را می‌سازد: ضربان، ساعت، دفترِ میرا (`age_tick`)، و نرخِ تجربه. طبق طرحِ خودت. هیچ منطقِ کسب‌وکاری دست نمی‌خورد — فقط یک لایهٔ زمان روی سیستمِ موجود سوار می‌شود.

## 0. ROLE
You build the **Chrono substrate** for Octopus and nothing else this phase. Additive only. Business logic untouched (DOC-B §0). Read-only until you have a plan; then implement step by step with a green test after each step.

## 1. PREREQUISITE
Read `04 - Architect System/OCTOPUS-RECON-MAP.md` §2 (heart/substrate). Confirm (with citations) that no `pacemaker/HLC/langar_ledger/age_tick/experience_rate` code exists yet. If any exists, wrap/extend it — do NOT duplicate.

## 2. SOURCES (verbatim design — follow exactly)
- `CHRONOS-FABLE-OS/10_Implementation/DataSchemas.sql` — the exact DDL (heartbeat, leg_clock, langar_ledger, experience_meter, duration_marker, anticipation_queue).
- `CHRONOS-FABLE-OS/01_SourceMap/_primaries/OCTOPUS_CHRONO_ARCHITECTURE.md` §8 (schema) + §9 (pseudocode: `heartbeat_loop`, `leg_loop`, `on_human_judgment`) + §11 (implementation order).
- `CHRONOS-FABLE-OS/08_Safety/HeartDesign_PulseCore.md` — the Pulse Core cascade (L0/L1/L2/DORMANT), fail-closed FSM, EffectorGate.
- Existing code to extend: `07 - Knowledge/genome-system/ledger/ledger.py` (hash-chain), `_ops/organism.py` (the always-on loop), `_ops/budget/opslib.py` (ledger bridge, LockedJson, flags).

## 3. LAWS (critical for this phase)
- **Extend, don't rival:** add `age_tick`/`is_human` to the existing genome ledger; don't create a second ledger.
- **`age_tick` advances ONLY on human-append (`is_human=1`)** — TINV-3 (ratified). Never auto-age. ⚠️ **Superseded by owner verdict 2026-07-08 → implemented as genome v0.4.6 (age_tick advances on human OR heartbeat `beat=1`; versioned so legacy still verifies). Windows-side suite + commit pending — see §6 + [[00 - Inbox/AGENT_QUESTIONS|AGENT_QUESTIONS]].**
- **TINV-5:** legs never read wall-clock; only HLC + last `beat_seq`.
- **TINV-7 effect-gate:** no `send/publish/sync/pay` settles without a LANGAR append first.
- **Two-clock:** heart beat-rate + load drives `experience_rate` (metabolic aging); the human tap drives `age_tick`. Confirm with operator that mortality is NOT heart-driven (default: no).
- SQLite single-writer: serialize leg writes at the heartbeat barrier. `$0` offline. UTF-8.

## 4. STEPS (do in order; a green test after each)

**P-Chrono-1 · Pacemaker + heartbeat loop.** Create `_ops/chrono.py`. Add the `heartbeat` table (DataSchemas.sql). Implement `heartbeat_loop(bus, legs, db, PERIOD=60)` per DOC-B §9: tick → collect acks → phi-accrual → shared-now = `hlc_max` → broadcast `{beat, hlc, present}` → run due scheduler items (this **also closes the missing F19 scheduler** — followup/escalate live here) → insert heartbeat row (light checkpoint). Wire it as a background task in `_ops/organism.py`. Test: `_ops/tests/test_chrono_heartbeat.py` — N ticks advance `beat_seq` monotonically, no wall-clock read in legs.

**P-Chrono-2 · HLC per leg.** Add `leg_clock` table + `hlc_tick`/`hlc_merge`/`hlc_max` (~20 lines, CockroachDB algo: on event `l=max(l,pt)`; if `l` unchanged `c+=1` else `c=0`). Stamp every emitted event with an HLC. Enforce TINV-5. Test: causal ordering across two simulated legs; monotonic HLC.

**P-Chrono-3 · phi-accrual liveness.** Per-leg `state ∈ {alive,suspected,failed}` via phi-accrual (SWIM suspected). `failed` → doctor restart from known-good ledger state (leave a hook `doctor.restart_from_known_good(leg, db)` for Phase 2). Test: a silent leg transitions alive→suspected→failed at the right thresholds.

**P-Chrono-4 · LANGAR arrow (`age_tick`).** Extend `genome-system/ledger/ledger.py` to the `langar_ledger` shape: add `age_tick`, `is_human`. Implement `on_human_judgment(judgment, db)` (DOC-B §9): append with `is_human=1`, `age_tick = last+1`, then `release_gated_effects(up_to=entry_seq)`. `age_tick` never decreases; reversal = hash-chain break = logical death. Bump genome CHANGELOG. Test: `age_tick` moves ONLY on `is_human=1`; hash-chain still verifies; non-human appends leave age unchanged.

**P-Chrono-5 · experience_rate + metabolic coupling.** Add `experience_meter`; `rate = events / Δt_pacemaker`, hard-capped (hardware ceiling), floor 0. Couple: busier leg per beat consumes more of the metabolic budget (faster = older, in the `experience_rate` sense only). Test: rate bounded within [0, cap]; coupling monotonic; `age_tick` unaffected (two-clock proven).

**P-Chrono-6 · duration + anticipation.** Add `duration_marker` (duration = now_hlc − event_hlc) and `anticipation_queue` keyed by `due_beat` (NOT wall-clock). The heartbeat scheduler dispatches due items by beat. Test: a scheduled item fires on the right beat regardless of wall-clock.

**P-Chrono-7 · TINV-7 effect-gate (choke-point).** Introduce a single `EffectorGate.settle(effect)` that refuses unless a matching LANGAR append exists. Route every world-effect path through it (this is the EffectorGate of HeartDesign; wire actual senders in later phases). Test: an irreversible effect cannot settle without a prior append; kill-switch force-closes the gate.

## 5. DEFINITION OF DONE
- Heartbeat live in `organism.py`; every event HLC-stamped; legs read no wall-clock.
- `age_tick` moves ONLY on human-append; hash-chain verifies; two-clock proven (experience_rate ≠ age_tick).
- Effect-gate proven: no irreversible effect settles without an append; kill force-closes it.
- New isolated tests all green; `python -X utf8 _ops/tests/run_all.py` still green; business logic byte-unchanged.

## 6. OPEN-DECISIONS — RESOLVED (owner verdicts 2026-07-08)
- **Mortality:** ⚠️ owner **re-ratified → age_tick IS heart-driven** (reverses ratified TINV-3 / §3 / 00-INDEX shared-law) → **implemented as genome v0.4.6**: `age_tick` advances +1 on a human append OR a pacemaker heartbeat (`beat=1`, every `CHRONO_AGE_PER_N_BEATS` beats — default 1440 ≈ daily, env-tunable). Versioned via a per-record `age_rule` tag so legacy records still `verify()`. Algorithm sandbox-tested (15 checks + py_compile); **Windows-side full suite + commit pending** — see [[00 - Inbox/AGENT_QUESTIONS|AGENT_QUESTIONS 2026-07-08]].
- **Numbers:** accepted as built defaults (env-tunable): `CHRONO_PERIOD_S=60 · PHI_SUSPECT=8 · PHI_DEAD=16 · XP_RATE_CAP=50 · WEAR_BASE=1.0`.

## 7. HAND-BACK
Update `_ops/ORGANISM-SPEC.md` (add the Chrono layer to the module map), refresh `01 - Dashboard/HANDOFF.md` (wikilinks only), keep the suite green, and leave an owner-gated `agent-checkpoint:` commit. Then STOP — Phase 2 (Doctor) consumes the `restart_from_known_good` hook and the effect-gate.
