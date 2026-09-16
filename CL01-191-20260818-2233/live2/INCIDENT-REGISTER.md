# INCIDENT REGISTER (LIVE-2)
INC-1 (HARD-STOP، فعال و صحیح): نرخ خطای provider 3/10=30% ≥5% پس از ۱۰ فراخوانی.
  الگو: هر ۵ baseline موفق؛ ۳ شکست همگی در «conditioned» (پرامپت بلندتر با شواهد) — راند 2/3/4.
  اثر: proposal-diff misses آلوده‌اند؛ سیگنال تمیز فقط راند 1و5 (هر دو changed=True).
  اقدام: فراخوانی‌های provider متوقف شدند؛ شواهد حفظ؛ ادامهٔ غیر-provider طبق قرارداد.
  درس برای Live-3: fallback به deepseek برای پرامپت‌های بلند یا کاهش اندازهٔ شواهد؛ نیازمند تصمیم مالک (پرداخت).
INC-2 (ثبتی): cost field برای fugu موجود نیست — به‌عنوان free-tier با cost=0 ثبت شد؛ اگر deepseek (پرداختی) انتخاب شود و cost غایب باشد → COST_UNOBSERVABLE و توقف.
INC-3 (پیشین، بسته): launch_attempt_1 import-fail — RESTART-AUDIT.md، بدون تغییر تاریخچه.
