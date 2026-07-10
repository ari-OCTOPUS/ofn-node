---
type: runbook
project: "[[PROJECT]]"
tags: [project-f, studio, runbook, ops]
up: "[[SABA-STUDIO-SPEC]]"
updated: 2026-07-10
---

# 🎬 استودیوی صبا — Runbook (گیت‌دار)

> جدا از لنگر. توکن و chat-id کاملاً مستقل. propose-only، صفر رسانه/PII.

## گام ۰ — تست ($0، بدون شبکه)
```
cd "<پوشهٔ پروژه>/studio"
python3 -m unittest test_saba_studio -v      # باید ۱۰/۱۰ سبز باشد
```

## گام ۱ — Shadow-mode (هفتهٔ اول، بدون تلگرام)
```
python3 saba_studio.py     # بدون env → stdin؛ منو را چاپ می‌کند، متن/دستور بزن
```
جریان‌ها را امتحان کن: `/start` · تایپ عنوان بعد از «ثبت» · `/halt` · `/resume`.

## گام ۲ — اتصال تلگرام (پس از تأیید)
1. صبا (یا آری برای او) یک bot جدا در BotFather بسازد — **غیر از bot لنگر**. نام بی‌ربط به برند.
2. chat-id صبا را بگیر.
3. env:
```
export TELEGRAM_SABA_BOT_TOKEN="111:AAA"     # جدا از لنگر
export TELEGRAM_SABA_CHAT_ID="<chat-id صبا>"
python3 saba_studio.py
```
4. (اختیاری) اگر مغز وصل شد، `/brief` از ThinkingBrain تغذیه می‌شود.

## سیم‌کشی با آری/لنگر (خودکار، فایل‌محور)
- درفت‌های صبا → `studio/drafts.json` → آری در لنگر با `/saba` و `/status` می‌بیند.
- اعلان‌های صبا (توقف/محدوده/برگشت) → `studio/to_ari.json` → لنگر `/saba`.
- گزارش/جواب آری به صبا → آری در `studio/for_saba.json` یک آیتم `{"date","text"}` اضافه می‌کند → صبا در «📬 پیام‌های آری» می‌بیند.
- ظرفیت هفتگی صبا → `studio/capacity.json` → لنگر می‌خواند.

## قواعد ثابت
- فقط به chat-id صبا جواب می‌دهد؛ غریبه = سکوت.
- هیچ رسانه‌ای وارد بات نمی‌شود؛ فقط عنوان/متن.
- هیچ پست/DM/پرداخت؛ همه‌چیز draft برای تأیید آری.
- ✋ `/halt` هر لحظه؛ فایل `HALT` را دستی هم می‌توان ساخت/پاک کرد.
- محدودهٔ صبا حرفِ آخر است؛ تنگ‌کردنش فوری اعمال و به آری اعلام می‌شود.
