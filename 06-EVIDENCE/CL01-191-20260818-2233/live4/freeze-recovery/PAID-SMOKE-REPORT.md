# PAID-SMOKE-REPORT — PASS (2026-08-19 10:17:32 +10:00)
route: tier=primary → deepseek-v4-flash (سیاست 2026-08-15؛ معیار = provider/model واقعی receipt)
single call · no retry · no local fallback · latency 8.26s (<60s)
receipt (cost-receipts.jsonl, append-only, trace=paid-primary-1787098652019):
  COMPLETE · REPORTED · cost_usd=1.568e-05 (⟪ cap $0.001) · AUD=2.2e-05 (FX-PIN-20260819-01 · 1.4082523588)
  tokens 90/11 · budget before/after present · سقف‌ها رعایت شد
notes صادقانه: budget_before/after در hook اسنپ‌شاتِ per-call است (ledgerِ روان در رسیدهای آزمایش)؛ after=-6e-06 خطای گرد کردن همین اسنپ‌شات — ثبت شد، فیلد کامل.
نتیجه: FREEZE-RELEASE-20260819-01 مؤثر؛ مسیر پرداخت پس از ۳ روز باز و کاملاً قابل‌مشاهده است.
GO/NO-GO بازبینی‌شده پس از smoke: ①FX 18.3h⟪24h ✓ ②smoke واقعی PASS ✓ ③allowlist ✓ ④فروزن+هش ✓ ⑤8/8 ✓ ⑥exclusion مکانیکی ✓ → GO
