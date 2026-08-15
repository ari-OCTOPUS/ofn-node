---
type: truth-note
section: test-count
created: 2026-08-15
verified_at: 2026-08-15
status: mixed — هر ردیف برچسب خودش را دارد
---

# TEST-COUNT — تعداد واقعی تست‌ها (راستی‌آزمایی زنده 2026-08-15)

## نتایج اجرای زنده (فرمان‌ها عیناً ثبت شده)

| مجموعه | ادعا | نتیجهٔ زنده | فرمان | وضعیت |
|--------|------|-------------|-------|-------|
| NBB-CP (`03 - Projects/NBB-Control-Plane`) | MANIFEST: **۲۰۷** (83+102+5+17) · BACKUP-README: **۱۷۱** · README رینه: ۲۰۷ | **`171 passed in 2.50s`** (۰ failed) | `py -m pytest -o addopts= -p no:warnings -q` | ✅ **verified: ۱۷۱** → [[CONTRADICTIONS|C-001]] |
| hypothesis_engine (`_ops/hypothesis_engine`) | CURRENT-TRUTH: «۵ سوییت سبز» | ابتدا ImportError → بعد از رأی NEW-4 (stash + بازگردانی): **`23 passed in 1.53s`** ✅ | `py -m pytest -o addopts= -q` | ✅ **verified: ۲۳** (بعد از بازگردانی 2026-08-15) → [[CONTRADICTIONS|C-003]] resolved |
| رصدخانه (working repo Desktop) | گزارش نشست: ۹۳ تست | **93 passed** (گزارش SYNC-REPORT-20260815-163907.md — خوانده‌شده مستقیم از دیسک) | `python -m pytest _ops\observatory\tests\ -q` | ✅ **verified: ۹۳** (اجرا توسط موتور sync) |
| epistemics (`_ops/epistemics`) | CURRENT-TRUTH: «۴۵/۴۵ + ۲۰/۲۰» · سربرگ ADR-039: «۱۳۳» | `test_planner.py`: collected 0 items (TestPlan مدل است نه تست) — سوئیت اجراشدنی پیدا نشد | `py -m pytest _ops/epistemics/test_planner.py -v` | ⚠️ **unverified** → [[CONTRADICTIONS|C-007]] |
| کل مخزن (ریشه) | مگاپرامپت: ۴۱۴ یا ۴۰۸ | `--collect-only` از ریشه: `15 tests collected, 2 errors` | `py -m pytest -q --collect-only` | ⚠️ **unverified** → [[CONTRADICTIONS|C-006]] |
| بازتولید hash زنجیره‌های شاهد | — | **۴/۴ ردیف منطبق** (۲ evidence + ۲ prediction) با فرمول عین سورس | اسکریپت python mode=ro (2026-08-15) | ✅ **verified** — فرمول‌ها در HANDOFF |
| **راستی‌آزمای کامل انبار زنده** (`scripts/verify_live_store.py` اصلاح‌شده) | — | **VERDICT: PASS — 27/27، CRITICAL 3→0** («All guarantees reproduced on live data») | `python scripts/verify_live_store.py` (2026-08-15 17:1x) | ✅ **verified — سطح A** |
| کل مخزن کاری Desktop | — | **320 passed in 3.90s** (پس از ۳ تست جدید این نشست) | `py -m pytest -o addopts= -q` | ✅ **verified** |
| OFN نود میدانی | مگاپرامپت: ۱۲۲۹ تست | دسترسی به اورنج‌پای نداریم | — | ⚠️ **unverified** |
| nbb-cp-kre (`4d_system/nbb-cp-kre`) | — | اجرا نشد (only-readonly طبق DR) | — | unknown |

## نکتهٔ مهم دربارهٔ ۴۱۴/۴۰۸

`git log --all --grep="414"` و `--grep="408"` → **خروجی خالی**. کامیت‌های حاوی این عددها در تاریخچهٔ فعلی نیستند. دلیل محتمل: کامیت پاکسازی `ea69126` (2026-08-03) — «merge 40 commits, delete 39 dead branches». پس هر دو عدد فقط از یادداشت‌ها قابل‌ارجاع‌اند، نه از git زنده.

## قاعده

هر عددی که اینجا `unverified` خورده، تا اجرای موفقِ سوئیت مربوطه «fact» نوشته نمی‌شود.

## تست‌های فعال‌سازی شب 2026-08-15 (سطح A)

| تست | نتیجه |
|-----|-------|
| فلگ چت یکپارچه (endpoint) | ✅ `owner_auth_required` — گیت فلگ باز |
| صدای دکتر (ارسال واقعی TG) | ✅ `ok:true` — پیام به مالک رسید |
| زنجیرهٔ hash با ۴ ردیف | ✅ PASS 27/27 (اجرای مجدد) |
| سوئیت `_ops/tests` از ریشه | ❌ INTERNALERROR (گارد sys.exit) — رانر رسمی `run_all.py` ~۱۷min → C-006 باز با شواهد بهتر |
