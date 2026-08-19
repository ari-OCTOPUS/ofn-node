# COST-OBS-1 EVIDENCE — ساخت و تست (worktree قرنطینه cl01/p2-gate)
فایل‌های جدید: _ops/cortex/cost_receipt.py (آداپتور ۱۲فیلدی) · pricing_pinned.json (قالب؛ مقادیر production عمداً خالی — فقط مالک) · _ops/tests/test_cost_receipt_costobs1.py
تست: python -X utf8 -m pytest -q _ops/tests/test_cost_receipt_costobs1.py → 9/9 PASSED · exit=0 · 1.00s · out-sha 116a425ce69c5122 (costobs1-test-run.txt)
پذیرش‌ها: REPORTED ✓ (از payload واقعی: cost_usd در لایهٔ _ask_paid موجود — model_router.py:302,312) · DETERMINISTIC فقط با قیمت+fx pinned ✓ · UNOBSERVABLE می‌بندد ✓ · مدل ناشناس/قیمت unpinned ✓ · سقف‌های اتمیک ✓ · idempotent ✓ · بدون راز ✓ · fallback دو-مسیره ✓ · FREE_OR_UNBILLED (نه 0 AUD بی‌شاهد) ✓
ریشهٔ اصلاح‌شده (INC-L3-1): دادهٔ هزینه از ابتدا در لایهٔ کلاینت بود؛ ProviderResponse عمداً آن را نمی‌رساند — آداپتور باید در ساختِ ProviderResponse/لایهٔ _ask_paid قلاب شود (۳ خط، نقطهٔ اتصال: model_router.py ~311 که response با tokens_in/out/cost_usd ساخته می‌شود).
خواهندهٔ مالک برای فعال‌سازی production: ① تأیید نقطهٔ قلاب ② fx_usd_to_aud (منبع pinned) ③ قیمت deepseek از منبع pinned (یا اتکا به REPORTED چون کلاینت cost_usd می‌دهد).
تعمیر داده: دو رکورد confidence‌گمشده نوشتهٔ ارگانیسم زنده‌اند (SGC/verdict) — بازسازی‌ناپذیر از منبع معتبر ⇒ EXCLUDED از واجدیت (حکم مالک: confidence ساختگی ممنوع) + کارت F3: گیتِ متادیتا در سطح MemoryStore.insert.
rollback: حذف سه فایل جدید (ساختِ همین کارت، نه evidence) — بدون لمس فایل‌های موجود.
