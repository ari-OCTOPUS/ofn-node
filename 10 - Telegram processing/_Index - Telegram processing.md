---
type: moc
status: active
tags: [telegram, inbox, pipeline]
created: 2026-07-03
updated: 2026-08-03
---

# ایندکس Telegram processing

> ایستگاهِ پردازشِ پیام‌های تلگرام. ‏۲۰۲۶-۰۸-۰۳ با واقعیت تراز شد: این نوت تا
> امروز `status: paused` بود و می‌گفت «فعلاً خالی؛ نقطهٔ شروع» — در حالی که لولهٔ
> capture ماه‌هاست زنده است و پوشهٔ `Raw/` نوتِ واقعیِ مالک دارد.

## قوانین (اول این دو)

- [[10 - Telegram processing/SOP|SOP]] — الگوریتمِ **واقعیِ** capture: یک نوت
  به‌ازای هر پیام، dedup ِ خودکار، پنج `kind`، ack ِ متنی. لنگرها نامِ نمادِ
  `capture.py`اند.
- [[10 - Telegram processing/ROUTING|ROUTING]] — مسیریابیِ **سه‌لایه**: گیتِ
  ورودی (`input_surface_policy`) · محتوا (`capture.classify`/`route`) · ریتمِ
  خروجی (`hold_policy` با SEND/DIGEST/HOLD).
  ⚠️ جدولِ هشتگیِ قدیمی (`#paint`، `IDEA:`، …) **هرگز پیاده نشد** و در پیوستِ
  همان سند به‌عنوان منسوخ نگه داشته شده — مالک لازم نیست هشتگ بزند.

## عملیات

- [[10 - Telegram processing/JOURNEY-RUNBOOK-2026-07-31|JOURNEY-RUNBOOK]] — سفرِ
  پذیرشِ ۶ساعتهٔ بدونِ ناظر (۱۳ فاز، دکترینِ سه‌حالتی).
- [[10 - Telegram processing/2026-07-31 2245 کارنامه سفر پذیرش|کارنامهٔ سفرِ پذیرش]] — ✅۱ · 🟢۹ · 🔴۰ · ⌛️۳.
- منشورِ UI و سیاستِ سطح (DM در برابر گروه): [[../_ops/telegram_contract/TG-UI-CHARTER-2026-07-31|TG-UI-CHARTER]].

## `Raw/` — ورودیِ خام

یک نوت به‌ازای هر پیام: `YYYY-MM-DD HHmm <slug>.md` با متادیتا در **فرانت‌متر**
(`message_id`/`chat_id`، و برای رسانه `file_id`/`duration`/`transcribed_by`/
`transcript_secs`). آرشیوِ دائمی است — هرگز حذف نمی‌شود، فقط برچسب می‌خورد.

🔴 **گپِ ثبت‌شده:** عکس فقط به‌صورت `[photo]` ثبت می‌شود — نه فایل بایگانی
می‌شود نه `file_id` می‌گیرد، پس در vault گم است (ویس سالم است). ردیفِ B4 در
[[../_ops/REPAIR-PLAN-2026-08-03|پلنِ رفع]].

## لاگ‌های تلگرامِ پروژه‌ها

[[03 - Projects/Lead-نقاشی/Lead-نقاشی|Lead-نقاشی]] · [[03 - Projects/Mining/Mining|Mining]] · [[03 - Projects/Crypto - etoro/Crypto - etoro|Crypto - etoro]] · [[03 - Projects/Accounting/Accounting|Accounting]] · [[03 - Projects/اونلی فنز/اونلی فنز|اونلی فنز]] · [[07 - Knowledge/هیپنوتیزم  و خودآگاهی/هیپنوتیزم و خودآگاهی|هیپنوتیزم و خودآگاهی]]

## نوت‌های مرتبط

- [[01 - Dashboard/Home|Home]] · [[01 - Dashboard/HANDOFF|HANDOFF]]
- [[10 - Telegram processing/گزارش پردازش ChatExport 2026-07-03|گزارش پردازش ChatExport 2026-07-03]] (تاریخی)
