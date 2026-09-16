# FREEZE-ROOT-CAUSE.md — پاسخ هفت پرسش الزامی مالک (2026-08-19)
۱) خواننده: opslib.frozen() (opslib.py:430، صرفاً exists) → organ_gate.reserve (خط ۷۲: allow=False «frozen-conflict (I3)») + cockpit/governor برای نمایش.
۲) سازنده در 2026-08-16 ~20:09: organ_gate.settle خط ۱۳۸ → opslib.freeze("settle failed for ARCHITECT_SYS: [Errno 22] Invalid argument: budget-state.json").
۳) آنچه رمزگذاری کرد: نامعInOut I3 «حسابداری نامعلوم» — settle نتوانست تخمین/واقعی را reconcile کند چون نوشتنِ budget-state.json با خطای OS-levelِ گذرا (Errno 22 = تداخل قفل فایل ویندوز) شکست خورد؛ catch-all آن را به یخِ دائمیِ همهٔ grantها تبدیل کرد.
۴) دامنهٔ واقعی: (a) — هر reserve پولی هر organ؛ نه provider-خاص، نه run-خاص. اثر عملی: کل مسیر LLM پرداختی از 2026-08-16 20:09.
۵) شرط رفعِ مصوب (قدیمی): حذفِ دستیِ فایل توسط مالک (متنِ خود approval_channel). بدون انقضا/رفع خودکار. (جدید: رکورد تصمیم + FREEZE-RELEASE-RECEIPT طبق همین کارت.)
۶) چرا fallback ساکت: انکارِ reserve در _ask_paid به‌صورت falsy برگشت؛ _ask_impl طبق طراحی «ردهٔ پولی بسته → local» ادامه داد بی‌آنکه status/block-receipt بنویسد (paid_log فقط استثنای کلاینت/کووتا را می‌نوشت). نقصِ شفافیت — رفع‌شده در وصله.
۷) تضاد با گیت فعال؟ خیر: anchors_ok=true · TCB tampered=false/signature=valid · هیچ STOP/HALT فعّال نیست · budget-state.json امروز سالم و خواناست (halted=false، هزینه‌ها جزئی). Errno-22 گذرا بود و دیگر موجود نیست؛ FREEZE امروز stale است و هیچ invariant فعالی به آن نیاز ندارد — اما طبق حکم، حذفِ دستی نکردم و رفع فقط با مراسمِ release رسیددار.
## خطرِ اصلی که FREEZE برایش ساخته شد و وضعیت امروزش
خطر: خرجِ بدونِ حسابداری (settle نافذ → ریسک هزینهٔ ثبت‌نشده). امروز: budget-state سالم، COST-OBS-1 رسیدِ کامل نصب شده، سقف‌های AUD فعال — یعنی همان خطر با ابزارِ بهتری مهار شده؛ FREEZEِ بازمانده فقط یک مسیرِ مردهٔ سه‌روزه است.
