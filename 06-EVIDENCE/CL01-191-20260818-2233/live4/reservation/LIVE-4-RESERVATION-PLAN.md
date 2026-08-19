# LIVE-4-RESERVATION-PLAN (LIVE-4-CAPACITY-RESERVATION-01 — گزینهٔ C)
لایه: _ops/cortex/live4_reservation.py (غیر-TCB، برگشت‌پذیر، بدون scheduler) + گیتِ پیش از _ask_impl در model_router.ask()
 semantics: در پنجرهٔ فعال — taskهای live4* عبور اختصاصی + شمارش تلاش (سقف ۹۰)؛ هر task پولیِ دیگر ⇒
   ok=False + reason=DEFERRED_FOR_LIVE4_RESERVATION + provider_actual=none + cost_aud=0 +
   retry_after=quota_reset_or_window_end + evaluation_eligible=false + ردیف رسید در paid-calls.jsonl
   — و _ask_impl هرگز صدا نمی‌شود (اثبات غیر-رسیدنی: 0.01s)
 شروع پنجره: فقط با observe_quota_reset (روزِ سهمیه > روزِ قبل؛ رکورد در QUOTA-RESET-OBSERVATION.json)
 پایان: انقضای ۹۰ دقیقه · سقف ۹۰ تلاش · 30 جفت · hard-stop ها
 تست: 4/4 رزرو + 15/15 مجموعهٔ قبلی — exit=0 (reservation-test-evidence.txt)
 rollback: RESERVATION-ROLLBACK.patch + حذف live4_reservation.py و تستش (ساختِ این کارت)
 اجرای خودکار در ریست بعدی: launcher در SILENT-WINDOW علاوه بر گیتِ رزرو، شرطِ سکوت را چک می‌کند
 و سپس live4_driver (پروتکل منجمد: 2×15، ≥10 برد/batch، ≥20 کل، داور کور، VOID=نه برد نه باخت) را اجرا می‌کند.
 محدودیت صادقانه: خودم scheduler ندارم و نمی‌سازم — «اجرا در ریست» یعنی نشستِ بعدی (یا دستور تو) launcher را صدا می‌زند؛
 لایهٔ رزرو تضمین می‌کند که هر لحظه که پنجره باز شود، ظرفیت فقط از آنِ Live-4 است.
