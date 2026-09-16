---
title: O-5 PayPal Invoice drafts 2026-09-17 (owner card: «آماده کن»)
updated: 2026-09-17T06:40:00Z
tags: [octopus, o5, paypal, invoice, revenue]
---

# پیش‌نویس فاکتورهای PayPal — هر دو بیزینس (O-5 = APPROVED)

رویهٔ اجرا (۳ کلیک، حساب PayPal دست مالک است):
`PayPal → Invoicing → Create invoice → متن زیر → Send → شمارهٔ INV-… را در همان کارت/چت بفرست`
ورودی لجر: `payout_id` بومی PayPal است؛ لِین فقط شمارهٔ INV و مبلغ را ثبت می‌کند.

---

## ۱) Ziman Gift — فاکتور فروشگاهی

```
Business:     Ziman Gift (ziman-gift.com.au) — Sydney, NSW
Bill to:      <نام و ایمیل مشتری>
Invoice #:    (PayPal خودش می‌دهد)
Item:         <نام محصول از شیت PRODUCT-SHEET-20260917>
Qty:          1
Amount:       A$<قیمت محصول>
Shipping:     A$20.00 (flat-rate Australia-wide)
Tax/GST:      طبق تنظیم PayPal (GST در checkout نمایش داده می‌شود)
Memo:         Handmade in Sydney. Made to order — allow 2–4 business days."
Due:          Payment due on receipt
```
نکته: برای سفارش تستی CHECKOUT-1 هم اگر خواستید از همین قالب استفاده کنید (بدون ارسال).

## ۲) Painting (بیزینس رنگ) — فاکتور دپازیت/کوت

```
Business:     <نام حقوقی کسب‌وکار رنگ>  ← هنوز در هیچ سندی تثبیت نشده؛ اگر نام دقیق بدهید همین‌جا می‌نویسم
Bill to:      <نام مشتری از لیدِ برنده (مثلاً Absolute Strata)>
Item:         Interior painting — <آدرس ساختمان> — deposit
Description:  <متراژ> m² × A$<نرخ توافقی ۱۵–۶۰> = A$<مبلغ کل>
Deposit:      A$<۲۵–۴۰٪ کل> (توافقی؛ مانده پس از اتمام)
Memo:         Deposit secures the booking date; remainder invoiced on completion.
Due:          Deposit due within 7 days to hold the date
```
قاعدهٔ نرخ (از web_rate_hunt خود ارگانیسم): **A$15–60/m²، حداقل A$60**.

## نگاشت به لجر (یک ریل، یک ledger)

- ردیف لجر بعد از پرداخت: `kind=verified_settlement | provider=paypal | payout_id=<PayPal transaction id> | amount_aud | invoice_id=INV-…`
- تا وقتی رسید PayPal نیامده، وضعیت `REPORTED_NOT_VERIFIED` می‌ماند (قانون VERIFIED_CASH).
