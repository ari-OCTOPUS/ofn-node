# KB-10 — Prompt Library

> کتابخانهٔ پرامپتِ قابلِ‌استفادهٔ مجدد برای نقاشیِ ساختمانِ سیدنی. دو هدف: خلاقیت + کیفیت/امنیت. قید: no false claims (ACL)، consent (Spam Act).
> اصل: اول واگرایی (A/C)، بعد همگرایی (B/D). خلاقیت بدونِ نقد = توهم؛ نقد بدونِ خلاقیت = فلج.

---

## A) Creativity Injectors
- **A1 ایده‌های واگرا:** «۱۵ ایدهٔ واقعاً واگرا بده (نه ۱۵ نسخهٔ یک ایده)، ۳ تا خطرناک/عجیب، بدونِ خودسانسوری؛ بعد ۳ برتر را با دلیل علامت بزن.»
- **A2 Constraint-flip:** «این محدودیت‌ها (بودجهٔ نزدیکِ صفر، تمرکزِ محلی، فقط owned channel) را به فرصت تبدیل کن؛ ۵ کانسپت که دقیقاً به‌خاطرِ این‌ها قوی‌اند.»

## B) Copy / Content (با گاردِ ACL + Spam Act)
- **B1 suburb page (Local SEO):** «صفحهٔ landing برای "painter in [suburb], Sydney"؛ محتوای یکتا و محلیِ واقعی، خدمت، چرا این محله، social proof، CTA quote؛ هیچ ادعای اثبات‌نشده.»
- **B2 caption before/after:** «کپشن برای عکسِ before/after؛ روایتِ کار (نه ادعای فروش)، محلی، CTA نرم، ۳ variant.»
- **B3 quote follow-up:** «پیامِ کوتاهِ روز ۲ (سؤال؟)، روز ۵ (تنظیمِ scope؟)، روز ۱۰ (بستن)؛ مودبانه، بدونِ فشار؛ هر پیام sender-ID/ABN + opt-out (Spam Act).»
- **B4 پاسخ به review:** «مثبت: تشکرِ شخصی. منفی: مالکیت + تعهد به اصلاح، بدونِ دفاعی‌شدن، بدونِ افشای PII.»
- **B5 Google Ads:** «۳ headline + ۲ description برای "[خدمت] painter [suburb]"؛ قصدِ بالا، CTA quote، بدونِ ادعای دروغ.»

## C) Red-Team / Skeptic (تأیید نکن، نقد کن)
- **C1 منتقدِ بی‌رحم:** «کارِ من را بی‌تعارف نقد کن؛ دنبالِ ادعای بی‌مدرک (ACL)، نقضِ Spam Act، anchoring، confirmation bias، نقاطِ شکست؛ ریسک‌ها را رتبه بده، یک اصلاح با دلیل بده؛ تصمیم با من.»
- **C2 Pre-mortem:** «فرض کن این کمپین ۶ ماهِ دیگر شکست خورد؛ ۸ دلیلِ محتمل؛ برای ۳ تای بالا mitigationِ ارزان.»
- **C3 Grounding:** «این ادعا را به منبع وصل کن (قانونِ AU/داده/مقاله)؛ کجا تخمین، کجا واقعیت؟ اگر grounding نداری، «نمی‌دانم» بگو.»

## D) Engineering
- **D1 مرورِ معماری:** «این طرح را با ۶ محور نمره بده (۱–۱۰): Cost/Complexity/Scalability/Maintainability/Security/Time؛ ساده‌ترین کافی؟ کجا framework بی‌دلیل پیچیدگی می‌دهد؟»
- **D2 tool/integration:** «toolها را نقد کن: کدام list-all است و باید search_x شود؟ کدام context هدر می‌دهد؟ طرحِ integration با ServiceM8/Tradify (Zapier/Make).»
- **D3 eval:** «یک eval set با held-out؛ متریک (cost-per-booked-job، conversion)؛ Wilson lower-bound برای A/B، نه pass-rate خام.»

## قواعدِ سخت
۱. هر copy از Gate (KB-07) رد شود. ۲. no false claim، consent همیشه. ۳. واگرایی قبل از همگرایی.

## قدم بعدی
استفاده در Workers C/D (KB-01)؛ promptهای C-series به‌عنوان red-team set برای KB-07/KB-08.
