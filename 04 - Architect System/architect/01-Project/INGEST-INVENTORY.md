---
type: report
status: awaiting-approval
created: 2026-07-03
updated: 2026-07-03
tags: [ingest, stage-1, inventory]
---

# INGEST-INVENTORY — Stage 1 (فقط‌خواندنی)

> روش: fingerprint مسیر+اندازه+mtime علیه vault زنده؛ peek فقط روی نمونه‌های غیرsecret. سورس‌ها دست نخورده‌اند.
> SOURCE_DIRS: `Desktop/AI-armin` (6.9M) · `Desktop/AI-sume` (8.4M) · `Desktop/Mining` (2.4G) · `backup/مغز دوم` (12K)

## جدول Inventory

| # | خوشه | محتوای واقعی | حجم/تعداد | زبان | مقصد پیشنهادی | Verdict |
|---|---|---|---|---|---|---|
| 1 | `Mining/` (کل) | پیش‌نسخهٔ کامل `03 - Projects/Mining` قبل از پاکسازی امروز: ۱۱۳ فایل عین vault + همان باینری‌هایی که امروز به `_Archive` رفت (OS 2.1G، ماینرها، MobaXterm) | 2.4G / 314f | fa+en | — | **SKIP** (تکرار کامل؛ کاندید آرشیو مالک) |
| 2 | `Mining/Robo-data/robots/*.pdf` ×2 | SENTINEL BUILD PROMPT · big scenarios framework — هر دو از قبل در vault (Ai bots / Crypto-etoro) | 500K | en | — | **SKIP** (موجود) |
| 3 | `AI-sume/فیوژن هیپنوتیزم/00_Knowledge_Base` | نسخهٔ **متفاوت** KB فیوژن: ۱۷ سکشن (vault: ۱۳) — هم‌نام‌ها هم‌اندازه نیستند؛ vault امروز ۲۳:۰۰ ویرایش شده (احتمالاً redaction فاز ۰) | ~45f | fa+en | `07 - Knowledge/…/فیوژن هیپنوتیزم` | **NOTE-VERSIONED** ⚠️ بدون overwrite؛ فقط با diff |
| 4 | `AI-sume/فیوژن هیپنوتیزم/Hypnosis-Research` + `nodes/` | ۸ نوت پژوهش هیپنوتیزم (P0–P3، X1، Hamfazi، پرامپت‌ها) — در vault **وجود ندارد** | 8f | fa | همان دامنه، زیرپوشه جدید | **NOTE** (جدید خالص) |
| 5 | `AI-sume/فیوژن هیپنوتیزم/Fusion-World` | ۲ نوت تئوری (seam detective با رجیستر E/S/P، handoff EN) — جدید | 2f | fa+en | همان دامنه | **NOTE** |
| 6 | `AI-sume/فیوژن هیپنوتیزم/Silabi-Bot` | roadmap.md + `silabi_bot.py` (کد — توکن hardcoded، ردیف 6) | 2f | fa | roadmap→NOTE، py→POINTER | **NOTE+POINTER** |
| 7 | `AI-sume/…/Neuro-HRV-Nof1` + `SERVER_ARCHITECTURE.md` | نسخه‌های متفاوت نوت‌های موجود vault + ۱ چک‌لیست جدید | 4f | fa | همان دامنه | **NOTE-VERSIONED** ⚠️ |
| 8 | `AI-sume/AGI-Personal/AIFarm-book/{fusion-mvp,langar,langar-pro,fusion-creative,fusion-safety}` | ریپوهای کد (py/pyc/env) — نسخهٔ canonical در ناحیهٔ بستهٔ agentignore داخل vault موجود است | ~250f | en | یک pointer برای هرکدام | **POINTER** (کد وارد vault نمی‌شود) |
| 9 | `AI-sume/…/fusion-safety/docs` + `fusion-creative/*.pdf` | ~۱۳ PDF مرجع فیوژن (canon، roadmap، igk) — بعضی از قبل در vault | 5+8f | en | `08 - Assets` + لینک از نوت فیوژن | **ASSET** (فقط hash-جدیدها) |
| 10 | `AI-sume/AGI-Personal/AiFarm-Lead` | ۱۲۵/۱۲۹ فایل عین vault `Lead-نقاشی/AiFarm-Lead`؛ فقط zip تئوری + ۱ pdf (که آن‌هم در vault هست) | 129f | fa+en | — | **SKIP** (+ ذکر zip در pointer) |
| 11 | `AI-armin/AGI-Personal` (کل) | زیرمجموعهٔ قدیمی‌تر AI-sume (۱۳۷/۱۵۸ مشترک)؛ armin-only: نسخه‌های قدیمی brushline governance + personal Research (هر دو فایلش SECRET-EXCLUDED) | 158f | fa+en | — | **SKIP** (نسخه قدیمی) به‌جز ردیف 12 |
| 12 | `AI-armin/…/architect/معماری قالب` + `LANGAR-MASTER-EXPORT.md` | ۱۰ نوت research (05–14) — عین `02-Research` vault (mtime/size یکسان)؛ EXPORT هم در `03-Exports` هست | 11f | fa | — | **SKIP** (موجود) |
| 13 | `AI-armin/…/AiFarm-Lead/data-entry.txt` | سند instruction انگلیسی سیستم AI کسب‌وکار نقاشی سیدنی | 1f | en | `03 - Projects/Lead-نقاشی` | **NOTE** |
| 14 | `backup/مغز دوم` | پوستهٔ خام Obsidian: Welcome پیش‌فرض + ۳ نوت خالی + `.obsidian` — هیچ محتوایی ندارد | 11f | — | — | **SKIP** (کاندید حذف مالک — vault تودرتو) |
| 15 | ۲۵ مسیر Stage 0 | فایل‌های secret-دار | — | — | — | **SECRET-EXCLUDED** → [[INGEST-EXCLUDED-SECRETS]] |

## جمع‌بندی verdicts

- **NOTE (جدید خالص):** ~۱۲ فایل (ردیف‌های 4، 5، 6، 13) — بدون ریسک
- **NOTE-VERSIONED ⚠️:** ~۴۹ فایل هم‌نام با محتوای متفاوت (ردیف‌های 3، 7) — نیاز به سیاست merge (سوال باز ۱)
- **POINTER:** ۵–۶ ریپوی کد (ردیف‌های 6، 8)
- **ASSET:** حداکثر ۱۳ PDF منهای تکراری‌های hash (ردیف 9)
- **SKIP:** ~۲.۴G — عمدتاً تکرار کامل vault یا نسخه قدیمی‌تر (ردیف‌های 1، 2، 10، 11، 12، 14)

## سوالات باز (پاسخ قبل از Stage 2)

1. **سیاست NOTE-VERSIONED:** نسخه‌های سورسِ هم‌نام (فیوژن KB) چطور بیایند؟ (الف) کنار نسخه vault با پسوند ` (desktop-v)` و لینک متقابل — پیشنهاد من؛ (ب) فقط diff-report و تصمیم فایل‌به‌فایل تو؛ (ج) اصلاً نیایند. توجه: overwrite ممنوع چون vault امروز redaction شده.
2. **canonical کد fusion-mvp/langar:** نسخهٔ داخل ناحیهٔ بستهٔ vault مبناست؟ pointerها به کدام مسیر مطلق اشاره کنند — vault یا Desktop؟
3. «مغز دوم» را خودت حذف می‌کنی یا در REDUNDANT-SOURCES فقط ثبت شود؟
