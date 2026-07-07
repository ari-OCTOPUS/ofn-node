---
type: proposal
status: ready
created: 2026-07-05
updated: 2026-07-05
extends: "[[BUILD-BACKLOG]]"
tags: [status, correction, build-backlog, verified]
---

# اصلاحِ وضعیتِ BUILD-BACKLOG (۲۰۲۶-۰۷-۰۵ · verify شده روی کدِ زنده)

> [[BUILD-BACKLOG]] (نوشته‌شده ۰۷-۰۴) را **بازنویسی نمی‌کند** — کنارش می‌نشیند. هدف: جلوگیری از دوباره‌کاری. عدم‌به‌روزیِ همان سندِ BACKLOG بعد از یک batchِ ساختِ ۰۷-۰۴ ۱۶:۵۶–۱۶:۵۷ باعثِ این شکاف شد.

## روشِ verify
هر milestone را با اجرای واقعیِ تست + grep روی کدِ واقعی چک کردم (نه با خواندنِ سند). محیط: Python 3.13.7، `PYTHONIOENCODING=utf-8` لازم است (کنسولِ ویندوز cp1252 پیش‌فرض با خروجیِ فارسی نمی‌سازد).

## نتیجه

| M | ادعای BACKLOG | وضعیتِ واقعی | شاهد |
|---|---|---|---|
| M0 | سوئیت قرمز (N-01) | ✅ سبز | `run_tests.py`=9/9، `test_phase3.py`=8/8، `test_igk_integration.py`=3/3، `test_milestones.py`=4/4، `test_failures.py`=7/7 → **۳۱/۳۱** |
| M1 | fallbackِ بی‌صدا | ✅ بسته شده | `config.py:78 IGK_REQUIRED=True`؛ `orchestrator.py:87` واقعاً halt می‌کند (`_stop(...)`)، نه fallback |
| M2 | ActuationGate فقط finalize | ✅ بسته شده | `orchestrator.py:47` → `ActuationGate(...)` واقعی ساخته و به `ToolGateway(gate=...)` پاس داده می‌شود؛ `tools.py: ToolGateway.call` واقعاً `self.gate.act(...)` صدا می‌زند |
| M3 | mockِ جعلی | ✅ بسته شده | `config.py:79 SAFE_DEGRADE=True`؛ `llm.py:66-68` پیشوندِ `[DEGRADED]` |
| M4 | فقط AILab | ✅ بسته شده | `langar/tests/test_budget_m4.py` → ۵/۵ سبز؛ پوشش در `ailab.py/bot.py/brain_router.py/main.py/migrations.py` |
| M5 | بدونِ بکاپ | ✅ بسته شده | `_ops/backup/{backup.ps1,restore.ps1,backup_selftest.py}` موجود؛ `backup_selftest.py` را زدم → `integrity=ok, value=42` |
| **M6** | tracer بی‌call-site | 🔴 **همچنان باز** | grep در `langar/` صفر نتیجه (فقط match در `venv/httpcore` بی‌ربط) — G-08 دست‌نخورده |
| M7 | پنلِ هیوریستیک | ✅ بسته شده | `panel.py:44-56` رأی از `provider.complete()` استخراج می‌شود؛ `_decide` فقط fallback |
| M8 | ارتقا فقط امتیازی | ✅ بسته شده | `self_update.py` → `STRESS_GATED_PROMOTION`/`masked`/`stress_ok`؛ تست تأیید کرد |

## یافتهٔ جانبی (مهم)
`src/optimizer.py` تنها فایلی بود که mtime‌اش با batchِ ۰۷-۰۴ ۱۶:۵۶ نمی‌خواند (قدیمی‌تر، ۲۵ژوئن) → **G-04 (Goodhart-by-construction در eval) هنوز واقعاً باز است**، مستقل از BUILD-BACKLOG. M7 رأیِ پنل را واقعی کرد ولی خودِ حلقهٔ بهبود همچنان از rubricِ کیواژه‌ای تغذیه می‌شود.

## نتیجه برای گامِ بعد
تنها کارِ genuine باقی‌مانده در scopeِ BUILD-BACKLOG فعلی: **M6 (observability)**. بعد از آن، کارِ نو (خارج از این backlog): G-04 (eval بیرونی)، G-16 (langar-pro schema)، G-15→G-26 (اثباتِ LIVE، بعد از باز شدنِ کاملِ گیت).

*propose-only. سندِ اصلی [[BUILD-BACKLOG]] دست‌نخورده می‌ماند.*
