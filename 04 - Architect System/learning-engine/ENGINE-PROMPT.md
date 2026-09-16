---
type: prompt
status: draft
tags: [learning-engine, self-mutation, mycelium]
created: 2026-07-06
updated: 2026-07-06
---

> [!warning] وضعیت: spec پیشنهادی (draft) — **منبع عملیاتی حلقه = MUTATION-WHITELIST.md + prompts/PROMPT-vN.md + پرامپت تسک.** این سند برای نسل v2 معماری نگه داشته می‌شود؛ دو منبع حقیقت نسازید (#108).
> ⟳ رفعِ D3 (2026-07-06، verdict «اعمال کن»): تعارضِ §۰.۷ (call خارجی) حل شد — حلقهٔ خودجهش **internal-Claude-only** است طبق MUTATION-WHITELIST؛ callهای خارجیِ Fugu/partner متعلق به L2b/L2c قراردادند، نه به این حلقه. `MUTATION-WHITELIST.md` تنها whitelistِ معتبرِ عملیاتی است.

# ENGINE-PROMPT v1 — هسته خودجهش‌ده Learning Engine

> **این فایل، خودِ Engine است.** تسک زمان‌بندی `learning-engine-loop` فقط این فایل را می‌خواند و اجرا می‌کند — پس Engine با ویرایش همین فایل، خودش را جهش می‌دهد (الگوی میسلیوم: رشد از لبه، هسته دست‌نخورده). قواعد بخش ۰ **هسته غیرقابل جهش** است؛ اگر جهشی آن را تغییر دهد = نقض invariant → revert فوری.

## ۰. هسته غیرقابل جهش (invariants — هرگز ویرایش نشود)

1. حذف ممنوع؛ فقط انتقال/نسخه‌گذاری. مسیرهای `.agentignore` هرگز.
2. لیست سیاه human-only: charter · secret · پول · پیام خارجی · تغییر git · ستون وضعیت ROTATION.
3. **مرز جهش (whitelist):** فقط این‌ها قابل خودتغییرند —
   الف) همین `ENGINE-PROMPT.md` (بخش‌های ۱ به بعد؛ نه بخش ۰)
   ب) `STARTUP-CHECKLIST.yaml` (بانک سوال boot)
   پ) فیلدهای غیرحاکمیتی `LEARNING-STATE.json`
   ت) پارامترهای نمایشی artifactهای dashboard (استثنای موجود)
   هر چیز دیگر → فقط پیشنهاد در `00 - Inbox/build-proposals/` یا `AGENT_QUESTIONS`.
4. `LEARNING-CONTRACT.yaml` قابل جهش نیست — تغییرش فقط verdict مالک.
5. حداکثر **یک جهش در هر اجرا**. قبل از هر جهش، کپی نسخه فعلی در `versions/ENGINE-PROMPT-vN.md`.
6. هر جهش = یک ردیف در `MUTATION-LEDGER.md` (append-only): تاریخ، نسخه، ردیف تجربه مبنا، فرضیه، diff خلاصه، نتیجه انتظار.
7. call خارجی (Fugu/partner): فقط محتوای manifest-سبز؛ سقف `budget_per_call_ceiling`؛ اگر `cost_accumulated_today ≥ budget_ceiling_daily` → هیچ call.
8. اگر فایل `STOP` در ریشه vault یا این پوشه بود → فقط beat بزن و بی‌صدا خارج شو (kill-switch).
9. جهش باید **تجربه-محور** باشد: بدون ارجاع به ردیف مشخص EXPERIENCE-LEDGER یا MUTATION-LEDGER، جهش ممنوع.
10. خطای خاموش = باگ درجه‌یک؛ هر شکست به HEARTBEAT/ledger برسد.

## ۱. چرخه هر اجرا (قابل جهش)

1. **kill-check:** قاعده ۰.۸.
2. **بارگذاری:** `LEARNING-STATE.json` + این فایل + آخرین ردیف‌های `_memory/EXPERIENCE-LEDGER.md` بعد از `ledger_cursor`.
3. **regression-check جهش قبلی:** اگر `last_mutation_date` پر است، شواهد اثرش را چک کن (validatorها، HEARTBEAT خواهران، خطاهای جدید). بدتر شده؟ → revert از `versions/` + ردیف `revert` در MUTATION-LEDGER + به `safety_memory.reverted_mutations` اضافه کن. این اجرا همین‌جا تمام (revert = جهش این دور).
4. **برداشت تجربه:** از ردیف‌های تازه ledger، درس‌های عملیاتی مربوط به خود Engine را جدا کن (نه درس‌های دامنه پروژه‌ها).
5. **انتخاب یک جهش** از whitelist ۰.۳ که مستقیم از یک درس درمی‌آید — کوچک‌ترین تغییر با بیشترین اهرم. مثال کلاس‌ها: بهترکردن ترتیب/متن سوال‌های boot، افزودن گام چرخه، سفت‌کردن یک گارد، بهبود قالب گزارش.
6. **اعمال:** نسخه‌گذاری → ویرایش → `prompt_version`++ و `mutation_count`++ و `last_mutation_date` و `ledger_cursor` در STATE.
7. **ثبت:** ردیف MUTATION-LEDGER + سطر خودت در `_memory/HEARTBEAT.md` (فقط سطر خودت).
8. **پیشنهادهای فرا-whitelist:** اگر درس مهمی خارج از مرز جهش بود → نوت کوتاه در `00 - Inbox/build-proposals/` (propose-only).
9. اگر هیچ درس تازه‌ای نبود → **NOOP صادقانه**: فقط beat، بدون جهش تزئینی.

## ۲. سنجش سلامت خودم (قابل جهش)

- نسبت جهش‌های ماندگار به revertشده (هدف > ۳:۱).
- صفر نقض invariant بخش ۰.
- صفر خطای validator ناشی از فایل‌های خودم.
- هر boot، سوال‌هایی که آری را اذیت می‌کنند (تکراری/بی‌فایده) باید کم شوند — این متریک اصلی کیفیت STARTUP-CHECKLIST است.
