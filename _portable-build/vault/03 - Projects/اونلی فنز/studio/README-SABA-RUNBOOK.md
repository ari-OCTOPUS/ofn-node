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
python3 -m unittest test_saba_studio -v      # باید ۱۵/۱۵ سبز باشد
```

## گام ۱ — Shadow-mode (هفتهٔ اول، بدون تلگرام)
```
python3 saba_studio.py     # بدون env → stdin؛ منو را چاپ می‌کند، متن/دستور بزن
```
جریان‌ها را امتحان کن: `/start` · `/new` · تایپ عنوان · self-cert با `/faceless` + `/feet` + `/no_explicit` + `/18` · `/done` · `/drafts` · `/cap` · `/halt` · `/resume`.

در shadow-mode بدون inline keyboard، aliasهای متنی کار می‌کنند: `/new`, `/drafts`, `/today`, `/cal`, `/more`, `/trend`, `/ppv`, `/stats`, `/inbox`, `/rules`, `/brief`, `/cap`, `/scope`, `/cancel`, و self-cert aliases: `/faceless`, `/feet`, `/no_explicit`, `/18`, `/done`.

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

## سیم‌کشی با اپراتور/لنگر (خودکار، فایل‌محور)
- درفت‌های Creator → `studio/drafts.json` → اپراتور در لنگر با `/saba` و `/status` می‌بیند.
- اعلان‌های Creator (توقف/محدوده/برگشت) → `studio/to_ari.json` → لنگر `/saba`.
- گزارش/جواب اپراتور به Creator → اپراتور در `studio/for_saba.json` یک آیتم `{"date","text"}` اضافه می‌کند → Creator در «📬 پیام‌های اپراتور» می‌بیند.
- ظرفیت هفتگی Creator → `studio/capacity.json` → لنگر می‌خواند.

## قواعد ثابت
- فقط به chat-id صبا جواب می‌دهد؛ غریبه = سکوت.
- هیچ رسانه‌ای وارد بات نمی‌شود؛ فقط عنوان/متن.
- هیچ پست/DM/پرداخت؛ همه‌چیز draft برای تأیید اپراتور.
- ✋ `/halt` هر لحظه؛ فایل `HALT` را دستی هم می‌توان ساخت/پاک کرد.
- محدودهٔ Creator حرفِ آخر است؛ تنگ‌کردنش فوری اعمال و به اپراتور اعلام می‌شود.
