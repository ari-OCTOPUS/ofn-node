---
type: layer-needs-council
status: evidence-backed
date: 2026-08-21
session_id: SESSION-20260820-21
---

# شورای نیازهای لایه‌ها — 2026-08-21

این شورا role-play نیست؛ هر ردیف از state/evidence لایه استخراج شده است.

## کارت لایه‌ها

```json
{"layer_id": "organism", "current_state": "poll سالم، restart کنترل‌شده، offset پایدار؛ LIVE-ORPHAN باز", "most_important_learning": "restart فقط با snapshot + hash manifest", "largest_open_loop": "LIVE orphan supervision", "requested_input": "wiring مشاهده‌ای watchdog", "proposed_next_action": "observe-only wiring + بستن بدون restart", "risk_if_ignored": "orphan بدون نظارت ادامه می‌دهد", "evidence_refs": ["RUNNING-CODE-MANIFEST-2026-08-21.json"], "confidence": 0.92}
```

```json
{"layer_id": "telegram", "current_state": "transport + command coverage PRODUCTION_CLOSED؛ S-T02 IN_PROGRESS", "most_important_learning": "گارد باید runtime وصل باشد", "largest_open_loop": "S-T02 event_bridge", "requested_input": "alert واقعی یا تصمیم مالک", "proposed_next_action": "ثبت‌شده؛ منتظر alert واقعی", "risk_if_ignored": "S-T02 بی‌شاهد می‌ماند", "evidence_refs": ["TELEGRAM-WINDOW-C-VERDICT.json", "EVENT-BRIDGE-CANARY-2026-08-21.json"], "confidence": 0.95}
```

```json
{"layer_id": "memory", "current_state": "read کار می‌کند (۱۱/۱۶ غیرخالی)؛ write-gate suite کهنه", "most_important_learning": "read-only با uri mode=ro اثبات می‌شود", "largest_open_loop": "memory gate F3 بدهی", "requested_input": "تعمیر تست‌ها + t_h", "proposed_next_action": "تعمیر memory gate (failing-test-first)", "risk_if_ignored": "موج ۱ activation مسدود", "evidence_refs": ["WAVE1-PREFLIGHT-2026-08-21.json"], "confidence": 0.9}
```

```json
{"layer_id": "cortex", "current_state": "fallback محلی با label DEGRADED_LOCAL_ONLY", "most_important_learning": "degradation باید صریح label شود", "largest_open_loop": "calibration→improve", "requested_input": "verify زنجیرهٔ علی", "proposed_next_action": "failing test برای calibration→improve", "risk_if_ignored": "feedback شکسته می‌ماند", "evidence_refs": ["telegram_adapter.py"], "confidence": 0.85}
```

```json
{"layer_id": "self-model", "current_state": "card journal-based؛ EMA و tiers باز", "most_important_learning": "render نباید اسکن سراسری کند", "largest_open_loop": "self_knowledge EMA", "requested_input": "EMA receipt-backed", "proposed_next_action": "EMA با failing test", "risk_if_ignored": "confidence ثابت می‌ماند", "evidence_refs": ["84a8a96"], "confidence": 0.85}
```

```json
{"layer_id": "doctor", "current_state": "doctor-link فعال؛ mission timeout باز", "most_important_learning": "mission بدون timeout deadlock است", "largest_open_loop": "mission deadlock", "requested_input": "timeout/quarantine/replacement", "proposed_next_action": "واحد timeout mission", "risk_if_ignored": "deadlock تک‌mission", "evidence_refs": ["LOOP-REGISTRY.json"], "confidence": 0.85}
```

```json
{"layer_id": "4d-system", "current_state": "parity NO_BASELINE", "most_important_learning": "مقایسهٔ بی‌مرجع PASS نیست", "largest_open_loop": "parity baseline", "requested_input": "baseline معتبر", "proposed_next_action": "ثبت NO_BASELINE", "risk_if_ignored": "validation جعلی", "evidence_refs": ["LOOP-REGISTRY.json"], "confidence": 0.9}
```

```json
{"layer_id": "safety", "current_state": "Mimosa فعال؛ secret scan صفر؛ LANE K جدا", "most_important_learning": "safety gate هرگز دور زده نشود", "largest_open_loop": "OFN-Board LANE K", "requested_input": "تصمیم مالک", "proposed_next_action": "LANE K جدا بماند", "risk_if_ignored": "commit مسدود می‌ماند", "evidence_refs": ["02-DECISIONS"], "confidence": 0.95}
```

```json
{"layer_id": "tests", "current_state": "۵۶ تست سبز؛ triage ۵۱ فایل؛ memory gate کهنه", "most_important_learning": "ثبت با اجرا فرق دارد", "largest_open_loop": "memory gate suite", "requested_input": "تعمیر F3 + timeout", "proposed_next_action": "تعمیر با failing-test-first", "risk_if_ignored": "موج ۱ مسدود", "evidence_refs": ["TRIAGE-51-FAILURES"], "confidence": 0.92}
```

```json
{"layer_id": "capabilities", "current_state": "inventory ۱۰ قابلیت؛ ۰ غلط VERIFIED", "most_important_learning": "IMPLEMENTED بدون OBSERVED VERIFIED نیست", "largest_open_loop": "قابلیت‌های DECLARED_UNOBSERVED", "requested_input": "evidence", "proposed_next_action": "به‌روزرسانی matrix", "risk_if_ignored": "ادعای بی‌شاهد", "evidence_refs": ["CAPABILITY-LOOP-MATRIX.json"], "confidence": 0.93}
```

## توافق لایه‌ها (حداقل سه لایه)

- **memory gate suite باید تعمیر شود** — memory، tests و capabilities هر سه Wave 1 را به آن گره زده‌اند (NEED-001/002).
- **S-T02 بدون alert واقعی یا تصمیم مالک بسته نمی‌شود** — telegram، safety و tests.
- **هر loop باید closure path داشته باشد** — capabilities، tests، organism.
- **zero paid call / zero memory write در موج read-only** — safety، memory، telegram.

## اختلاف لایه‌ها

- **S-T02 terminal**: telegram می‌گوید low-urgency به notif inbox می‌رود (طراحی)؛ در حالی که رویدادهای incident مستقیم به تلگرام می‌روند. این دو رفتار هم‌زمان درست‌اند؛ شواهد جدا ثبت شد (EVENT-BRIDGE-CANARY).
- **memory gate**: تست‌ها کهنه‌اند (F3) ولی مشخص نیست gate در تولید کدام رفتار دارد — نیاز به بازتولید روی state واقعی دارد.

## Dependency order

1. تعمیر memory gate (blocker موج ۱).
2. laneهای شناختی (calibration→improve ← self_knowledge EMA ← cockpit tiers).
3. recovery (orphan watchdog ← LIVE-ORPHAN ← PROBE-INVALID).
4. S-T02 (منتظر alert واقعی یا تصمیم مالک).

## درخواست‌های واقعی از مالک

- NEED-011: تصمیم OFN-Board LANE K.
- NEED-003/012: alert واقعی event_bridge یا تأیید اینکه inbox-termination کافی است.

## کارهای خودکار

- NEED-001/002/004/005/006/007/008/009/010: همگی self_resolvable → repair queue.
