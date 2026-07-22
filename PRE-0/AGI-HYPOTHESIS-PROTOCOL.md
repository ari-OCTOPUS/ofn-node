# AGI-HYPOTHESIS-PROTOCOL

AGI = فرضیهٔ **ابطال‌پذیرِ** اثبات‌نشده. هیچ ادعای «AGI اثبات شد».

## قواعد
1. `agi_is_fact()` همیشه False (تست ۱)؛ `check_generated_files` عبارت‌های ادعای AGI را در
   اسناد بلاک می‌کند (مگر در ستونِ رد با `[NO-GO]`).
2. هر «توانمندی» فقط با benchmark مهروموم + held-out + baselineِ منجمد سنجیده می‌شود؛
   benchmark leakage یک hard constraint است.
3. consensus/agreement شاهد نیست (تست ۸).
4. capability-gap closure = بهبودِ قابل‌سنجشِ برگشت‌پذیرِ ثبت‌شده برای بازبینیِ مالک؛
   نه «خودتکمیلی».
5. failed hypotheses حفظ می‌شوند (museum)، silent drop ممنوع.
