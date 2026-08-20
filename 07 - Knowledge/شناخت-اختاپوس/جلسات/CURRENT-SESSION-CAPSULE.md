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
سیستم چندلایهٔ محلی (organism/telegram/memory/brains/doctor) با تلگرام به‌عنوان cockpit مالک؛ موج read-only، نوشتن production ممنوع.

## Baseline و HEAD
- baseline: 9bc506f (Wave 0 PASS، frozen)
- accepted checkpoint: 0ad6f53 (پذیرش مالک)
- generated_from_head: e8b7415 — هاروست از این HEAD تولید شد
- current_head_at_final_verification: fec3288 (۳ commit هاروست: 3f5343b ← 10eceb3 ← fec3288)

## Wave state
- Wave 0: PASS، frozen، append-only gate 4/4.
- Wave 1: LOCKED (wave1_unlocked=false). Preflight: ۱۶ shadow read (۱۱ غیرخالی)، zero mutation؛ memory gate suite کهنه → activation مجاز نیست.

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

## Loopهای باز (9)
- S-T02 event_bridge — IN_PROGRESS (alert واقعی یا تصمیم مالک).
- PROBE-INVALID، LIVE-ORPHAN، OFN-Board LANE K — OPEN.
- Wave 1 — LOCKED (پیش‌شرط: تعمیر memory gate).
- cognitive chain (calibration→improve، EMA، tiers، self_insight shadow، self-audit probes).
- doctor mission deadlock — OPEN.
- brain parity — NO_BASELINE.
- LOOP-APPROVAL-QUEUE — OPEN / OWNER_DECISION_REQUIRED (owner-reported pending=20؛ منبع محلی پیدا نشد).

## تصمیم‌های فعال مالک
- گیت commit سمت مالک است؛ Mimosa دور زده نشود؛ OFN-Board جدا.
- verdict معتبر تک است؛ verifier باید SUPERSEDED_BY را preserve کند.
- پنجرهٔ C strict؛ duplicate بدون پیشروی.
- Session Harvest: مستندات Obsidian مجاز؛ memory write تولیدی ممنوع.
- تصحیح حسابداری هاروست: CONTAINED/UNCERTAIN هرگز CLOSED شمرده نشوند.

## محدودیت‌ها
- paid_calls=0، memory_mutations=0، Wave 1 locked، STOP-TG-HEARTBEAT روشن، بدون incident جعلی، بدون message_id جعلی، بدون اجرای خودکار approve/reject، سکوت = approval نیست، پول قفل.

## Next executable actions
1. تعمیر memory gate (F3 + t_h + timeout) — blocker موج ۱.
2. laneهای شناختی (failing test calibration→improve).
3. orphan watchdog observe-only.
4. S-T02: ثبت‌شده، منتظر alert واقعی.
5. Approval queue: digest به مالک با گزینه‌های approve/reject/defer.

## Evidence entrypoints
- `_ops/state/loops/TELEGRAM-CANARY-AUTHORITATIVE-VERDICT.json`
- `_ops/state/loops/canary-coverage-2026-08-21-C/AUDIT.json`
- `_ops/state/loops/EVENT-BRIDGE-CANARY-2026-08-21.json`
- `_ops/state/waves/WAVE1-PREFLIGHT-2026-08-21.json`
- `06-EVIDENCE/SESSION-HARVEST-2026-08-21/`

## چیزهایی که نباید دوباره کشف شوند
- گارد canary در center.run_once وصل است؛ observe بعد از auth و قبل از intent.
- uncertain send → صف reconciliation؛ OWNER_OBSERVED هرگز DELIVERY_CONFIRMED نیست.
- append-only با prefix integrity؛ verifier با merge_preserved.
- پنجرهٔ C دقیقاً با همان update_ids/msg_ids بسته شده.
