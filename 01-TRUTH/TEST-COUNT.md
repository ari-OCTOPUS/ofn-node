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
| کل مخزن کاری Desktop | — | **320 passed in 10.47s** (بازمقایسهٔ جاروی تست 2026-08-15 شب) | `py -m pytest -o addopts= -q` | ✅ **verified** |
| رصدخانه (working) — بازشماری جاروی تست | مگاپرامپت: 115 | **116 passed in 1.07s** (+۱ نسبت به ادعا؛ ۹۳→۱۱۶ رشد از نشست‌ها) | `py -m pytest _ops\observatory\tests\ -o addopts= -q` | ✅ **verified: ۱۱۶ زنده** |
| bayes (working) | 21 | **21 passed in 0.26s** | `py -m pytest _ops\observatory\tests\test_bayesian.py -o addopts= -q` | ✅ **verified** |
| سوئیت 4d_system (نخستین ثبت در این دفتر) | — | **265 tests: 261 pass + 4 pre-existing failures** (test_self_code_gate → C-013) | `cd 4d_system && python tests/run_all.py` | ⚠️ verified با ۴ شکستِ ریشه‌یابی‌شده |
| تست نوِ حلقهٔ حافظه (C-012) | — | **12 passed** | `python -m pytest tests/test_memory_loop_c012.py -o addopts= -q` (در 4d_system) | ✅ verified |
| تست نوِ fold غنی (T1b) | — | **4 passed** | `python -m pytest tests/test_consolidation_fold_rich.py -o addopts= -q` (در _ops) | ✅ verified |
| `_ops/tests/test_epistemic_bayes.py` | — | **صفر تابع تست** (فایل docstring-only؛ grep -c "def test_" → 0) | grep | ⚠️ مرده — مرتبط C-007 |
| epistemics — خانوادهٔ کامل (جاروی تست T3) | ۶۵ یا ۱۳۳ | **۱۷۷ چکِ سبز** در ۱۱ فایلِ خوداعتبارسنج (+۳۷ مجاور = ۲۱۴) — همه exit 0 | `python -X utf8 <file>.py` در `_ops/tests` | ✅ verified → C-007 بسته |
| سوئیت رسمی `_ops` (T2 — نخستین اجرای کاملِ ثبت‌شده) | — | **۲۴۰ فایل سبز (۲۹۳۱/۲۹۳۱ چک) + ۱۶ فایل شکست** (۱۵ pre-existing + ۱ فیکس‌شده در حینِ اجرا) | `cd _ops/tests && python -X utf8 run_all.py` (~۲۳min؛ لاگ: `_baselines/run-all-output-20260815-sweep.log`) | ✅ verified → C-006 بسته |
| endpoint چت یکپارچه + رگرسیونِ فیکس (T7) | — | **6/6** (تست نو: ترافیکِ واقعیِ now=None بدون message_id) | `python -X utf8 test_octopus_chat_endpoint.py` | ✅ verified |
| nbb-cp-kre (T9 — نخستین اجرای ثبت‌شده) | unknown | **21 passed in 30.68s** | `cd 4d_system/nbb-cp-kre && python -m pytest tests -o addopts= -q` | ✅ verified |
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
