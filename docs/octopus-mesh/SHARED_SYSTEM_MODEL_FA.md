# Shared System Model — نسخه ۱

مدل مشترک سیستم که از پاسخ‌های واقعی ۱۸۰ (result) و ۱۸۲ (witness_response) توسط ۱۳۸ ساخته شد.

- منبع: config/shared_system_model_v1.json (canonical JSON، SHA-256 ثبت‌شده)
- نقش‌ها: ۱۳۸=commander/reconciler · ۱۸۰=quality-brain (PROPOSE_ONLY) · ۱۸۲=lab-witness (read-only)
- may_authorize در همه‌جا false
- قواعد معرفتی: observation≠inference؛ ادعای system-wide نیازمند شاهد چند‌نودی؛ درآمد فقط با شاهد ledger
- ریسک‌های باز: runtime خودکار ۲۴/۷ وجود ندارد؛ کلیدهای mesh گسترده‌اند؛ پورت 9101 روی ۱۸۲ نیازمند بررسی مالک؛ redaction heuristic است
