# GOVERNANCE-MAINTENANCE-LANE

نقص‌های **constitution** و **verifier** هرگز توسط حلقهٔ self-improvement اصلاح نمی‌شوند
(`governance.routes_to_maintenance_lane`؛ اثبات: تست ۴).

## مسیر
1. حلقهٔ خودبهبودی نقص را فقط **گزارش** می‌کند (propose)، نه patch.
2. تغییرِ constitution/verifier فقط با:
   - branchِ جدا، owner-governed؛
   - بازبینیِ مستقل (نه همان claimant)؛
   - رأیِ صریحِ مکتوبِ مالک در ledger؛
   - regression که precedence و hard constraints را دوباره اثبات کند.
3. هیچ merge/activation بدونِ امضای مالک.

این جداسازی مانعِ «سیستم قانون‌اساسیِ خودش را تضعیف کند» می‌شود.
