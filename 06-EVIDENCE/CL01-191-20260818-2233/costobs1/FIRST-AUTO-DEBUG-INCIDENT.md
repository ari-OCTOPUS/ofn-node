# FIRST-AUTO-DEBUG-INCIDENT (INC1) — کشف‌شده از telemetry واقعی، نه مثال ساختگی
incident_id: INC-CL1-001 · discovered: 2026-08-18T23:5x+10:00 (پوششِ پنجرهٔ Live-3) · severity: MED
component: مسیر ورودِ متادیتا به حافظهٔ کانونی (non-TCB) · classification: BUG (نویسنده فیلد اجباری را نمی‌دهد)
evidence: دو ردیف ADMITTED بدون confidence در پنجرهٔ زنده (mem_5b84…, mem_3d0d…) + کوئری پوشش
root-cause: goal_action_bridge.consolidate_new_verdicts (~L598) و receipt_critic.evaluate_new (~L172)
  کاندیدای episodic بدون «confidence» به MemoryGate می‌دهند؛ گیت commit می‌کند ⇒ رکورد کم‌متادیتا.
disconfirming-test: اگر نویسندهٔ دیگری بود، grep «SGC cycle»/«receipt-verdict action» آن را نشان می‌داد — فقط همین دو.
patch (قرنطینه→پروموشن): افزودن confidence="0.9" با قراردادِ ثبت‌شدهٔ deterministic (فقط برای رکورد سیستمی؛
  مسیر LLM مشمولش نیست) + regression تست داینامیک (fixture→نویسنده→حافظهٔ موقت→assert) + استاتیک.
re-run original failure: تست داینامیک در درخت اصلی PASS ⇒ ردیف جدید ADMITTED با confidence+expiry (TTL وصلهٔ قبلی).
تاریخی‌ها: طبق حکم مالک EXCLUDED ماندند؛ confidence ساخته نشد.
final_state: FIXED_VERIFIED (تست: 2/2 قرنطینه، 2/2 درخت اصلی؛ مجموع اجرای پروموشن 11/11)
