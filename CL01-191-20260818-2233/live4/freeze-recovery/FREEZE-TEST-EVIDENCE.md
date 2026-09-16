# FREEZE-TEST-EVIDENCE — گیتِ recovery
quarantine: 4/4 passed · exit=0 · 2.00s (freeze-test-run.txt)
main-tree پس از پروموشن (کد فقط؛ flag دست‌نخورده): 15/15 passed · exit=0 · 2.34s (شامل cost_receipt×9 + INC1×2 + freeze×4)
سناریوها: ①یخ + درخواست paid ⇒ _ask_paid هرگز صدا نمی‌شود + receipt با هر ۷ فیلد + evaluation_eligible=false
②release رسیددار (رکورد تصمیم ⇒ FREEZE-RELEASE-RECEIPT.json + آرشیو flag نه حذف) ⇒ با mock، _ask_paid رسیدنی، بدون تماس provider
③tier-map: primary=deepseek طبق سیاست ۲۰۲۶-۰۸-۱۵ ④freeze_state ساخت‌یافته برای flagهای legacy
هیچ تماس provider/شبکه‌ای در هیچ تستی انجام نشد · rollback: FREEZE-SEMANTICS-ROLLBACK.patch + حذف فایل تست
