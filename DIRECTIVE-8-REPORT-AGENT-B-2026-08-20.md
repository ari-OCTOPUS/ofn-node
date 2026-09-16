---
type: evidence
task: directive-8-report
tags: [octopus, directive-8, agent-b, t47-t51, live-a, live-b, live-c]
created: 2026-08-20T15:05+10:00
created_by: agent B (ZCode) — session sess_1d388c34-c221-49c0-a2d7-0e7d225b5968
authority: "[[../../02-DECISIONS/OWNER-DIRECTIVE-08-2026-08-20]] §۹"
lease: 8d7b0c413a704534a211db58c107be2d (renewed; released at session end)
---

# گزارش §۹ دستور مالک #۸ — ایجنت B

```text
T47 LEASE ACTIVE      : YES → رسید: 06-EVIDENCE/T47-LEASE-ACTIVATION-2026-08-20.md
                       acquire→renew→inspect واقعی؛ lease_id 8d7b0c41…؛
                       خط LEASE_ACCEPTED_BY_A (تحمیل مالک) در AGENT_QUESTIONS ثبت شد.
T48 EVENT-TIME LIVE   : sources_live=2 مستقر (provider/router_request_ts +
                       telegram/telegram_message_date) · اولین رویداد واقعی:
                       provider×1 در spine زنده (schema v2, legacy=0) ·
                       سنجش ۶۰+ دقیقه: زمان‌بندی‌شده برای 15:49 +10
                       (automation-92a6ef41 → T48-EVENT-TIME-MEASUREMENT-2026-08-20.md)
T49 MEMORY READ LIVE  : reads_per_cycle=3 (beat 42943، حلقهٔ زنده) ·
                       read-back=read_ok (تست زندهٔ N→N+1 پاس) ·
                       degraded events=0 · فایل تلمتری:
                       _ops/state/pulse/memory-read-latest.json
T50 RECEIPT FIELDS    : DONE — task_id/run_id/attribution در CostReceiptAdapter +
                       اتصال در model_router (task از caller، run از OCTOPUS_RUN_ID) ·
                       تست‌ها ۴/۴ + regression ۱۳/۱۳ سبز؛ ردیف‌های زندهٔ جدید
                       فیلدها را می‌گیرند (رسیدهای قدیمی دست‌نخورده).
T51 FULL-LOOP CARD    : PREPARED (execution=0) —
                       02-DECISIONS/PRE-REG-FULL-LOOP-FLASH-2026-08-20.md

BITEMPORAL ON REAL    : NOT_RUN — نیازمند پنجرهٔ دادهٔ T48 (≥60m)؛
                       suite ۱۵تایی روی fixture سبز (BITEMPORAL-SPINE-SPEC)؛
                       اجرای روی داده واقعی پس از گزارش سنجش.

LIVE-A : PASS (T47 ✓)
LIVE-B : BLOCKED تا سنجش ۶۵+ دقیقه (producerها زنده‌اند؛ اولین رویداد ثبت شد)
LIVE-C : PASS — شواهد زنده: reads>0 · read-back=PASS · executable=false ·
         crash=0 (یک ریاستارت کنترل‌شده با ~۴ دقیقه شکاف — رکورد پایین)
LIVE-D : BLOCKED (کارت آماده؛ منتظر LIVE-B + امضای Ed25519 جداگانه)
LIVE-E : BLOCKED (طبق دستور)

backup_recovery       : UNKNOWN (تا اعلام مالک — runbook آماده در owner-runbook)
paid calls / AUD      : 0 / 0 (این جلسهٔ دستور #۸)
executable=true       : 0
organism crashes      : 0 (crash نه؛ یک clean-exit + relaunch با ~۴ دقیقه gap — ثبت زیر)
lease held by         : agent-B-ZCode / sess_1d388c34 (در پایان جلسه release شد)
schema version        : events = 2 (dual-write افزودنی؛ ۷,۲۶۷ ردیف legacy نسخهٔ ۱ دست‌نخورده)
GAP-001               : OPEN
commit / branch       : equip/g10-cognition-20260816 (commit همین گزارش)
```

## کدام کد زنده تغییر کرد (همه زیر lease + flag + rollback)

| فایل | تغییر | rollback |
|---|---|---|
| `_ops/spine/event_spine.py` | migration افزودنی ۵ ستون + schema v2 + منطق legacy/clock-skew | ستون‌ها additive؛ کد خواندن legacy سازگار |
| `_ops/spine/spine_adapters.py` | پارامترهای occurred_at/event_time_source/time_precision | صریح؛ حذف پارامتر = رفتار قبل |
| `_ops/cortex/model_router.py` | T50 (task_id/run_id) + T48 producer_1 (spine emit از بلوک رسید) | OCTOPUS_T48_EVENT_TIME=0 |
| `_ops/intel_spine/telegram_adapter.py` | T48 producer_2 (message.date) | OCTOPUS_T48_EVENT_TIME=0 |
| `_ops/cortex/cost_receipt.py` | فیلدهای انتساب (additive) | — |
| `_ops/organism.py` | T49 tick خواندن حافظه (فقط‌خواندنی) | OCTOPUS_WIRE_MEMORY_READ=0 |
| `_ops/memory_read_loop.py` | SpineReadStore + tick_from_spine | سیم‌نشده به هیچ اثر جانبی |

تست‌های این جلسه: lease ۶/۶ · لنگر ۳/۳ · انتساب ۴/۴ · event-time ۶/۶ ·
memory-loop ۵/۵ + spine suites موجود (۹/۹ و سری single-surface) سبز.

## رکورد صادقانهٔ ریاستارت (T49)

مسیر مارکری STOP+RESTART فرضِ supervisor فعال داشت؛ supervisor واقعی (cmd /c از
۱۱:۴۷) همراه organism خارج شد و ~۴ دقیقه organism پایین ماند (۱۴:۳۳–۱۴:۳۶).
مارکرها ساختهٔ همین پروتکل بودند (قبل از آن organism زنده بود = kill-switch
مالک نبود) → پاک‌سازی مارکرهای خود + relaunch با همان مسیر watchdog.
نتیجه: PID جدید 19736، پورت 8771 زنده، beat جلو می‌رود، تلمتری T49 می‌نویسد.
درس ثبت‌شده: مسیر ریاستارت مارکری فقط با supervisorِ زنده معتبر است؛
دفعهٔ بعد اول supervisor چک شود.

## چه چیزی هنوز فقط پیشنهاد است

کارت LIVE-D (T51) · اجرای suite بitemporal روی دادهٔ واقعی (منتظر پنجرهٔ T48) ·
ریاستارت brain.daemon برای producer_1 در مسیر فراخوان‌هایش (سرپرست آن
`launch5.cmd` نامشخص است — عمداً ریاستارت نشد؛ ریسک STOP بدون بازیافت) ·
آپگرید producer_1 به `created` خود provider (ساعت سرور واقعی) · آداپتور
vault_bridge برای memory_read_loop (فعلاً spine-backed).

## پیش‌بینی مراحل بعد (خواستهٔ مالک)

۱. **~15:49 امروز:** گزارش سنجش T48 می‌رسد. سناریوی محتمل: provider چند ده
رویداد (فراخوان‌های خودکار organism) با stdev بالا؛ telegram احتمالاً صفر یا
کم (فراخواننده‌اش ممکن است کد قدیم داشته باشد) → LIVE-B یا PASS مشروط یا
«منبع دوم نیازمند ریاستارت daemon/پیام تلگرامی». اگر پیام تلگرامی بدهید،
producer_2 همین امروز data می‌سازد.
۲. **پس از LIVE-B=PASS:** اجرای suite پانزده‌تستی روی دادهٔ واقعی spine
(read-only wrapper) → اگر پاس، اولین بار «حافظهٔ دوزمانیِ زنده» قابل ادعاست
(VERIFIED_BITEMPORAL مسیرش باز می‌شود).
۳. **امضای کارت LIVE-D توسط مالک (Ed25519):** دوازده task واقعی، سقف AU$0.50 —
اولین حلقهٔ کامل شناختی با مدل واقعی از این مسیر می‌گذرد.
۴. **LIVE-E** همچنان دست مالک: یک اقدام کم‌خطر برگشت‌پذیر با dry-run و
تأیید موردی. GAP-001 تا آن‌جا باز می‌ماند.
۵. ریسک‌های پیش‌رو: daemon قدیمی (producer نیمه‌فعال) · وابستگی
رویدادهای telegram به پیام واقعی · supervisorهای ناشناخته برای ریاستارت‌های
آینده (درس امروز ثبت شد).
