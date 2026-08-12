---
type: spec
project: "[[03 - Projects/اونلی فنز/PROJECT]]"
status: built (activation gated — BotFather دست صبا/آری + shadow هفته)
created: 2026-07-10
created_by: agent (Claude Fable 5)
relates_to: "content_studio.py (موتور) · [[PROJECT-F-BRAIN-SPEC]] · [[architecture-blueprint-2026-07-04]] §۳/§۷ · langar/ (کاکپیت آری) · CLAUDE.md"
tags: [project-f, saba, studio, telegram, ui, hitl]
aliases: ["Saba Studio", "استودیوی صبا", "Studio"]
---

# استودیوی صبا (SABA-STUDIO) — رابط تلگرامیِ جدا از لنگر

> رابط تلگرامیِ **خوشگل، ساده و کارآمد** برای صبا (تولید محتوا). جدا از لنگر (کاکپیت آری). لحن گرم و انسانی؛ boundary-first؛ propose-only؛ صفر رسانه/PII.

## ۱. سیم‌کشی با معماری کل (blueprint §۳ two-brain · BRAIN-SPEC §۱)
```
🎬 صبا (saba_studio.py) ──submit──▶ studio/drafts.json ──┐
        │  ▲                         (موتور: ContentStudio)│
   ✋HALT │  │ 📬 for_saba.json                            ▼
        │  └───────────────  ⚓ لنگر (آری): /saba /drafts /status
        └──── to_ari.json (اعلان‌های صبا) ────────────────┘
                    اعمال verdict = دستیِ آری، درون‌پلتفرم
```
- **منبع حقیقت مشترک = `ContentStudio`** (drafts.json + config.json). کانِن دوم ساخته نشد.
- **Creator→Operator:** درفت‌ها به `drafts.json` (pending) → لنگر با `/saba` و `/status` می‌بیند؛ اعلان‌های Creator (توقف/تنگ‌کردن محدوده/برگشت) به `to_ari.json`.
- **Operator→Creator:** اپراتور/لنگر به `for_saba.json` می‌نویسد (گزارش هفتگی، جواب) → Creator در «📬 پیام‌های اپراتور» می‌بیند و mark-read می‌شود.
- **مرز مشترک:** `HALT` فایل — صبا با ✋ می‌سازد؛ هم بات خودش هم لنگر (`/saba`,`/status`) آن را می‌بینند.
- **ظرفیت:** `capacity.json` (ساعت هفتگی صبا) → لنگر می‌خواند و در برنامه‌ریزی (delivery-rate G1) لحاظ می‌شود.

## ۲. صفحه‌ها (UX)
منوی سه‌سطحی با inline-keyboard، HTML غنی، microcopy گرم فارسی:
- 🏠 **خانه:** سلامِ زمان‌آگاه + وضعیت سریع (درفت منتظر، تم هفته، ظرفیت، پیام خوانده‌نشده).
- 📤 **ثبت ایده/درفت:** جریان چندمرحله‌ای (عنوان → toggleهای self-cert چهارگانه → ثبت نهایی) → `ContentStudio.submit_draft`.
- 📋 **درفت‌های من:** فقط pendingها.
- 🌟 **امروز چیکار کنم؟:** تمرکز تقویم + ایدهٔ سریع + یادآور مرز (فقط پا).
- 🗓 تقویم · 🔎 ترند · 💡 پلن PPV · 📈 نتیجه‌ها (تجمیعی، صفر PII).
- 🫶 **ظرفیت من:** اعلام ساعت هفتگی (عدد فارسی/انگلیسی) → capacity.json.
- 📬 **پیام‌های اپراتور** (inbox) · ✋ **محدودهٔ من** (بیانیهٔ مرز + تنگ‌کردنِ فوری + /halt).
- Shadow-mode بدون تلگرام با aliasهای متنی کار می‌کند: `/new`, `/drafts`, `/today`, `/cal`, `/more`, `/trend`, `/ppv`, `/stats`, `/inbox`, `/rules`, `/brief`, `/cap`, `/scope`, `/cancel`, و self-cert: `/faceless`, `/feet`, `/no_explicit`, `/18`, `/done`.
- 🔒 قول‌های ما · 🧠 بریف هفته (از مغز اگر وصل باشد).

## ۳. خطوط قرمز کدشده
فقط chat-id Creator (غریبه=سکوت؛ shadow-mode stdin با chat=0 مجاز است) · صفر متد رسانه‌ای (photo/video/document اصلاً وجود ندارد) · propose-only، دوکلیده (submit→اپراتور) · self-cert اجباری (faceless·feet_only·no_explicit·over_18) وگرنه drop · **محدودهٔ Creator مقدمِ مطلق:** ✋ توقفِ پایدار + تنگ‌کردنِ لحظه‌ای که فوراً به اپراتور می‌رسد · صفر مذاکرهٔ پرداخت · geo/opsec: هیچ اسم/شهر در متن.

## ۴. تست‌ها (test_saba_studio.py — ۱۵/۱۵ هدف، $0 آفلاین)
سکوتِ غریبه · خانه/منو · halt پایدار + اعلانِ اپراتور + resume · درفت فقط-pending · جریان کامل ثبت (cert→done) · بلاکِ cert ناقص · ظرفیت persist با ارقام فارسی/عربی · تنگ‌کردن محدوده (لاگ+اعلان) · inbox mark-read · صفر متد رسانه · shadow-mode chat=0 · aliasهای متنی · self-cert متنی · halt fail-closed تا resume. **پل لنگر↔استودیو هم با تست قرارداد جدا تأیید شد.**

## ۵. فعال‌سازی (گیت‌دار)
Runbook: [[studio/README-SABA-RUNBOOK|README-SABA-RUNBOOK]]. ساخت bot در BotFather = اکشن بیرونی (دست انسان). طبق منشور: هفتهٔ اول shadow-mode (stdin، بدون تلگرام)، بعد اتصال با `TELEGRAM_SABA_BOT_TOKEN`/`TELEGRAM_SABA_CHAT_ID`. **بات Creator و بات لنگر توکن و chat-id کاملاً جدا دارند** (blueprint §۷.۲).

## ۶. تفاوت با نسخهٔ قبلی (studio_telegram_v3.py)
v3 موجود می‌ماند (سازگار با همان موتور). این نسخه: UX گرم‌تر و boundary-first، جریان ثبت درفت چندمرحله‌ای با toggle، ظرفیت هفتگی، inbox دوطرفهٔ آری، و **سیم‌کشیِ صریحِ handoff با لنگر**. برای استفادهٔ عملی این نسخه توصیه می‌شود؛ v3 به‌عنوان fallback.
