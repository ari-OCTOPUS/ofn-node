# PAIRED PROPOSAL EVALUATION (LIVE-3)
۱۵/۱۵ جفت VOID — هیچ miss یا hit ثبت نشد (خطای provider = عدم دسترس، نه شکست تصمیم):
- پرامپت‌های conditioned >500 کاراکتر → طبق سیاست مستقیم fallback → deepseek
- اولین فراخوانی deepseek موفق BUT فیلد cost در پاسخ router موجود نبود → COST_UNOBSERVABLE → hard-stop پرداختی‌ها (حکم مالک، اجرا شد)
- از آن نقطه: هر conditioned → FALLBACK_UNAVAILABLE (12 رسید) → جفت‌ها یک‌به‌یک باطل
- baselineهای fugu کوتاه: ۵/۵ موفق — سیاست «fugu فقط کوتاه» صحت داشت
نتیجهٔ شرط④ مالک: غیرقابل‌استیبنط — راه‌گشا: افزودن observability هزینه به مسیر پرداختی router (کارت COST-OBS-1)
