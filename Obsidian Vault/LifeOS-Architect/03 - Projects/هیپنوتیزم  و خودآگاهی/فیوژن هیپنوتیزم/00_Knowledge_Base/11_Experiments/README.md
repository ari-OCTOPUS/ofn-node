# 11_Experiments — نسخه‌یِ کاملِ Experiments.md

## Neuro-HRV — E1 تا E5
جدولِ کامل و جزئیاتِ هرکدام در `Experiments.md` (ریشه) و منبعِ اصلی `Neuro-HRV-Nof1/heart-awareness-map.html` بخشِ C. تکرار نشد تا محتوا دوبار نیاید؛ فقط یک نکته‌یِ اضافه اینجا: E5 (حلقه‌یِ شبانه) با ⭐ در منبع مشخص شده به‌عنوانِ «پراهرم‌ترین» — یعنی اگر فقط یک آزمایش قرار است اجرا شود، طبقِ خودِ سند باید همین باشد.

## Fusion-World — Rung 0 / CHSH / Selectivity Probing
جزئیاتِ کامل در `Experiments.md` (ریشه) و `03_Quantum/README.md`. نکته‌یِ تکمیلی: Rung 0 دقیقاً نقشِ «negative control روی خودِ ابزار» را دارد — قبل از هرگونه جست‌وجویِ سیگنالِ واقعی. این را می‌شود «آزمایشِ صفرم» نامید: آزمایشی که موضوعش خودِ آزمایش‌کننده است.

## fusion-mvp — Grounding Validation (دایجست)
طرحِ جایگزینیِ mock با retrieval واقعی + held-out set در evals + `GroundingValidator` («این claim رویِ fresh data قابلِ‌تحقق است؟»). اصلِ راهنما: «internal coherence = necessary but never sufficient» — جمله‌ای که می‌تواند تیترِ کلِ این پوشه باشد.

## جدولِ مقایسه‌یِ سه نوع «negative control»

| برنامه | negative control | چه‌چیزی را تأیید می‌کند |
|---|---|---|
| Fusion-World | Rung 0: کانالِ کلاسیک خاموش | pipeline درست، no-comm را می‌بیند |
| fusion-mvp | held-out set در grounding | claim رویِ داده‌یِ ندیده هم درست است |
| (پیشنهادی، سنتز) Silabi-Bot | دیتایِ تصادفیِ ساختگی رویِ `learn_profile` | مدل بیش‌برازش ندارد |

این جدول نشان می‌دهد یک الگویِ روش‌شناختیِ واحد (یالِ ۲ در `KnowledgeGraph.md`) در دو زمینه‌یِ اجراشده و یک زمینه‌یِ پیشنهادی قابلِ‌اعمال است.

**اولویتِ کلیِ این پوشه:** Rung 0 و Grounding هر دو «قدمِ بلافاصله‌یِ بعدی» طبقِ اسنادِ خودشان‌اند — یعنی دو تا از بالاترین‌اولویت‌ترین اقداماتِ کلِ پروژه اینجا جمع‌اند.
