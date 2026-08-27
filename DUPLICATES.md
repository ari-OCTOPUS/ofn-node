# DUPLICATES — تکرارهای اثبات‌شده

> Branch: `audit/zcode-20260828` · Date: 2026-08-28 · معیار: محتوای یکسان/تقریباً یکسان با خطر drift

## درون `langar`

| Duplicate | Files | Risk |
|---|---|---|
| search_providers | `langar/researcher/search_providers.py` ≡ `langar-pro/app/research/search_providers.py` (هر دو 112 خط، یکسان) | فیکس باید دوبار اعمال شود |
| source_quality | `researcher/source_quality.py` ≡ `app/research/source_quality.py` (94=94، یکسان) | همان |
| synthesizer | 43≈43 خط | **فراخوان ناسازگار**: نسخهٔ pro با 4 آرگومان موقعیتی `(SYS, question, ranked, target)`؛ اصلی 2 آرگومان — pro با brain اصلی کرش می‌کند |
| constitution | `core/constitution.py` 14 اصل در برابر `app/research/constitution.py` 13 اصل | قاعدهٔ «تناسب ارتباطات» در pro غایب — دو قانون‌اساسی |
| بانک سؤال | `ai.py:18-67` در برابر `brain/question_bank.py:7-38` | همان سؤال‌ها با کلیدهای متفاوت (body در برابر body_hrv) |
| نرمال‌ساز رقم فارسی | `_en()` در bot.py:72 در برابر `_DIGITS` در hrv.py:14 | منطق دوبار |
| مدل هاردکد | `claude-haiku-4-5-20251001` در providers.py:58 و ai.py:202 و pro brain.py:48 | سه‌جای وابسته به deprecation |

## بین‌مخزنی/بین‌گره‌ای

| Duplicate | Parts | Note |
|---|---|---|
| پروژهٔ هم‌نام «langar» | ari322/langar (بات HRV) در برابر F:\backup `03 - Projects/اونلی فنز/langar/` (langar_bot.py) | دو کدبیس متفاوت با یک نام — سردرگمی مستند |
| قانون‌اساسی موازی | NBB-CP (Black Box، 12 invariant، 171 تست) در برابر TCB/WORKLOCK/_ops زنده | هر دو زنده‌اند، هیچ‌کدام canonical همه‌چیز نیستند (رأی مالک 08-15: «همش منم») |
| چهار router | langar brain_router + agents/router + OFN routing + node routers | مرز وظیفه مبهم (سند مالک پذیرفته) |
| بورد مالک | پوشهٔ canonical + ۱۲ میرور (Inbox/Dashboard/07-HANDOFF/agent-prompts/FUGU-BIZ/پروژه‌ها) | خطر نسخهٔ واگرا |
| بکاپ‌های کل | OCTOPOUS.rar 5.1GB + backup.rar 19.3GB + 6 پوشهٔ snapshot + 2 پوشهٔ phase0 | بدون manifest یکپارچه |
| اسنپ‌شات بکاپ دستی center.py | center.py.bak-bridge-attach-20260823 و bak-tg-wire-20260823 و … | درخت زنده پر از .bak است |

## نتیجهٔ عملی
تکرارِ واقعاً پرهزینه سه‌تاست: **researcher×3، constitution×2، بانک سؤال×2** (همه در langar) — چون drift فعال دارند. بقیه هزینهٔ شناختی‌اند نه اجرایی. بازنویسی بزرگ فقط برای همین سه‌تا (پس از تأیید مالک) توجیه دارد؛ قاعدهٔ مالک: «بازنویسی ممنوع مگر duplication اثبات‌شده» — این‌جا اثبات شد.
