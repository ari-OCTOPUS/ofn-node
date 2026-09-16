# INC-CL1-002 — نقشهٔ tier با حکم مالک 2026-08-15 ناسازگار (ROOT-CAUSED)
کشف: اجرای Live-4 #1 نامعتبر — هر ۱۵ جفت VOID (داورِ local ناخوانا)؛ spent=0
شواهد: رسیدهای driver (model=qwen2.5:1.5b در هر دو بازو) · paid-calls.jsonl بدون ردیف جدید
       (fugu-quota تمام‌شده از Aug-16: quota_daily-cap در 61) · probe مستقیم keys_present همه True
ریشه: model_router._ask_impl::_has — «primary→fugu»، «secondary→deepseek»؛ درحالی‌که کامنتِ
       مالک (2026-08-15: «فوگو گرونه، فعلا با دیپ‌سیک») می‌گوید primary باید reason/deepseek باشد.
       یعنی reroute فقط در مستندات انجام شد نه در نقشهٔ کلید. نتیجه: primary→fugu(کووتای مرده)→
       fallback بی‌صدای local با ok=True — بدون لاگِ شکست (سکوتِ تله‌آمیز).
اثر تجربی: اختلاف بازوها نباید provider باشد؛ در #1 هر دو local بودند (متقارن ولی داور ناتوان).
اصلاح اجرایی: درایور #2 — هر سه فراخوانی tier="secondary" (deepseek) برای انصاف زوجی.
کارت اصلاح ریشه (مالک‌بر): هم‌ترازیِ _has با حکم 2026-08-15 (primary→deepseek) + لاگ‌گذاری fallback محلی.
