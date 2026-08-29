---
type: decisions-index
created: 2026-08-15
canonical_source: "04 - Architect System/architect/01-Project/DECISIONS.md"
rule: "owner-authored — متن اصلی هرگز تغییر نمی‌کند؛ این فایل فقط ایندکس/راستی‌آزمایی است"
---

# DECISIONS — ایندکس تصمیم‌های مالک (D-01 … D-37 + O-01…O-04)

> **منبع کانونیکال:** [[../04 - Architect System/architect/01-Project/DECISIONS.md|architect/01-Project/DECISIONS.md]] (2026-07-09، append-only)
> مگاپرامپت از «D-1 تا D-21» گفت؛ فایل واقعی **D-01 تا D-37** + چهار تصمیم باز دارد. شواهد مقدم است — چیزی حذف نشد.

## وضعیت راستی‌آزمایی

| بسته | دامنه | verified_in_code | یادداشت |
|------|-------|------------------|---------|
| D-01…D-05 | حاکمیت/معماری کلی (رئیس‌کل=انسان، ۵ جزء core، حذف MVP…) | unchecked | تصمیم‌های سطح طرح — مرجع کدشان در پروژه‌های ai-farm/langar است |
| D-06…D-09 | ایمنی/kill-switch/routing | **partial** | ارجاع `langar/bot.py` → `langar` در `03 - Projects/اونلی فنز/langar` موجود است ✅؛ `fusion-mvp/src/killswitch.py` در این مخزن **پیدا نشد** ❌ (maxdepth 4) |
| D-10…D-23 | مالی/ sandbox / بودجه / tenantها | unchecked | — |
| D-24…D-29 | یکپارچگی سه لایهٔ vault / بودجه v1 / ترتیب tenant / sync | unchecked | D-29: «هیچ سینکی قبل از بستن BACKLOG-01» — ربط مستقیم به قاعدهٔ ۶-۷ همین مأموریت |
| D-30…D-37 | گیت‌های D-A تا D-H (HLC، امضا، genome، تک‌پا، effect-lease) | unchecked | منبع: نشست 2026-07-09 + موافقت Ari |
| O-01…O-04 (architect) | باز: VPS، GROUNDING_REQUIRED، userbot، محل دادهٔ HRV | open | در [[OPEN-VERDICTS]] با شناسهٔ `ARCH-O*` تفکیک شد |

## تداخل شماره‌گذاری (ثبت، بدون حل)

مگاپرامپت از «O-3 = ESP32ها» و «O-4 = Gridcoin/BOINC» گفت؛ فایل architect از «O-03 = userbot Telethon» و «O-04 = محل دادهٔ HRV».
دو سیستم شماره‌گذاری متفاوت‌اند → در [[OPEN-VERDICTS]] هر دو با پیشوند جدا ثبت شدند (MP-O3/MP-O4 برای مگاپرامپت، ARCH-O01…O04 برای architect).

## صف راستی‌آزمایی کد (کار آینده — این جلسه انجام نشد)

- [ ] برای هر D که code_refs دارد، وجود مسیر و رفتار بررسی شود و `verified_in_code: true/false` پر شود
- [ ] D-22/D-25 (سقف‌های بودجه) با `_ops/budget/budget-state.json` تطبیق داده شود
- [ ] D-32 (امضای entry) با کد فعلی تلگرام/امضا تطبیق داده شود
