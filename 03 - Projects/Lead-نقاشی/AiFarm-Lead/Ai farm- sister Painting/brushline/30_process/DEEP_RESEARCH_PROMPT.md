# DEEP RESEARCH PROMPT — مباحثی که تحقیقِ خیلی بیشتری می‌خواهند

> این پرامپتِ پژوهشی است برای تکمیلِ نقاطی که لایهٔ تئوری فقط فریم/تخمین دارد و قبل از build واقعی به **تحقیقِ عمیقِ منبع‌دار** نیاز دارند.
> طرزِ استفاده: هر بلوک را به‌عنوان یک ماموریتِ پژوهشی اجرا کن. خروجی: یافته‌های منبع‌دار + به‌روزرسانیِ KB مربوطه. قاعده: هر ادعای متغیر = منبع + تاریخ؛ هرجا قطعیت نیست «نمی‌دانم».

---

## R-1 — حقوقِ AU (وکیل‌-grade) → KB-12/03/09
چرا عمیق‌تر: قانون متغیر و enforcement فعال شده؛ ریسکِ جریمهٔ واقعی.
سؤالات:
- جریمه‌های **دقیق و روزِ** Spam Act 2003 (ACMA) per breach/per day.
- وضعیتِ **tranche 2** اصلاحاتِ Privacy Act (حذفِ small-business exemption؟ «fair & reasonable»؟ right to erasure؟).
- الزامِ دقیقِ **ADM disclosure (APP 1.7)** برای سیستمی مثل Brushline: آیا lead-handlingِ AI «significant effect» محسوب می‌شود؟ متنِ نمونهٔ privacy policy.
- مرزِ **inferred consent** برای follow-up و **cold B2B** (Capital Works/strata outreach).
- الزاماتِ **Notifiable Data Breach** (۷۲h؟ آستانهٔ «serious harm»).
- آیا OAIC sweep روی real estate شریکِ ارجاعِ Brushline را درگیر می‌کند؟
منابع: oaic.gov.au، acma.gov.au، accc.gov.au، legislation.gov.au، تحلیل‌های law firm.
خروجی: KB-12 با ارقام/تاریخ + privacy-policy template.

## R-2 — APIهای واقعیِ integration → KB-01/09
چرا عمیق‌تر: spec فعلی مفهومی است؛ build به endpoint/scope/rate-limit واقعی نیاز دارد.
سؤالات:
- **ServiceM8 REST:** endpointهای دقیق (company/job/contact)، scopeها، OAuth flow، rate limit، webhook برای job-completed.
- **Tradify:** سطحِ API واقعی؛ چه چیزی فقط via Zapier/Make ممکن است؛ هزینهٔ Zapier/Make.
- **GBP:** فرایندِ approvalِ دسترسی به Business Profile API، quota، OAuth scope، rate limit؛ جایگزینِ managed (bundle.social/SlashPost) هزینه.
- **Meta/Instagram Graph (Content Publishing):** الزامِ Business account، app review، rate limit؛ یا scheduler رسمی (Buffer/Metricool) به‌جای مستقیم.
منابع: docs رسمیِ هر سرویس.
خروجی: KB-01 §۵ با جدولِ endpoint/scope/limit واقعی.

## R-3 — دادهٔ بازارِ محلیِ سیدنی (primary) → KB-13/14/02
چرا عمیق‌تر: KB-13/14 الگو دارند، نه دادهٔ زندهٔ محله.
سؤالات:
- چگالیِ رقیب و سطحِ review در محله‌های هدفِ Operator (map pack واقعی).
- قیمتِ واقعیِ بازار per m² (داخلی/بیرونی) در سیدنی ۲۰۲۶؛ فرکانسِ repaint coastal vs inland.
- وضعیتِ روزِ پل‌های اجاره‌ای (hipages/Oneflare/ServiceSeeking pricing؛ آیا Oneflare هنوز فعال؟).
- اقتصادِ Capital Works: ارزشِ متوسطِ یک پروژهٔ exterior strata؛ تعدادِ strataهای هدف.
منابع: Domain/realestate.com.au، Strata Hub، سایتِ پل‌ها، quote واقعی.
خروجی: KB-13/14 با دادهٔ محلی + ورودیِ break-even در KB-02.

## R-4 — اقتصادِ واقعی (R11/R12) → KB-02/CONFIG
سؤالات: `fx_aud_usd` روز؛ Google Places per-request؛ `avg_margin_per_job`؛ `enquiry→quote rate`؛ `quote→job rate`؛ بودجهٔ Ads.
خروجی: CONFIG پر شود؛ break-even واقعیِ KB-02 محاسبه شود.

## R-5 — LANGAR reuse (داخلی، نه قابلِ‌سرچ) → KB-01
سؤالات: دقیقاً چه interface/DB/process از LANGAR قابلِ‌reuse است؟ مرزِ جداسازیِ دادهٔ شخصی (تستِ «هیچ LANGAR»). نقشهٔ نگاشتِ ماژول‌های خواهر به A–F.
خروجی: KB-01 با نقشهٔ reuse مشخص.

## R-6 — Eval harness عملی → KB-08
سؤالات: promptfoo vs DeepEval vs Braintrust برای این use-case (هزینه/lock-in/قابلیت)؛ طراحیِ held-out set واقعی؛ پیاده‌سازیِ Wilson؛ آستانه‌های anomaly.
خروجی: KB-08 با طرحِ harness عملی.

## R-7 — go-to-market حقوقیِ Capital Works → KB-14/12
سؤالات: cold outreach به strata manager زیر Spam Act — کجا inferred consent صدق می‌کند؟ آیا «free assessment» پیشنهادِ تجاری است؟ متنِ امنِ outreach.
خروجی: KB-14 با playbookِ منطبق.

---

## قاعدهٔ خروجی
هر بلوک: (۱) یافته‌های منبع‌دار با تاریخ، (۲) به‌روزرسانیِ KB هدف، (۳) به‌روزرسانیِ CONFIG اگر پارامتری بسته شد، (۴) علامتِ باقی‌ماندهٔ «نامعلوم». هیچ کدی؛ فقط تعریف/داده تا فاز ۰.
