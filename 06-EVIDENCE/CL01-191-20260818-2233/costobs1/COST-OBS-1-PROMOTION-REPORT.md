# COST-OBS-1 PRODUCTION PROMOTION REPORT — 2026-08-19 ~10:2x +10:00
پروموشن‌ها: ① cost_receipt.py + pricing_pinned.json (قالب خالی) + ۹ تست ② قلاب minimal در
model_router._ask_paid (درست در لایه‌ای که tokens_in/out + cost_usd موجودند؛ fail-soft برای مغز)
هش‌ها: model_router pre=e9bbea99… post=a64886f2… · diff=COST-OBS-1-PROMOTION.diff (37 خط) · rollback=COST-OBS-1-ROLLBACK.patch
تست: pytest (9 cost + 2 inc1) → 11/11 PASSED · exit=0 · 0.82s · out-sha bab43104… (promotion-test-run.txt)
smoke: import model_router OK (قلاب در دسترس)
synthetic REPORTED (cost_usd بدون fx pinned) → COST_UNOBSERVABLE + یادداشت «fx unpinned» + paid_blocked=True (طبق قاعدهٔ مالک: ثبت USD، بستن AUD)
synthetic UNOBSERVABLE → paid_blocked=True ✓ · راز/کلید در هیچ خروجی/لاگ نیست ✓
بدون هیچ فراخوانی live provider در طول پروموشن ✓ · بدون تغییر allowlist/budget-gate/credential/TCB ✓
مقادیر production قیمت/fx: عمداً خالی — فقط با دست مالک؛ تا آن موقع مسیر REPORTED ثبت می‌کند و AUD بسته می‌ماند.
