---
type: session-capsule
status: verified
session_id: SESSION-20260820-21
date: 2026-08-21
baseline: 9bc506f
accepted_checkpoint: 0ad6f53
generated_from_head: e8b7415
harvest_evidence_commit: 3f5343b
harvest_reflections_commit: 10eceb3
harvest_capsule_commit: fec3288
current_head_at_final_verification: fec3288
canonical_harvest_entry: 75-SESSION-HARVEST-WAVE0-TELEGRAM-2026-08-21
---

# CURRENT-SESSION-CAPSULE

## Octopus چیست؟
سیستم چندلایهٔ محلی (organism/telegram/memory/brains/doctor) با تلگرام به‌عنوان cockpit مالک. Wave 1 با حکم مالک باز است؛ LAB_PASS ادعاى AGI نیست.

## Baseline و HEAD
- baseline: 9bc506f (Wave 0 PASS، frozen)
- accepted checkpoint: 0ad6f53 (پذیرش مالک)
- generated_from_head: e8b7415 — هاروست از این HEAD تولید شد
- current_head_at_final_verification: fec3288 (۳ commit هاروست: 3f5343b ← 10eceb3 ← fec3288)

## Wave state
- Wave 0: PASS، frozen، append-only gate 4/4.
- Wave 1: UNLOCKED (owner grant 2026-08-21). Production authority is `_ops/state/wave1/lock.json`. Memory gate 12/12 on live.

## Continuation 2026-08-21 — AGI loop passes + lab
- Pass 1 READ-ONLY: `06-EVIDENCE/AGI-LOOPS-PASS1-2026-08-21/` + `_ops/state/loops/AGI-LOOP-REGISTRY.jsonl`.
- Pass 2 SHADOW: `06-EVIDENCE/AGI-LOOPS-PASS2-SHADOW-2026-08-21/`.
- Pass 3 LIVE: **granted** — [[../../02-DECISIONS/OWNER-GRANT-UNLOCK-AGI-LOCKS-2026-08-21]] · digest msg 583 · doctor-pulse merged.
- Self-upgrade lab: memory ALREADY_FIXED · heart/brain LAB_PASS · observe_only merged to live. [[../../06-EVIDENCE/SELF-UPGRADE-LAB-CYCLE-2026-08-21/README]] · نوت [[../79-SELF-UPGRADE-LAB-CYCLE-2026-08-21|۷۹]].

## Next executable actions
1. BotFather Menu Button → `/miniapp` (owner manual).
2. Route miniapp for the 10 families still UNROUTED — without both surfaces they cannot close L6.
3. Register `_ops/tests/test_improve_reads_calibration.py` in `run_all.py` (WORKLOCK — report name, do not self-register).
4. LOOP-APPROVAL-QUEUE still OPEN (local pending≠owner-reported 20).
5. Center restart still required for D15 `is_bot` skip if PID is pre-splice.

## محدودیت‌ها
- paid_calls this lab cycle=0. LAB_PASS ≠ L6 OWNER_VISIBLE. سکوت = approval نیست. Miniapp 10 UNROUTED not granted.

## Loopهای بسته (PRODUCTION_CLOSED = 3)
- S-T01 durable transport — PRODUCTION_CLOSED (پنجرهٔ A، message_ids 554/557/560/561/562).
- LOOP-TELEGRAM-COMMAND-COVERAGE — PRODUCTION_CLOSED (پنجرهٔ C: 572/574/576/578/580، verifier سبز).
- LOOP-RUNNING-CODE-DRIFT — PRODUCTION_CLOSED (restart 23568→29492 + manifest).
- RUN_ALL_TIMEOUT — ROOT_CAUSE_FIXED (self_insight journal؛ ریشه‌یابی، نه closure تولیدی).

## Loopهای CONTAINED (2)
- LOOP-TELEGRAM-UNOWNED-INSTANT-ALERT — CONTAINED_VERIFIED: **task identity هنوز غایب است؛ CLOSED نیست**.
- LOOP-LEGACY-RECEIPT-UNCONFIRMED — CONTAINED_VERIFIED: رزولوشن owner-observed.

## قرنطینه / نامعلوم (2)
- Window-B updates 223883344 و 223883346 — OWNER_OBSERVED_UNCONFIRMED_API / QUARANTINED: **بدون message_id/readback تأییدشده؛ DELIVERY_CONFIRMED نیستند**؛ هرگز auto-resend.

## Loopهای باز
- S-T02 event_bridge — IN_PROGRESS.
- PROBE-INVALID / heartbeat — STOP file moved (owner grant); loop not L6-closed.
- LIVE-ORPHAN — observe_only now on live; L6 still needs owner-visible surface.
- Miniapp 10 UNROUTED families — cannot close without both surfaces.
- LOOP-APPROVAL-QUEUE — OPEN (local pending≠owner-reported 20).
- brain parity — NO_BASELINE.

## تصمیم‌های فعال مالک
- گیت commit سمت مالک است؛ Mimosa دور زده نشود؛ OFN-Board جدا.
- سکوت = approval نیست. Miniapp routes for 10 families not granted.
- LAB_PASS در worktree ≠ PRODUCTION_VERIFIED.

## Evidence entrypoints
- `_ops/state/loops/TELEGRAM-CANARY-AUTHORITATIVE-VERDICT.json`
- `_ops/state/waves/WAVE1-PREFLIGHT-2026-08-21.json`
- `06-EVIDENCE/SELF-UPGRADE-LAB-CYCLE-2026-08-21/`
- `06-EVIDENCE/AGI-LOOPS-PASS3-LIVE-2026-08-21/`
- `06-EVIDENCE/SESSION-HARVEST-2026-08-21/`

## چیزهایی که نباید دوباره کشف شوند
- گارد canary در center.run_once وصل است؛ observe بعد از auth و قبل از intent.
- uncertain send → صف reconciliation؛ OWNER_OBSERVED هرگز DELIVERY_CONFIRMED نیست.
- append-only با prefix integrity؛ verifier با merge_preserved.
- پنجرهٔ C دقیقاً با همان update_ids/msg_ids بسته شده.
- Full `git worktree add` روی این vault >۱۲۰ث؛ lab باید `--no-checkout` + sparse `_ops` باشد.
- `secret-scan` نباید `token` داخل `max_tokens` یا `sk-` داخل `ask-exception` را بلوک کند.
