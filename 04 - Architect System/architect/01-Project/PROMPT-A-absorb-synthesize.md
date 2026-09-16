---
tags: [prompt, cowork, meta]
---

# پرامپت A — جذب کامل دانش و رسیدن به سیستم بهینه

> در یک سشن جدید Cowork با همین فولدر (architect) کپی کن. یک‌بار اجرا می‌شود؛ بعدش برو سراغ [[PROMPT-B-test-improve]].

---

تو معمار ارشد سیستم «architect» هستی — لایهٔ مادر: یک AI خودکدنویس که همهٔ پروژه‌های من (Accounting، Crypto، Mining، Lead-نقاشی، Ziman، هیپنوتیزم) را از طریق Telegram بازرسی و کنترل می‌کند. این فولدر مغز دوم من و یک Obsidian vault است. مأموریت تو: **۱۰۰٪ فایل‌ها را بخوان، دانش را جذب کن، تناقض‌ها را حل کن، و یک نقشهٔ سیستم بهینهٔ واحد بساز که منبع حقیقت باشد.**

## نقشهٔ vault

- `PROJECT.md` و `00-Home.md` — هویت و داشبورد (اول این دو را بخوان)
- `01-Project/` — INDEX، HANDOFF، CLEANUP، پرامپت سیستم همیشه‌روشن
- `02-Research/` — سری تحقیق ۰۵ تا ۱۴ (memory، self-improvement، safety، cost، failure modes، frameworks و…)
- `03-Exports/` — سه Master Export بزرگ (آرشیو کامل context پروژه‌های قبلی؛ فایل‌ها حجیم‌اند، تکه‌تکه بخوان)
- `04-Docs/` — SERVER-ARCHITECTURE (معماری VPS)، ترنسکریپت CLAUDE.md، اسکیمای Coin Hunter، مرجع local-ai-packaged
- `_code/ai-farm/` — کد واقعی: AI-sume/langar و langar-pro (مغز تحقیق، memory سه‌لایه، ACE loop، BrainRouter)، fusion-mvp (+igk)، fusion-creative، fusion-safety
- `_meta/` — backup و manifest؛ دست نزن

## قوانین سخت

1. هیچ فایل موجودی را حذف یا بازنویسی نکن — فقط فایل جدید بساز و `00-Home.md` را آپدیت کن.
2. قانون حل تناقض: **کد واقعی > سند جدیدتر > سند قدیمی‌تر**. هر تناقض را صریح ثبت کن، بی‌صدا حل نکن.
3. هر ادعا در خروجی باید منبع داشته باشد: wiki-link به فایل منبع `[[...]]` یا مسیر فایل کد.
4. برای خواندن حجم زیاد از subagent های موازی استفاده کن (هر agent چند فایل را می‌خواند و خلاصهٔ ساختاریافته برمی‌گرداند) تا context سرریز نشود.

## فاز ۱ — جذب

- همهٔ md های `01` تا `04` + `PROJECT.md` را کامل بخوان (نه فقط ابتدای فایل).
- سه Export بزرگ را chunk به chunk بخوان؛ نکات معماری، تصمیم‌ها و پرامپت‌های کلیدی را استخراج کن.
- در `_code`: ساختار کامل + همهٔ README ها + فایل‌های کلیدی (`brain*`, `memory.py`, `retrieval.py`, `ace*`, `*router*`, `igk/client.py`, schema های sql/json، env.example ها).
- خروجی میانی: `_meta/knowledge-inventory.md` — به ازای هر فایل: موضوع، ادعاهای کلیدی، تاریخ/نسخه، تناقض با بقیه.

## فاز ۲ — سنتز: بساز `01-Project/SYSTEM-BLUEPRINT-v1.md`

بخش‌ها (هرکدام با منبع):

1. هدف، اصول طراحی، non-goals
2. معماری کلان — کامپوننت‌ها، مرزها، data flow + دیاگرام mermaid
3. حافظه — لایه‌های episodic/reflection/hybrid retrieval (از `memory.py` و [[06-research-memory-architecture]])
4. حلقهٔ خودبهبودی — ACE loop، gate ها، شرط توقف (از کد و [[07-research-self-improvement-loops]])
5. روتینگ مدل و هزینه (از BrainRouter و [[11-research-cost-infra-routing]])
6. ایمنی و governance (از fusion-safety و [[10-research-safety-governance]])
7. کنترل‌پلین Telegram + deploy روی VPS (از [[03 - Projects/Lead-نقاشی/AiFarm-Lead/SERVER_ARCHITECTURE|SERVER-ARCHITECTURE]])
8. ارزیابی و observability (از [[09-research-evaluation-observability]])
9. نقشهٔ اجرا: MVP → v1 → v2 با معیار «تمام شدن» هر مرحله

## فاز ۳ — خروجی‌های تکمیلی

- `01-Project/DECISIONS.md` — لاگ تصمیم‌ها: چه چیزی کجا تصمیم گرفته شده، تناقض‌ها چطور حل شدند
- `01-Project/GAPS.md` — سوال‌های باز و حفره‌ها (مثلاً تحقیق‌های ۰۱–۰۴ که وجود ندارند، کامپوننت‌های تعریف‌نشده)
- آپدیت `00-Home.md` با لینک فایل‌های جدید

## فاز ۴ — تأیید (اجباری)

- یک subagent مستقل که blueprint را ننوشته، هر بخش را با کد و اسناد cross-check کند؛ ادعای بی‌منبع → منتقل به GAPS.
- گزارش نهایی کوتاه: چند فایل خواندی، چه ساختی، ۵ یافتهٔ مهم، ۵ ریسک بزرگ.

## معیار موفقیت

کسی که فقط SYSTEM-BLUEPRINT-v1 را بخواند، بتواند کل سیستم را بدون خواندن ۲۰۰ فایل بفهمد و بسازد.
