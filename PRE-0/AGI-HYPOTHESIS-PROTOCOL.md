# AGI-HYPOTHESIS-PROTOCOL

AGI = فرضیهٔ **ابطال‌پذیرِ** اثبات‌نشده. هیچ ادعای «AGI اثبات شد».

## قواعد
1. `agi_is_fact()` همیشه False — کدِ اجراشده در `PRE-0/governance.py` (تستِ واقعی:
   `test_pre0_real_entry` P1). **[SPEC، هنوز کد نشده]** یک کنترلِ آیندهٔ
   `check_generated_files` قرار است عبارت‌های ادعای AGI را در اسناد بلاک کند (مگر در
   ستونِ رد با `[NO-GO]`)؛ این کنترل هنوز پیاده‌سازی نشده و نباید به‌عنوانِ گاردِ فعال
   فرض شود. تنها اثباتِ فعلیِ عدمِ نشتِ هویتِ AGI، مسیرِ ADVISORY-همیشهٔ Memory Gate است
   (`test_pre0_real_entry` P1/P6).
2. هر «توانمندی» فقط با benchmark مهروموم + held-out + baselineِ منجمد سنجیده می‌شود؛
   benchmark leakage یک hard constraint است.
3. consensus/agreement شاهد نیست (تست ۸).
4. capability-gap closure = بهبودِ قابل‌سنجشِ برگشت‌پذیرِ ثبت‌شده برای بازبینیِ مالک؛
   نه «خودتکمیلی».
5. failed hypotheses حفظ می‌شوند (museum)، silent drop ممنوع.
