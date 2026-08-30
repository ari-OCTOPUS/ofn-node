---
type: report
project: "[[04 - Architect System/architect/PROJECT]]"
status: ready
tags: [octopus, owner-decision, witness, p2]
created: 2026-08-29
updated: 2026-08-29
created_by: agent
language: fa
sources:
  - "[[06-EVIDENCE/OCTOPUS-REUSE-AUDIT-2026-08-29/P1-RESULT]]"
  - "[[06-EVIDENCE/OCTOPUS-REUSE-AUDIT-2026-08-29/MISSING-EDGES]]"
---

# P2 Discovery — OwnerDecision binding، بدون پچ

```
P2_PATCH_APPLIED=false
OWNER_DECIDE_TRACED=true
OWNER_DECISION_DATA_AVAILABLE_AT_APPROVAL=false
LOCAL_WITNESS_IS_CANONICAL=false
SMALLEST_SEAM=producer_binding_then_owner_decide_validation
RUNTIME_CHANGES=0
EXTERNAL_EFFECTS=0
```

## مسیر واقعی

```
POST /api/v1/decide
  → ApiApp._owner_decide(item, approve, confirmed_twice)
  → Node.owner_decide
      → outbox.get(scope, key)
      → executable(...human_approved...)
      → outbox.approve_manual(scope, key)
      → ledger.append(VERDICT)
```

این مسیر فقط `item_id`, `approve`, `confirmed_twice` می‌گیرد. V2 در آن نیست.

## چرا ساخت OwnerDecision داخل `owner_decide` هنوز امن نیست

`OwnerDecision.validate()` دوازده فیلد غیرخالی می‌خواهد:
`decision_id`, `run_id`, `lane`, `action`, `recipient_masked`,
`exact_payload`, سه hash، `idempotency_key`, `expires_at`, `rollback`.

در لحظهٔ `owner_decide`:

- OutboxItem: `idem_key`, `tenant`, `kind`, `payload`, `tier`, lifecycle timestamps.
- ندارد: `run_id`, `artifact_sha`, `verdict_sha`, `expires_at`, `rollback`,
  witness reference.
- exact send payload فقط بعداً در `owner_outbox_packet()` از
  `text|caption|message` ساخته می‌شود.
- `validate()` عمداً hash واقعی `exact_payload` را verify نمی‌کند؛ این کار
  در executor است.

پس ساخت record در approval با مقدارهای حدسی fail-open یا fabricated provenance می‌شود.

## Witness boundary

`witness_mint.mint_witness_request()`:

- artifact bytes + payload bytes + policy/schema version می‌خواهد.
- یک JSONL محلی می‌نویسد.
- فقط `STRUCTURAL_PASS` می‌سازد.
- حق ساخت `EXECUTABLE_PASS` ندارد.

body-map، worker ۱۸۲ را witness کانونیکال می‌داند. بنابراین فراخوانی مستقیم
local `witness_mint` داخل `Node.owner_decide` یک witness truth موازی می‌سازد
و فعلاً **REJECT** است.

## کوچک‌ترین seam پیشنهادی برای commit جدا

### Producer side — قبل از enqueue

1. binding کامل از artifact/payload واقعی ساخته شود.
2. `propose()` به choke point موجود `_gate_enqueue()` همگرا شود؛ orchestrator جدید نه.
3. binding داخل payload موجود یا receipt موجود حمل شود؛ migration/DB جدید نه.
4. درخواست witness ۱۸۲ قبل از نمایش card ثبت شود.

### Approval side — داخل `owner_decide`

1. binding موجود را بخواند؛ هیچ مقدار missing را نسازد.
2. `OwnerDecision(...)` بسازد و `validate()` کند.
3. payload hash را جداگانه روی exact bytes دوباره محاسبه کند.
4. witness reference کانونیکال ۱۸۲ را verify کند.
5. فقط بعد همان `outbox.approve_manual()` موجود اجرا شود.
6. ledger VERDICT شامل decision_id/payload_sha/witness_id شود.

### Shadow observer

`fake_executor` بعد از approval فقط در shadow:
`provider_called=false`. این fake نباید runtime executor شود.

## RED لازم برای P2

1. item بدون binding → approval fail-closed؛ outbox همچنان pending.
2. artifact/verdict/run/expiry ناقص → fail-closed.
3. payload hash mismatch → fail-closed.
4. witness ۱۸۲ missing/unresolved → fail-closed.
5. binding کامل → همان existing `approve_manual`, بدون provider.
6. reject path به OwnerDecision وابسته نشود.
7. legacy items سیاست migration صریح داشته باشند؛ فعال‌کردن ناگهانی gate همهٔ
   آیتم‌های قدیمی را قفل می‌کند.

## تصمیم باز قبل از P2 implementation

منبع canonical برای این شش مقدار باید مشخص شود:
`run_id`, `artifact bytes`, `verdict bytes`, `recipient_masked`,
`expires_at`, `rollback`.

تا آن زمان P2 فقط discovery است؛ هیچ schema یا witness موازی اضافه نشود.
