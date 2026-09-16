---
type: doc
project: "[[03 - Projects/اونلی فنز/PROJECT]]"
status: active
tags: [creator-business, architecture]
created: 2026-07-20
updated: 2026-07-20
---

# 08 · TEST REPORT — 2026-07-20 (عددِ فرمان‌دار، نه ادعا)

محیط: git worktree ‏`parallel-agents-7bf4ec` (برنچ sprint) · Python 3.13.7 · pytest 9.1.1 · آفلاین، بدون توکن تلگرام · STOP-ORGANISM درخت زنده فعال ولی خارج از مسیر walk-up ‏worktree (SCAN-LOCK §1).

## خط پایه (قبل از کدهای sprint — همان صبح)

| runner | نتیجه |
|---|---|
| `python -m pytest tests/ -q` (ریشه) | 96 passed |
| `cd studio && python -m pytest test_saba_studio.py -q` | 16 passed |
| `cd brain && python -m pytest test_acquisition_pipeline.py test_learning.py -q` | 23 passed |
| `cd langar && python -m pytest test_langar.py test_pf_admin.py -q` | 17 passed |
| **جمع** | **152/152** |

## نهایی (پس از C0–C2 + C1 rename) — فرمان‌ها در [[../../tests/README|tests/README]]

| runner | نتیجه |
|---|---|
| `python -m pytest tests/ -q` (شامل ۹ تست compliance/standalone + ۲۱ تست state-machines جدید) | **126 passed** |
| `cd studio && python -m pytest test_creator_studio.py test_creator_brain.py test_affirm.py -q` | **43 passed** |
| `cd brain && python -m pytest test_acquisition_pipeline.py test_learning.py -q` | **23 passed** |
| `cd langar && python -m pytest test_langar.py test_pf_admin.py -q` | **17 passed** |
| `python studio/creator_brain.py --selftest` (صفر PII) | ALL PASS |
| **جمع** | **209/209 — صفر شکست** |

## معیارهای پذیرش §۷ مگاپرامپت

1. compliance ‏PASS (۷ تست + گِیت tick) ✅ · 2. illegal transitions ‏PASS ✅ · 3. dedup ‏PASS ✅ · 4. dryrun صفر-اثر ‏PASS ✅ · 5. ‏full_stop دو-هشداره finalize را می‌بندد ‏PASS (test_warning_kill + check_all_guards) ✅ · 6. هیچ تستی توکن زندهٔ تلگرام نمی‌خواهد ✅ · STOP فایل هرگز ساخته/حذف نشد (فقط monkeypatch) ✅

## ادعاهای بازنشسته

«155/155» (PROJECT.md ‏07-17) · «148» (DEEP-SCAN ‏07-17) · «100/100» (LAUNCH-RUNBOOK/PF-LAUNCH-SAFETY ‏07-16) · «29» (manifest ‏07-10). از این پس تنها مرجع: این فایل + DL-2026-07-20-TESTS.

## نکتهٔ flake

هیچ flake ای در ۳ بار اجرای کامل دیده نشد. اجرای هم‌زمانِ دو run_all موازی روی یک درخت = ریسک قفل AV ویندوز (درسِ ثبت‌شدهٔ vault) — سریالی اجرا کن.
