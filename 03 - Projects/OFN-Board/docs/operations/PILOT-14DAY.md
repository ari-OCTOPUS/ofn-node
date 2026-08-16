---
tags: [ofn, operations, pilot]
aliases: [پایلوت ۱۴روزه, PILOT-14DAY]
updated: 2026-08-11
---

# O12 — پایلوت ۱۴روزه: روز صفر و هر روز

**فاز O12 · تاریخ: ۲۰۲۶-۰۸-۱۰ · نیازمند همکاری واقعی شریک‌ها — آماده شد، اجرا نشد**

**پیوندها:** [[REVENUE-STAGES]] · [[REVENUE-WEEK-CHECKLIST]] · [[HANDOFF]]

آستانه‌های موفقیت از ۲۰۲۶-۰۸-۱۱ در پنل مالک قابل ثبت‌اند
(`GET/POST /api/v1/owner/pilot/config` · فایل `pilot_config.json` زیر
state_dir). پیش‌فرض همان ۳ listing / ۱ inquiry / ۱ payment است؛ روش پرداخت
هر بیزنس تا حکم مالک `unset` می‌ماند و گزارش آن را «اندازه‌گیری‌نشده» می‌نویسد.

## روز صفر — با آری و شریک‌ها (واقعی)

1. **walkthrough واقعی هر پنل** — مالک، عباس (لید)، ملیحه (زیمان)، سبا (استودیو).
2. **پنج سناریوی seeded بدون PII واقعی** — با `tools/seed_pilot.py` (پایین).
3. **screenshot** از هر پنل قبل/بعد.
4. **زمان انجام هر سناریو** — در جدول روز صفر ثبت شود.

## هر روز (خودکار قابل‌اندازه‌گیری)

| شاخص | منبع |
|---|---|
| overdue / manual completion / held-failed | `owner_workboard` + outbox |
| lead response lag | `painting_leads.last_contacted_at` |
| listing readiness + sale receipts | `products` + `product_sale_events` |
| studio blocked reasons | consent gaps + workboard |
| connector freshness | observability |

## هر هفته

- outcome measured · funnel conversion
- کارهای دستی فراموش‌شده · false blocker / unsafe bypass attempt
- partner friction notes (از خود شریک‌ها)

## معیار دقیق موفقیت پایلوت

پایلوت فقط وقتی موفق است که در بازهٔ UTC خواسته‌شده، یک زنجیرهٔ واقعی و
زمان‌مرتب در جدول‌های commerce وجود داشته باشد:

1. دست‌کم **۳ رویداد listing تولیدی**؛
2. دست‌کم **۱ inquiry تولیدی** که به یکی از همان listingها وصل است؛
3. دست‌کم **۱ payment تولیدی** که از راه یک order به همان inquiry وصل است،
   وضعیتش `confirmed` یا `settled` است، `amount_cents > 0` دارد و
   `evidence_digest` آن خالی نیست.

همهٔ حلقه‌ها باید داخل همان بازه باشند و ترتیب
`listing → inquiry → order → payment` را رعایت کنند. پرداخت `refunded` یا
`reversed` موفقیت نیست. شمارنده‌های جداگانه به‌تنهایی کافی نیستند؛ زنجیرهٔ
لینک‌شده لازم است. داده‌های `seed`، `test`، `demo` و `legacy_unknown` هرگز
حساب نمی‌شوند؛ به‌ویژه سناریوهای ساخته‌شده با `tools/seed_pilot.py` فقط برای
walkthrough هستند و هیچ‌وقت معیار پایلوت را پاس نمی‌کنند.

## ابزار

### seeding (بدون PII واقعی)
```bash
python3 tools/seed_pilot.py
```
پنج سناریو: ۲ لید تستی، ۲ قطعهٔ زیمان (یکی for_sale)، ۱ draft استودیو.
همه با نام‌های ساختگی — هیچ دادهٔ واقعی شریک/مشتری.

### tracking
```bash
python3 tools/pilot_report.py --days 3
```
گزارش از store های canonical — هیچ DB موازی. `--days` یک بازهٔ واقعی UTC
می‌سازد و فقط زنجیره‌های commerce داخل همان بازه را می‌سنجد.

---

## روز صفر — ثبت‌شده ۲۰۲۶-۰۸-۱۰ (بعد از بستن P0)

| شاخص | مقدار اندازه‌گیری‌شده | منبع |
|---|---|---|
| لید باز (lead) | ۷ | `painting.list_leads("lead")` — ۲ تای seeded + ۵ قبلی |
| پیگیری معوق | ۰ | `painting.follow_ups_due` |
| قطعهٔ زیمان آمادهٔ لیست | ۲ | `products.list("ziman")` (۵ کل، ۲ ready-to-list) |
| فروش ثبت‌شده | ۰ | `product_sale_events` |
| draft استودیو | ۱ | `studio.drafts("studio")` — pilot-draft-1 |
| pilot تلگرام (فقط-خواندنی) | ✅ کار می‌کند — ۳ آیتم خواند: me/webhook/channel | run زنده با Robo2725_bot |
| پنل‌ها | ۴/۴ HTML واقعی سرو می‌شود (۲۰۰) | panel/ziman/lead/studio |
| معیار موفقیت | زنجیرهٔ تولیدی ۳ listing → ۱ inquiry لینک‌شده → ۱ order → ۱ payment معتبر | جدول‌های commerce در `products.sqlite` |

### گزارش روزانه (خودکار)
```bash
python3 tools/pilot_report.py --days 1
```
هر روز یک بار اجرا شود و خروجی در `docs/operations/pilot-daily/` ثبت شود
(یک فایل در روز، نام `YYYY-MM-DD.txt`) تا روند ۱۴روزه از روی فایل‌ها خوانده
شود، نه از حافظه.
