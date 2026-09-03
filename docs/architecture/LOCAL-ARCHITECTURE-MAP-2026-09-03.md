# LOCAL-ARCHITECTURE-MAP — ofn-node روی board138، اندازه‌گیری‌شده 2026-09-03 (~20:30 AEST)

> ایجنت مقیم (laptop .191، اکانت ari322). جایگزینِ گزارش‌های غیر-SSH نشست‌های ابری.
> هر بند با فرمان/مسیر. main لحظهٔ نقشه: `6f9298a8` (شامل #150 repair_api و #151 B2B-ingest).

## ۱) وضعیت اجرا روی بورد (پایهٔ deploy بعدی)

```text
BRANCH  = fix/env-independent-tests-20260903 @ 10de2e13   ← «behind-2» نشست‌های ابری غلط بود؛ واقعی = 10 مرج عقب
BEHIND  = 10 (شامل #150 repair_api · #151 B2B-ingest · #146 · #135 · #136)
FAILED  = 0 یونیت · imap: Result=success @10:30:39Z، تایمر فعال (بعدی 10:45Z)
WAL     = 1 (owner-ruling-4gates) · صفر ارسال از 02:00Z دیروز
```
نتیجه: **یک `git pull --ff-only` + daemon-reload** بورد را روی main می‌آورد و repair_api/self_model_producer را روی دیسک می‌آورد (یونیت‌هاشان قبلاً نصب است، فقط ExecStart غایب بود).

## ۲) نقشهٔ مصرف‌کننده‌ها — چی تولید می‌شود و کی می‌خواند (grep روی main)

| تولید | مصرف‌کنندهٔ فعلی | حکم |
|---|---|---|
| events.jsonl (imap/outbound/notify/quote) | doctor.probe_pulse (نبض) + quote_pipeline.extract_m2 (بی‌فراخوان) | نیم‌وصل |
| state/doctor/report.json | owner_absence.py (برای dead-man) | **هیچ رندری برای مالک نیست** — باز |
| state/OWNER-QUEUE.md | فقط خود owner_absence | باز — گلاس/کاکپیت نمی‌خواند |
| claims-ledger.jsonl (شاهد) | هیچ (فقط verify داخلی) | باز — SILENT_FLIP بی‌هشدار |
| لجر یادگیری اقتصادی | telegram_glass.build_learning_snapshot (بی-فراخوان) + کارت کاکپیت (run دستی) | باز |
| repair_api | صفر (تازه مرج شد؛ هنوز روی بورد deploy نشده) | پس از deploy: دکتر→repair می‌بندد |
| SYSTEM-SELF-MODEL.json | کاکپیت v2 ✓ | تولیدش تایمر شد (روی بورد نصب؛ در deploy/ مخزن ثبت نیست) |
| board_events | هیچ فرستنده/گیرنده | قرارداد-فقط (docstring لازم) |
| BrainPort | صفر فراخوان | قفل فوگو-شکل پابرجا |
| ShopifyConnector | صفر ثبت در run.py | سفارش ورودی fail-closed |

## ۳) زیمان (وضعیت پس از #151)
- **تازه**: `tools/` B2B lead ingest — ۸ حساب دستی (strata/commercial/gov) وارد lead-store شد → اولین جریان لیدِ غیر-خودکار.
- برداشت خودکار (#141) هنوز بی-فراخوان (دوقفل)؛ source_registry با رجیستری نود دوقلوست؛ order-ingest: توکن Admin نیست.

## ۴) مش سه‌برد (پس از موج درمان دیروز)
```text
138: inbox 0 · outbox 0 · processed 28,613 · rejected 9 · درین ساعتی فعال
182: inbox 0 · outbox 3 · تایمر witness-send فعال (آخرین 10:00Z) · NATS تک‌کلاینت لوکال
180: outbox 24 (بی-TTL، بی-فرستنده — طراحی فرستنده لازم)
پالس شاهد→۱۳۸: processed/terminal_consumed_no_reply (audit.jsonl seq 152920-21) ✓
```

## ۵) صف کار مرتب‌شده (برای هر ایجنت بعدی)
1. **deploy بورد** (pull ff-only) — همهٔ عضوهای مرج‌شده را زنده می‌کند؛ بدون restart سرویس زنده
2. پالس دکتر در heartbeat (مصرف report.json) + هشدار SILENT_FLIP → owner_notify
3. runner گلاس (پاسخ به شش فرمان) — کلید ۴ سطح بسته
4. ثبت unit فایل‌ها در deploy/ + رفع تسک‌های Observatory/4d روی لپ‌تاپ (SCAN-A:1-3)
5. ziman: ثبت ShopifyConnector + فیدر لجر یادگیری

FILES_I_MERGED=none · additive doc only
