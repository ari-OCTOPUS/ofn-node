---
type: session-capsule
status: verified
session_id: SESSION-20260820-21
date: 2026-08-21
baseline: 9bc506f
accepted_checkpoint: 0ad6f53
current_head: e8b7415
---

# CURRENT-SESSION-CAPSULE

## Octopus چیست؟
سیستم چندلایهٔ محلی (organism/telegram/memory/brains/doctor) با تلگرام به‌عنوان cockpit مالک؛ موج read-only، نوشتن production ممنوع.

## Baseline و HEAD
- baseline: 9bc506f (Wave 0 PASS، frozen)
- accepted checkpoint: 0ad6f53 (پذیرش مالک)
- HEAD: e8b7415 (۱۹ commit بعد از baseline؛ baseline ancestor است)

## Wave state
- Wave 0: PASS، frozen، append-only gate 4/4.
- Wave 1: LOCKED (wave1_unlocked=false). Preflight: ۱۶ shadow read (۱۱ غیرخالی)، zero mutation؛ memory gate suite کهنه → activation مجاز نیست.

## Loopهای بسته
- S-T01 durable transport — PRODUCTION_CLOSED (پنجرهٔ A، message_ids 554/557/560/561/562).
- LOOP-TELEGRAM-COMMAND-COVERAGE — PRODUCTION_CLOSED (پنجرهٔ C: 572/574/576/578/580، verifier سبز).
- LOOP-RUNNING-CODE-DRIFT — PRODUCTION_CLOSED (restart 23568→29492 + manifest).
- RUN_ALL_TIMEOUT — ROOT_CAUSE_FIXED (self_insight journal).
- Unowned fear alert — CONTAINED_VERIFIED.
- Window-B 344/346 — OWNER_OBSERVED_UNCONFIRMED_API (نه confirmed).

## Loopهای باز
- S-T02 event_bridge — IN_PROGRESS (alert واقعی یا تصمیم مالک).
- PROBE-INVALID، LIVE-ORPHAN، Wave 1 preflight، cognitive chain (calibration→improve، EMA، tiers، self_insight shadow)، doctor mission، parity NO_BASELINE، OFN-Board LANE K.

## تصمیم‌های فعال مالک
- گیت commit سمت مالک است؛ Mimosa دور زده نشود؛ OFN-Board جدا.
- verdict معتبر تک است؛ verifier باید SUPERSEDED_BY را preserve کند.
- پنجرهٔ C strict؛ duplicate بدون پیشروی.
- Session Harvest: مستندات Obsidian مجاز؛ memory write تولیدی ممنوع.

## محدودیت‌ها
- paid_calls=0، memory_mutations=0، Wave 1 locked، STOP-TG-HEARTBEAT روشن، بدون incident جعلی، بدون message_id جعلی.

## Next executable actions
1. تعمیر memory gate (F3 + t_h + timeout) — blocker موج ۱.
2. laneهای شناختی (failing test calibration→improve).
3. orphan watchdog observe-only.
4. S-T02: ثبت‌شده، منتظر alert واقعی.

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
