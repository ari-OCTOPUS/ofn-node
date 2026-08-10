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
