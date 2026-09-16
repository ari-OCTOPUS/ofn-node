---
tags: [ofn, operations, revenue, checklist]
updated: 2026-08-11
---

# چک‌لیست هفتهٔ درآمد — اجرا روی OFN

**پیوندها:** [[REVENUE-STAGES]] · [[PILOT-14DAY]] ·
[[docs/architecture/DECISION-open-gates|گیت‌های موقت]] ·
[[docs/runbooks/SECRET-ROTATION|چرخش راز]] · [[HANDOFF]] · [[DECISIONS|O-5]]

این چک‌لیست همان [[REVENUE-STAGES|نقشهٔ مراحل درآمد]] را عملیاتی می‌کند.
فروش کاملاً خودکار هدف این هفته نیست — اولین پول دستی واقعی است.

## ۰) احکام مالک (قبل از سنجش)

در پنل مالک → **پایلوت — آستانه‌ها و پرداخت**:

| فیلد | پیش‌فرض سند | کار تو |
|---|---|---|
| min listings / inquiry / payment | ۳ / ۱ / ۱ | فقط اگر می‌خواهی سخت‌تر کنی عوض کن |
| روش پرداخت lead | `unset` | یکی از payid / bank_transfer / cash / stripe |
| روش پرداخت ziman | `unset` | معمولاً payid یا cash |
| روش پرداخت studio | `unset` | یا funnel به دو تای بالا |

تا وقتی payment = `unset` است، گزارش پایلوت می‌گوید ریل پرداخت اندازه‌گیری نشده.

```bash
# خواندن از CLI
python3 - <<'PY'
from ofn import config
from ofn.adapters.pilot_thresholds import as_dict, load
print(as_dict(load(config.load().state_dir)))
PY
```

## ۱) Painting — P0→P1 (نزدیک‌ترین پول)

- [ ] عباس ۷ لید باز را در `lead.html` ببیند
- [ ] برای هر لید: موعد پیگیری + «الان تماس گرفتم»
- [ ] هشدار duplicate را بخواند قبل از تماس دوباره
- [ ] quote/پاسخ → تأیید تو → ثبت انجام دستی
- [ ] با اولین پیش‌پرداخت واقعی: **ثبت پیش‌پرداخت/مبلغ** (status=won + cents)
- [ ] پنل مالک «امروز» → پیگیری معوق و booked $

APIها:
- `POST /api/v1/painting/leads/{id}/follow-up`
- `POST /api/v1/painting/leads/{id}/touch`
- `POST /api/v1/painting/leads/{id}/booked`
- `GET  /api/v1/painting/duplicates/{id}`

## ۲) GiftMesh — Z0

- [ ] جواب factهای GST / delivery / days_before_worry در پنل زیمان
- [ ] ۳ قطعه واقعی با عکس و قیمت → `for_sale`
- [ ] کانال فروش از `direct` / `cash` / `payid` (کارمزد صفر در پک)
- [ ] برای Instagram/Etsy: آری درصد را در `packs/ziman.yaml` اضافه کند
- [ ] «بستهٔ آگهی» → کپی و پست دستی
- [ ] «رسید فروش ثبت کن» با مبلغ واقعی

## ۳) Studio — S0

- [ ] در پنل مالک: سوژه + release برای `telegram_channel`
- [ ] سبا: draft + عکس + felt/route
- [ ] صف outbox → تأیید تو
- [ ] یا ثبت انجام دستی، یا **آزمایش خشک تلگرام** سپس ارسال واقعی
- [ ] fact پیش‌شرط انتشار (`ops.publication_precondition`) از مسیر سؤالات پک

## ۴) گیت‌ها و رازها (قرمز)

مهلت: **۲۰۲۶-۰۸-۱۷ UTC**

- [ ] چرخش رازها طبق `docs/runbooks/SECRET-ROTATION.md`
- [ ] بعد از چرخش: `OFN_KEEP_GATES_OPEN=1` فقط اگر عمداً باز بمانند
- [ ] بدون چرخش: از آن تاریخ `config.load()` خودش `secret_rotation` و `partner_precondition` را می‌بندد

## ۵) سنجش روزانه

```bash
python3 tools/pilot_report.py --days 1
# خروجی را در docs/operations/pilot-daily/YYYY-MM-DD.txt بگذار
```

موفقیت پایلوت = زنجیرهٔ تولیدی listing→inquiry→order→payment با آستانه‌های ثبت‌شده — نه seed.
