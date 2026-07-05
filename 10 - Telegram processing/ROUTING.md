---
type: reference
status: active
tags: [telegram, pipeline, routing]
created: 2026-07-03
updated: 2026-07-03
---

# ROUTING — جدول مسیریابی پیام تلگرام

> جدول اعلانی که کد ربات architect می‌خواند؛ الگوبرداری از مدل distribution-rule پلاگین Telegram Sync، بدون خود پلاگین. قاعده‌ها به ترتیب چک می‌شوند؛ اولین انطباق برنده است.

## امنیت

فقط پیام‌های user ID مالک (whitelist در config ربات) مجاز به trigger نوشتن‌اند. بقیه: ثبت در لاگ ربات، بدون write.

## قاعده‌ها

| # | فیلتر | مقصد | حالت |
|---|---|---|---|
| 1 | `#paint` یا `#نقاشی` | لاگ تلگرام Lead-نقاشی | APPEND |
| 2 | `#ziman` یا `#زیمان` | لاگ تلگرام Ziman Galerry (در صورت نبود، بساز از template) | APPEND |
| 3 | `#mining` یا `#ماینینگ` | لاگ تلگرام Mining | APPEND |
| 4 | `#crypto` یا `#کریپتو` | لاگ تلگرام Crypto - etoro | APPEND |
| 5 | `#acc` یا `#حسابداری` | لاگ تلگرام Accounting | APPEND |
| 6 | `#architect` | لاگ architect | APPEND |
| 7 | `#fusion` یا `#فیوژن` | لاگ هیپنوتیزم و خودآگاهی | APPEND |
| 8 | `TODAY:` / `امروز:` | تسک `- [ ]` در PROJECT.md پروژه ذکرشده (پیش‌فرض: Inbox) | APPEND |
| 9 | `IDEA:` / `ایده:` | نوت جدید در `00 - Inbox` با `status: idea` | CREATE |
| 10 | `RESEARCH:` / `تحقیق:` | stub تحقیق در `00 - Inbox` | CREATE |
| — | catch-all | `Raw/YYYY-MM-DD.md` | APPEND |

## قواعد ساخت نوت (حالت CREATE)

- نام: `YYYY-MM-DD HHmm <چهل حرف اول پیام>.md` — تصادم‌ناپذیر.
- فرانت‌متر از `_Templates` + متادیتای پیام (`chat_id`/`message_id`/`sender` در بدنه).
- dedup با `message_id` قبل از هر write (رجوع: [[10 - Telegram processing/SOP|SOP]]).

<!-- fallback آینده: پل n8n/webhook برای فرار از پنجره ۲۴h — همین قالب نوت + همین dedup را نگه دارد تا تعویض‌پذیر بماند. -->
