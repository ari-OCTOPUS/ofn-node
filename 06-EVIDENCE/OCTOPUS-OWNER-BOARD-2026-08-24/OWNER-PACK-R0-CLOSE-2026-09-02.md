---
title: بستهٔ مالک — R0-CLOSE (یک فایل، همهٔ کلیک‌ها)
created: 2026-09-02T13:35Z · rule: paste-output-back («انگار خرم»)
format: تک‌خط PowerShell بدون گیومهٔ داخلی · شماره‌دار · ❌ نکن‌ها آخر
---

# R0-CLOSE — کارهای فقط-مالک (به ترتیب ارزش)

## ۱) عکس/PDF رسید پرداخت قرارداد Manly را بینداز (سریع‌ترین راه به verified_payment_count=1)
فایل را در این پوشه بگذار (Drag & Drop کافی است):
`C:\Users\Armin\Downloads\` → بعد این یک خط:
```
Copy-Item C:\Users\Armin\Downloads\RECEIPT-FILE.pdf F:\backup\06-EVIDENCE\OCTOPUS-OWNER-BOARD-2026-08-24\payment-receipts\
```
(RECEIPT-FILE.pdf را با نام واقعی فایل عوض کن.) بعدش اسمش را همین‌جا بگو تا با هش R6 (`SHA256(payment_id|amount|currency|received_at|payer)`) تأیید و در لجر ثبتش کنم. **قرارداد ≠ پرداخت؛ فقط رسید واقعی عدد را ۱ می‌کند.**

## ۲) پاسخ نهایی DET را بفرست (از mailbox خودت؛ اول ایمیل اصلی‌شان را کامل بخوان)
متن نهایی (تصمیم: خط بیمه با عدد $۲۰M، امضا بدون نام شخصی — فقط کپی و ارسال):

```
Subject: RE: Painting quote — Education sites

Good morning,

Thank you for your reply and for the opportunity to clarify.

Our details for your supplier records:

- Business name: MASTER PAINTING AND MAINTENANCE AND DESIGN PTY LTD
- ABN: 46 673 280 030 (ACN 673 280 030) — GST registered
- Contact: 0410 609 616 / 0493 577 719
- Experience: 25 years in painting and maintenance across Sydney
- Insurance: Public Liability $20,000,000 per occurrence
  (Allianz, policy 109XN94167COM) — certificate available on request
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

## ۳) این پیام را برای Elahe-z بفرست (تلگرام)
> الهه جان، این PRها منتظر review تو هستند (به همین ترتیب):
> #102 CODEOWNERS (گیت استقلال — مهم‌ترین) · #101 ستون درآمد · #103 sanitize · #73 و #65 (سبز کامل از قبل)
> همه: https://github.com/ari-OCTOPUS/ofn-node/pulls — لطفاً روی HEAD فعلی هرکدام رأی بده.

## ۴) Supplier Hub (هر وقت رسید — بسته در BUYNWS-SUPPLIER-PACK-2026-09-02.md)
https://buy.nsw.gov.au → ثبت‌حساب → بعد درخواست SCM0256 رستهٔ Painting & Decorating.

## ۵) رأی‌های باز (یک‌کلمه‌ای جواب بده همین‌جا)
- V2 درمان یونیت‌ها/پورت‌ها: پس از merge شدن #101 بورد pull می‌خواهد — «بکش»؟
- V5 fast-lane: فعلاً قفل بماند (پیشنهاد) تا V4 (یعنی #102) merge شود.
- مادهٔ ۱۰ (کدنویسی پنل/تلگرام): freeze تا payment=1 (پیشنهاد).

## ❌ نکن
- merge هیچ PRی خودت با حساب aram-ui بدون review الهه (الان enforce_admins=true است ولی عادت را نگه دار)
- ارسال DET توسط هر سیستم/ایجنت — فقط mailbox خودت
- تغییر برچسب Gmailها · روشن‌کردن WAL · restart پروسه‌ها
- مدارک شرکت را در مخزن عمومی GitHub نگذار
