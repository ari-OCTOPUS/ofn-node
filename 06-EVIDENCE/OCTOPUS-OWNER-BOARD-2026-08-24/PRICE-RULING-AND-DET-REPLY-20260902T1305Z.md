---
type: owner-ruling-execution-receipt
ruling: مالک 2026-09-02 ~13:00Z — «قیمتم خودت بده بچرخه بعدا کالیبره میکنیم تو متوسط سیدنی بگیر دقیق» + دادهٔ شرکت (ABN Lookup) + تلفن‌ها + ۲۵ سال سابقه
executed: 2026-09-02T13:05Z · FILES_I_MERGED=none · ارسال DET همچنان فقط با دست مالک (R3)
---

# ۱ — حکم قیمت (مالک‌مخول، روش‌ثبت)

**روش:** متوسط سیدنی، منبع‌دار؛ کالیبره بعدی با مالک.

| قلم | نرخ (ex GST) | مبنا (متوسط سیدنی) |
|---|---|---|
| رنگ داخلی (دیوار+سقف) | $35/m² | Sydney interior repaint متوسط بازار |
| رنگ بیرونی | $50/m² | متوسط Sydney exterior (پایین‌باند $25–60+، میانگین‌ها $40–70) |
| روزکار/نگهداری | $75/hr | متوسط سیدنی $60–90/hr |

منابع: hipages 2026 cost guide ($40–70/m² خارجی؛ $70–100/hr) · Advance Painting Sydney 2026 ($25–60+/m² خارجی سیدنی) · painters.edu.au ($10–60/m² عمومی؛ $65–95/hr).

**ثبت روی QT-20260902-001 (scope نداشت → کارت معرفی = کارت نرخ + حداقل سفارش استاندارد):**
`total_aud = 600.00` = یک روزکار نقاش ($75 × 8h، ex GST) — «priced» شد تا حلقه بچرخد؛ کالیبره با مالک بعد از scope واقعی.

```
STEP: price-write · MEASURED_AT_UTC: 2026-09-02T13:05Z · SOURCE: sqlite3 board138 painting.sqlite
BEFORE: qt_number=QT-20260902-001 · priced=0 · total_aud=NULL · status=sent · card 5d2620ad…/fp 47937f8b…
WRITE:  UPDATE painting_quotes SET priced=1, total_aud=600.00 WHERE qt_number='QT-20260902-001' AND priced=0  → changes()=1
AFTER:  priced=1 · total_aud=600.0 · status=sent (دست‌نخورده) · scope_json/card_sha256/fingerprint دست‌نخورده
INTEGRITY: PRAGMA quick_check=ok
RECEIPT_TIME: 2026-09-02T13:05Z · VALID_UNTIL: کالیبرهٔ بعدی مالک
verified_payment_count هنوز 0 — قیمت ≠ پرداخت (R6 پابرجا)
```

# ۲ — دادهٔ شرکت (منبع: ABN Lookup استخراج 2026-09-02، دست مالک + تلفن‌ها از مالک)

- نام قانونی: **MASTER PAINTING AND MAINTENANCE AND DESIGN PTY LTD**
- ABN: **46 673 280 030** · ACN: 673 280 030 · Australian Private Company · **GST: Registered** (از 28 Nov 2023) · Active · NSW 2768
- تماس: **0410 609 616** · **0493 577 719**
- سابقه: **۲۵ سال** نقاشی و نگهداری (بیان مالک؛ برای ادعای written referee بعداً از مالک گرفته شود)
- بیمه: جزئیات عددی در هیچ DB بورد نیست («Fully insured, ABN on file» در کارت‌های ارسالی) → در پاسخ: certificates on request — **هیچ عدد بیمه‌ای ساخته نشد**

# ۳ — متن نهایی پاسخ DET (آمادهٔ ارسال توسط خود مالک — R3؛ اول ایمیل اصلی را کامل بخوان)

```
Subject: RE: Painting quote — Education sites

Good morning,

Thank you for your reply and for the opportunity to clarify.

Our details for your supplier records:

- Business name: MASTER PAINTING AND MAINTENANCE AND DESIGN PTY LTD
- ABN: 46 673 280 030 (ACN 673 280 030) — GST registered
- Contact: [NAME] · 0410 609 616 / 0493 577 719
- Experience: 25 years in painting and maintenance across Sydney
- Insurance: Public Liability and Workers Compensation certificates
  available on request
- We are happy to complete any vendor registration or prequalification
  step you require (e.g., buy.nsw supplier profile via Supplier Hub, and
  SCM0256 prequalification under the Painting & Decorating trade category).

Indicative pricing (Sydney market averages, ex GST):
- Interior repaint (walls & ceilings): from $35 per m2
- Exterior repaint: from $50 per m2
- Scheduled maintenance / day works: $75 per hour
  (standard engagement: one painter-day, $600 ex GST)

We can price a trial scope within a few days of receiving details.

Kind regards,
Master Painting and Maintenance and Design Pty Ltd
0410 609 616 · 0493 577 719
```

تنها جای‌خالی: `[NAME]` (نام کوچک مالک) — بقیه کامل است. **ایمیل از mailbox خود مالک ارسال شود؛ هیچ برچسبی عوض نشد، هیچ سیستمی چیزی نفرستاد.**
