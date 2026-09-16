# F-GATE-VERDICT — Independent Sandbox Test Authority

> **حکم: CONDITIONAL PASS — ۱۱ از ۱۲ گیت سبز؛ یک residualِ مستندِ کوچک (F-G8).**
> بدون سبزِ کاذب: F به‌طور کامل PASS اعلام نمی‌شود تا F-G8 به‌صورتِ سخت (۰ تلاشِ external) بسته شود.
> **C هنوز شروع نمی‌شود** (طبق خوانشِ سختِ گیت‌های خودت).

## ماتریس گیت‌ها (اثبات‌شده با اجرای repo مستقل)

| گیت | وضعیت | مدرک |
|---|---|---|
| F-G1 independent repo | ✅ PASS | `git rev-parse --git-common-dir` داخلِ `F:\octopus-phase0-isolated`، نه `F:\backup\.git` |
| F-G2 همهٔ test files inventory | ✅ PASS | `test_manifest.json` از `run_all.py` (۲۴۷ direct + ۶ pytest + ۲ extra)؛ `TEST-INVENTORY.csv` |
| F-G3 همهٔ تست‌های معتبر توسط runner دیده می‌شوند | ✅ PASS | manifest-driven، subprocess-per-file (pytest-vs-direct محترم)؛ ۲۴۹/۲۴۹ اجرا |
| F-G4 full sandbox suite | ✅ PASS | **۲۴۹/۲۴۹ PASS** (`full-run-3.log`, `FULL-SANDBOX-TEST-REPORT.json`) |
| F-G5 static/lint | ✅ PASS (تغییرات) | ruff روی فایل‌های تغییرکرده clean؛ ۳ E741 پیش‌موجود در `chrono.py:94,748` (خارج از scope، دست‌نخورده) |
| F-G6 attempted_live_writes == 0 | ✅ PASS | **suite_attempted_live_writes = ۰** با barrierِ **معتبر** (۲۶۳ child با evidence، ۰ install-failure) |
| F-G7 successful_live_writes == 0 | ✅ PASS | barrier هر نوشتنِ زیرِ `F:\backup` را بلاک می‌کند (adversarial ۱۴/۱۴ + ۹/۹ re-verify) |
| **F-G8 external_network_attempts == 0** | ⚠️ **RESIDUAL** | **۶ تلاشِ external، همه بلاک‌شده** → صفر شبکه‌ی خارجی رخ داد (ایمن)، ولی attempt≠۰. نیازمندِ seam-mock در ≤۶ تست (منابعِ محتمل در `NETWORK-EFFECT-AUDIT`: email_inbound/ingest_adapter/debate-client, پورتِ paid ۴۰۰۰) |
| F-G9 secret exposure == 0 | ✅ PASS | env حساس scrub؛ هیچ مقدار secret چاپ نشد؛ manifestِ حساس فقط classification |
| F-G10 capability marker sandbox-only | ✅ PASS | runner، `run_all.__main__` (که marker می‌نویسد) را اجرا نمی‌کند؛ هر state → sandbox؛ barrier backstop |
| F-G11 before/after live evidence | ✅ PASS | barrier tripwire (attempted-writes، نه mtime) + ۲۶۳ evidence file؛ live `_ops/state` mtime هم بدون تغییر |
| **F-G12 BLOCKER-1 production-like** | ✅ PASS | **۷/۷** با ChronoDB/EffectorGate/genome-ledger/on_human_judgment **واقعی** — `unauthorized ⇒ released==0 ⇒ settled==0` |

## کشفِ صداقتِ کلیدیِ این نشست
barrier یک باگ داشت (`sys` import‌نشده) که `install()` را بی‌صدا می‌شکست → یک اجرای full قبلی «۰ live-write» گزارش داد در حالی که **barrier اصلاً نصب نشده بود** (evidenceِ باطل). **خودم گرفتم، فیکس کردم، runner را fail-loud کردم** (`os._exit(97)` روی install-failure + شمارشِ `barrier_install_failures`)، و اجرای معتبر را بازتولید کردم. mtime تنها اثبات نیست — tripwireِ فعال است.

## فیکس‌های candidate این نشست (candidate-only، NOT merged)
- BLOCKER-1 کامل (fail-closed در کل مسیر) — `88d07f2`، حالا production-like اثبات‌شده.
- L-08 memory-trust escalation — `_verify_external_grade` (بولینِ ادعاکننده ignore؛ receipt مستقل)؛ green-lieِ `test_memory_gate::t_b` اصلاح شد؛ ۷/۷ security.
- L-06 split-brain STOP — `test_stop_contract` حالا `opslib.STOP_ARCHITECT` canonical را assert و exercise می‌کند.
- root-cause ۷ شکستِ full-run: ۶ barrier-too-strict (localhost + python-subprocess، اصلاح شد)؛ ۱ live-coupling واقعی (budgets.yaml fallback به live) که sandbox آشکار کرد → seedِ سنتتیک.

## قدم بعدی (برای بستنِ کاملِ F پیش از C)
۱. شناساییِ دقیقِ ۶ تستِ external-attempt (tag per-test در runner + یک re-run) و seam-mock (طبق `NETWORK-EFFECT-AUDIT`).
۲. re-run تا **F-G8 = ۰** → F کاملاً PASS.
۳. سپس **C** (schema migration روی fixture) — طبق ترتیبِ تأییدشدهٔ تو.

## ممنوعیت‌های live: همه برقرار
merge / flags / DB-migration / restart / STOP-clear / send / paid / PocketSmith / propagation-runtime = **NOT AUTHORIZED**. live عملیاتاً دست‌نخورده (tripwireِ معتبر: ۰ live-write).
