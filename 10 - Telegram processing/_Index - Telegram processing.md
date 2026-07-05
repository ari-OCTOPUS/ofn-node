---
type: moc
status: paused
tags: [telegram, inbox, pipeline]
updated: 2026-07-03
---

# ایندکس Telegram processing

> ایستگاه پردازش خروجی‌های تلگرام — پیام‌های خام اینجا تکه‌تکه، خلاصه و به نوت پروژه درست منتقل می‌شوند. فعلاً خالی؛ این نوت نقطه شروع است.

## نوت‌های این بخش

- [[10 - Telegram processing/SOP|SOP]] — الگوریتم پردازش هر پیام (مشترک Claude و ربات architect)
- [[10 - Telegram processing/ROUTING|ROUTING]] — جدول مسیریابی اعلانی (هشتگ/کلیدواژه → مقصد)
- [[10 - Telegram processing/گزارش پردازش ChatExport 2026-07-03|گزارش پردازش ChatExport 2026-07-03]]

## جریان پیشنهادی

1. خروجی خام تلگرام → `00 - Inbox` (یا مستقیم اینجا).
2. تفکیک بر اساس پروژه → append به لاگ تلگرام همان پروژه (مثل [[03 - Projects/Mining/Mining|Mining]]).
3. نکته‌های ماندگار → نوت دانش در `07 - Knowledge` یا نوت پروژه.
4. فایل پردازش‌شده از اینجا خارج شود — این پوشه باید معمولاً خالی باشد.

## لاگ‌های تلگرام موجود

- [[03 - Projects/Lead-نقاشی/Lead-نقاشی|Lead-نقاشی]] · [[03 - Projects/Mining/Mining|Mining]] · [[03 - Projects/Crypto - etoro/Crypto - etoro|Crypto - etoro]] · [[03 - Projects/Accounting/Accounting|Accounting]] · [[03 - Projects/اونلی فنز/اونلی فنز|اونلی فنز]] · [[07 - Knowledge/هیپنوتیزم  و خودآگاهی/هیپنوتیزم و خودآگاهی|هیپنوتیزم و خودآگاهی]]

## نوت‌های مرتبط

- [[01 - Dashboard/Home|Home]]
