# TIER-ROUTING-CONTRACT (پس از INC-2 + FREEZE-01)
| tier | provider مجاز | منبع سیاست | قابل‌رسید |
|---|---|---|---|
| primary | DeepSeek (کلید deepseek) | رأی مالک 2026-08-15 «فوگو گرونه، فعلا با دیپ‌سیک» | receipt مدل/هزینه |
| secondary | DeepSeek یا GLM | نگاشت مستند budgets.routing.reason | receipt |
| fugu | فقط مسیر صریح سهمیه‌ای | سهمیهٔ روزانه (امروز: تمام‌شده 61/62 از Aug-16) | receipt |
| local (پیش‌فرض tasks) | qwen2.5:1.5b | TASK_TIERS | tier=local در خروجی |
قواعد جدید الزامی: درخواستِ paid در حالت freeze ⇒ pre-check قطعی، receipt «PAID_PATH_BLOCKED_BY_FREEZE» با ۷فیلد،
نتایج localِ ناشی از آن evaluation_eligible=false و fallback_reason ثبت‌شده — جا زدن به‌عنوان موفقیت/زوجِ قابل‌امتیاز ممنوع.
