---
type: report
project: "[[04 - Architect System/architect/PROJECT]]"
status: ready
tags: [octopus, missing-edges, reuse]
created: 2026-08-29
updated: 2026-08-29
created_by: agent
language: fa
sources:
  - "[[06-EVIDENCE/OCTOPUS-REUSE-AUDIT-2026-08-29/REUSE-MAP]]"
  - "[[06-EVIDENCE/OCTOPUS-L191-FINDINGS-2026-08-28]]"
---

# MISSING-EDGES

P1 بسته شد ۲۰۲۶-۰۸-۲۹: E2 mismatch هویت صف **CONFIRMED** (`mesh message_id` ≠ `tenant:idem`).

فقط یال. هیچ ماژول جدیدی اینجا تعریف نمی‌شود.

مشاهده: 2026-08-29. پروب runtime تازه به ۱۳۸ انجام نشد. وضعیت ۱۳۸ = آخرین LIVE_RUNTIME مستند (L191 + `f09681a`)، برچسب `inference` وقتی تعمیم داده شود.

## اولویت مشکوک (از دستور مالک) — حکم شواهد

### E1 — provenance ری‌استارت / هویت درخت در برابر `c803dee`

| | |
|---|---|
| چیست | `ofn.service` روی درختی که M1 دارد ری‌استارت شده (`F-1` / P1 در `f09681a`) بدون receipt تأیید. `c803dee` **نوک vault** است نه نوک ۱۳۸. |
| نوع | MISSING_CONNECTION (receipt) + خطر اشتباه گرفتن دو HEAD |
| اثبات لازم | یک receipt: unit start time + `HEAD` worktree ۱۳۸ + sha `ofn/run.py` + sha `cockpit_v2_read_model.py` در صورت وجود |
| نساز | سیستم provenance جدید؛ از ledger/audit موجود استفاده کن |
| وضعیت امروز این میزبان | **باز**. reboot بعدی را بدون receipt نبند |

### E2 — Cockpit V2 در برابر پنل legacy به‌عنوان منبع فرمان — CONFIRMED

| | |
|---|---|
| چیست | دو UI **و دو صف**. فرمان = `POST /api/v1/decide` روی `tenant:idem`. V2 queue = `message_id` فایل‌های mesh. |
| نوع | MISSING_CONNECTION داخل ReadModel موجود · نه کمبود API |
| حکم P1 | **A CONFIRMED / B REJECTED** — جزئیات [[P1-QUEUE-IDENTITY]] |
| نساز | `/api/control/v2` یا UI سوم |
| پچ بعدی | منبع outbox کسب‌وکار را به `_collect_queue` یا resource صریح `business_outbox` اضافه کن؛ GO لازم |

### E3 — F-2 claims در verify-dispatcher

| | |
|---|---|
| چیست | dispatcher فقط ID می‌فرستد → witness empty/unresolved (`04af67d5`, `e19fe76b` در audit) |
| نوع | DISK_ONLY + MISSING_CONNECTION |
| فایل | `/home/ari/octopus-mesh/bin/octopus_verify_dispatcher.py` (طبق body-map؛ **این نشست فایل را نخواند**) |
| `6881337` بست؟ | witness_mint + fake E2E را اضافه کرد؛ **خود dispatcher را در git ofn-node اصلاح نکرد** |
| نساز | سرویس verify جدید |
| وضعیت | **باز فرض کن** تا diff همان فایل دیسکی دیده شود |

### E4 — 180 proposal → 182 witness → OwnerDecision

| | |
|---|---|
| چیست | EDGE-6: handler spine بعد از registry `return` می‌کند؛ `outbox.persist_pending` / `transmit_pending` صدا نمی‌شود (L191 FACT). mint ۱۳۸ و witness ۱۸۲ برای `run-spine-138-snap-20260828T005835Z` MISSING_FOR_RUN. |
| نوع | MISSING_CONNECTION روی کد موجود ۱۸۰ |
| OwnerDecision | حتی پس از drain، decide فعلی فیلدهای ۱۲تایی را mint نمی‌کند |
| نساز | command bus / witness service |
| پچ کمینهٔ قبلاً شناسایی‌شده | همان ۳ خط الگوی mirror پس از registry — نیاز GO روی ۱۸۰؛ این نشست اعمال نکرد |

### E5 — production Telegram decision renderer

| | |
|---|---|
| چیست | `138-TELEGRAM-CONTRACT.md`: CONTRACT_GAP. پنج token، صفر poller، bridge مرده، `alert.py` shadow، کارت OwnerDecision نیست. |
| نوع | MISSING_CONNECTION روی bot `__owner__` موجود |
| نساز | bot ششم / sender جدید |
| reuse | فیلدهای `OwnerDecision` + یک poller وقتی env موجود است + `alert.py` فقط اگر همان Owner Control path شود، نه کانال موازی |

### E6 — backup mesh

| | |
|---|---|
| چیست | GAP-3: `ofn-backup.timer` DBهای OFN را می‌گیرد؛ `~/octopus-mesh` کامل نیست |
| نوع | MISSING_CONNECTION روی timer canonical |
| نساز | سیستم backup چهارم |
| پچ | additive یک‌خطی طبق `HOW-TO-CONNECT` — فقط با GO |

### E7 — canonical test discovery/count

| | |
|---|---|
| چیست | ۲۰۲۸ در `f09681a`؛ اعداد دیگر در evidence پراکنده |
| نوع | DUPLICATE counters |
| نساز | تست بیشتر برای بالا بردن عدد |
| پچ | یک runner (`unittest discover` سندشده) + ثبت error `test_greeting_name` |

## یال‌های اضافی که این ممیزی پیدا کرد

### E8 — `OwnerDecision` ↛ `http_api` / `run.py`

@ `6881337`، `run.py` فقط `CockpitV2ReadModel` را load می‌کند. هیچ import از `owner_decision` / `witness_mint` / `fake_executor` در آن فایل دیده نشد.  
پس schema ۱۲ فیلدی **وجود دارد و بی‌سیم است.**

### E9 — `fake_executor` ↛ outbox

Executor آزمایشی receipt را در `state_dir` تست می‌نویسد، نه در `Outbox.approve_manual`. اتصال به sole egress موجود نیست.

### E10 — vault `c803dee` ↛ فایل‌های V2/spine

ساختن دوبارهٔ همان فایل‌ها داخل `F:\backup\03 - Projects\OFN-Board` = بازنویسی موازی.  
اگر لازم شد، merge **داخل** خانوادهٔ ofn-node (`OD-SYNC-03`)، نه کپی به germline.

### E11 — نام Cockpit V2 دو بار

ارگانیسم `_ops` و OFN هر دو «cockpit v2» دارند. ادغام کد ممنوع؛ فقط qualify در اسناد.

## رد ادعا: «کمبود معماری»

ماژول‌های خوانده‌شده کافی‌اند. شکاف‌ها **یال**اند. تا E1 و E4 و E8 بدون پچ موازی مشخص نشوند، هر Event Store / Command Bus / orchestrator جدید = REJECT.
