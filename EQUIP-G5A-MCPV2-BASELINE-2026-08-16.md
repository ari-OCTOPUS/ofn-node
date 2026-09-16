# EQUIP-G5A-MCPV2-BASELINE Evidence Report

**Date:** 2026-08-16
**Group:** G5 -- Infrastructure (sub-phase الف/MCPv2, STEP 1 of 2)
**Wave:** D (G5-INFRA)
**Branch:** `equip/g5-infra-20260816`
**Verdict:** PASS (baseline locked)

---

## Executive Summary

STEP 1 فاز ۵-الف بسته شد: وضعیتِ «قبل» از سرورِ MCP ِ محلی (`_ops/octopus_mcp/server.py`)
در `_ops/tests/_baselines/mcpv2-baseline.txt` **قفل** شد — شاملِ اجرایِ verbatim تستِ
مرجع، پروب‌های زندهٔ موتور جستجو، و inventory پروتکل.

## چرا این قفل لازم بود

کارِ STEP 2 (ترابردِ stateless ِ HTTP روی همان `server.py`) ریسکِ رگرسیون روی
مسیرِ stdio دارد که کلاینتِ `.mcp.json` به آن وصل است. بدونِ baseline قفل‌شده،
«سبز بودنِ بعد» قابلِ راستی‌آزمایی نیست (درسِ INV-8: خودگزارش بی‌اعتماد؛ شاهد بگیر).

## کشفِ مهمِ حینِ قفل (root-cause، شاهدِ زنده)

ماشین از ~2026-08-06 به بعد **rg سیستمی گرفته** (winget: ripgrep 15.2.0 در PATH).
`server._find_rg()` آن را می‌یابد ⇒ موتورِ `search_hybrid` عملاً از `py-tracked-only`
به `rg` سوئیچ کرده — بدونِ اینکه تستی این تغییرِ موتور را پوشش بدهد. نتیجه:

1. **تستِ مرجع همین الان ۱ شکست دارد** (pre-existing، ثبت‌شده در baseline):
   `t_empty_query_is_handled` — کوئریِ `"   "` با rg پنج hit جعلی برمی‌گرداند
   (خطوطِ تورفتگی) در حالی که قراردادِ fallback می‌گوید `[]` + `empty-query`.
2. **کوئریِ فاصله‌ای با rg دگرگون شده**: `"search rg"` → صفر hit، چون کلِ رشته
   به‌عنوان یک regex (عبارتِ پیوسته) به rg می‌رود؛ قراردادِ `_match_terms`
   (AND رویِ واژه‌ها، مستقل از ترتیب — خطِ `def _rg_search(` را باید بیابد) نقض می‌شود.

این دقیقاً همان «مشکلِ رفتار rg روی کوئریِ فاصله‌ای» است که در مرحلهٔ بعدِ فاز فیکس می‌شود —
اول قفل، بعد فیکس؛ نه برعکس.

## روش

| قلم | مقدار |
|---|---|
| اجرای تست | `PYTHONIOENCODING=utf-8 python -X utf8 _ops/tests/test_octopus_mcp_search.py` → ۱ FAIL از ۵ (verbatim در baseline) |
| پروب موتور | سه `t_search_hybrid` زنده روی درختِ واقعی (خروجی در baseline) |
| inventory | stdio-only · PROTOCOL_VERSION ثابتِ "2025-06-18" · ۵ ابزار · بدون session · ثبتِ `.mcp.json` بدون تغییر |
| git | base `0fff585`؛ `server.py` و تست در لحظهٔ قفل clean (تغییراتِ commit‌نشدهٔ مالک دست‌نخورده) |

## محدودهٔ صادقانه

- این STEP فقط «ثبتِ وضعیت» است؛ هیچ کدی تغییر نکرد.
- `run_all.py` دست نخورد (WORKLOCK) — `test_octopus_mcp_search.py` در آن ثبت نیست و ثبتشکارِ من نیست؛ فقط گزارش.
- baseline یک snapshot از درختِ زنده است؛ کامیت‌های موازیِ فرایندهای زنده (مثل `0fff585` که حینِ کار آمد) در آن ضبط شده‌اند.

## قدم بعدی

STEP 2: پیاده‌سازیِ دستیِ ترابردِ stateless (Streamable HTTP ِ spec 2025-06-18) روی
همان `server.py` با فقط stdlib — **بدونِ افزودنِ پکیج `mcp`** (مسیر A). سپس فیکسِ rg
طبق دو پروبِ baseline.
