# O12 — پایلوت ۱۴روزه: روز صفر و هر روز

**فاز O12 · تاریخ: ۲۰۲۶-۰۸-۱۰ · نیازمند همکاری واقعی شریک‌ها — آماده شد، اجرا نشد**

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

## قانون
**هیچ threshold موفقیتی اختراع نکن.** در روز صفر آری thresholdها را ثبت
کند و تست/گزارش همان‌ها را بخواند. اگر threshold ثبت نشد، پایلوت «اندازه‌گیری
نمی‌شود» می‌گوید — نه عدد جعلی.

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
گزارش از store های canonical — هیچ DB موازی.

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
| threshold موفقیت | ⏳ **منتظر حکم آری** — هیچ عددی اختراع نشد | قانون پایلوت |

### گزارش روزانه (خودکار)
```bash
python3 tools/pilot_report.py --days 1
```
هر روز یک بار اجرا شود و خروجی در `docs/operations/pilot-daily/` ثبت شود
(یک فایل در روز، نام `YYYY-MM-DD.txt`) تا روند ۱۴روزه از روی فایل‌ها خوانده
شود، نه از حافظه.
