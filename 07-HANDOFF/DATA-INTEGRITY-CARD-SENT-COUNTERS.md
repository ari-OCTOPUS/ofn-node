---
title: کارت صحت داده — ناسازگاری sent_today / sent_total
created: 2026-09-17T07:58:00Z
tags: [octopus, data-integrity, season-meter, funnel]
status: RESOLVED_NAMING_MIGRATION (no history rewritten)
---

# یافتهٔ صحت داده: sent_today=11 > sent_total=3

## ریشه (audit فقط-خواندنی ۲۰۲۶-۰۹-۱۷)

- `sent_today` از **`sent-log.jsonl`** شمرده می‌شود = تعداد **پیام‌های ارسالی
  امروز** (۱۱ ردیف ۲۰۲۶-۰۹-۱۶، همه با `outcome:"sent"` صریح، همگی ۰۰:۰۱:۲۲Z).
- `sent_total` از **state پکت‌ها** شمرده می‌شود = تعداد **پکت‌هایی که lifecycle
  state=SENT دارند** (۳).
- یعنی دو **واحد متفاوت** (پیام در برابر پکت/لید در حالت SENT) با نام‌های
  مبهم — باگ شمارش نبود؛ باگ نام‌گذاری بود. ضمن audit یک باگ واقعی کوچک هم
  پیدا شد: شرط `.get("outcome","sent")` ردیف‌های بدون outcome را بی‌صدا «sent»
  می‌شمرد.

## اینوارینت ثبت‌شده (طبق رأی مالک)

اگر هر دو شمارندهٔ ارسال بودند: `sent_total >= sent_today >= 0` باید برقرار
می‌بود؛ **نقض شد (۱۱ > ۳)** و همین نقض، اختلاط واحد را آشکار کرد. پس از
مهاجرت نام‌ها، مقایسه فقط هم‌واحد انجام می‌شود.

## اصلاح (پچ کوچک دارای pre-image + migration note؛ بدون بازنویسی receiptها)

- pre-image: `revenue_state.py.pre-meter-naming-20260917`
- نام‌های جدید: `messages_sent_today` (پیام) و `packets_in_sent_state` (پکت).
- باگ default-outcome رفع شد (فقط `outcome=="sent"` صریح شمرده می‌شود؛ عدد
  امروز تغییری نکرد چون همهٔ ردیف‌ها صریح بودند).
- رسید `METER_NAMING_MIGRATION` (اسکیمای `octopus.funnel-integrity.v1`) با
  snapshot پیش/پس به `receipts.jsonl` **append** شد — هیچ receipt قدیمی
  بازنویسی نشد.
- **تا تثبیت معناشناسی، هیچ نرخ تبدیل یا ادعای عملکرد درآمدی منتشر نمی‌شود.**
  `verified_cash=0.0` بدون تفسیر خوش‌بینانه باقی می‌ماند.

## متر جدید (زنده، 2026-09-16T21:34:18Z)

```json
{
 "leads_total": 97,
 "emails_known": 68,
 "contactable_phone_only": 29,
 "verified_cash": 0.0,
 "messages_sent_today": 11,
 "packets_in_sent_state": 3
}
```

## صف phone_only (طبق رأی، بند ۴)

`phone-only-queue.jsonl` — ۲۹ لید بدون هیچ ایمیل قابل‌یافت، با
`channel=phone_only` و یادداشت صریح: **هیچ ارسال/تماس/اثر خارجی بدون
کارت/consent/gate مربوطه ممنوع**. صف جدا از لجر ایمیل نگهداری می‌شود.
