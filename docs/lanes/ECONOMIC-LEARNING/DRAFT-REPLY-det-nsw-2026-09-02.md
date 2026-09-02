# DRAFT REPLY — amprocurement@det.nsw.edu.au (owner ruling 3, 2026-09-02)

> **وضعیت: پیش‌نویس برای بازبینی و ارسالِ خودِ مالک. این سیستم هیچ‌چیز نمی‌فرستد.**
> منبع: inbound واقعی 2026-09-02T01:30:25Z (painting.sqlite، وضعیت needs_reply).
> متن ذخیره‌شده در runtime ناقص است («As I am locating you…» قطع شده) — متن کامل در
> mailbox است؛ مالک قبل از ارسال، ایمیل اصلی را کامل بخواند.

## زمینه (از رسید)

- ارسال ما: initial-intro quote-card بدون قیمت، 2026-09-01T12:15:27Z (QT-20260902-001، fingerprint 47937f8bb0d2…)
- پاسخ آنها: «Good Morning — Thank you for your interest in working with the NSW Department of Education. As I am not locating you [متن قطع…]»
- قرینهٔ محتمل: در رجیستری تأمین‌کننده (buy.nsw vendor record / SCM prequalification) ما را پیدا نمی‌کنند — پرسش کلاسیک پیش‌نیاز SCM0256.

## پیش‌نویس پاسخ (جای‌خالی‌ها فقط با دادهٔ واقعی مالک پر شوند)

```
Subject: RE: Painting quote — Education sites

Good morning,

Thank you for your reply and for the opportunity to clarify.

Our details for your supplier records:

- Business name: [LEGAL BUSINESS NAME]
- ABN: [ABN]
- Contact: [NAME] · [PHONE] · [EMAIL]
- Insurance: Public Liability $[X]m (certificate available on request)
- We are happy to complete any vendor registration or prequalification
  step you require (e.g., buy.nsw supplier profile / SCM0256
  prequalification scheme for painting services).

We hold experience in [1–2 SHORT FACTS — ONLY REAL REFERENCES] and can
provide site-visit availability at short notice across Sydney metro.

Please let me know which registration path you prefer and we will
complete it the same day.

Kind regards,
[NAME]
[BUSINESS NAME] · [PHONE]
```

## یادداشت اقتصادی (اتصال به حلقهٔ یادگیری)

- این inbound زنجیرهٔ dept-of-education را از RESPONSE_SIGNAL به «پاسخ نیازمند-اقدام انسانی» برد — بدون اقدام مالک، سیگنال سرد می‌شود.
- اگر به ثبت تأمین‌کننده منجر شود، حلقهٔ «response → quote(priced) → payment» باز می‌شود — اولین مسیر واقعی برای رسید پرداخت مستقل (رأی ۶: رسید مالک + SHA256).
- پیش‌نیاز پیشنهادی بعدی (فقط با رأی مالک): پر کردن priced/total_aud برای QT بعدی — کارت قیمت‌دار نرخ رسمی.
