# EQUIP-G5A-MCP-SEARCH-RG-FIX Evidence Report

**Date:** 2026-08-16
**Group:** G5 -- Infrastructure (sub-phase الف/MCPv2، فیکسِ تکمیلی پس از baseline)
**Wave:** D (G5-INFRA)
**Branch:** `equip/g5-infra-20260816`
**Verdict:** PASS

---

## Executive Summary

باگِ «رفتار rg روی کوئریِ فاصله‌ای» (و کوئریِ خالی) در `search_hybrid` فیکس شد و
تستِ مرجع — که در baseline با ۱ شکستِ pre-existing قفل شده بود — حالا **کاملاً سبز**
است: `test_octopus_mcp_search.py` **۶/۶**.

## ریشه (شاهد در EQUIP-G5A-MCPV2-BASELINE)

`rg` از طریقِ winget روی PATH این ماشین آمده بود (ripgrep 15.2.0) ⇒ موتورِ
جستجو بدونِ هیچ تغییرِ کدی از `py-tracked-only` به `rg` سوئیچ کرد، و دو قراردادِ
مستندِ fallback پایتونی زیر پا افتاد:

1. **کوئریِ فقط‌فاصله** (`"   "`): الگوی خام به rg می‌رفت و خطوطِ تورفتگیِ فایل‌های
   md را hit می‌کرد (۵ hit جعلی در پروبِ baseline) — fallback می‌گوید `[]` + `empty-query`.
2. **کوئریِ چندواژه‌ای** (`"search rg"`): کلِ رشته یک regex/عبارتِ پیوسته می‌شد ⇒
   صفر hit؛ در حالی که قراردادِ `_match_terms` (AND رویِ واژه‌ها، مستقل از ترتیب —
   docstringِ خودِ `_py_search`) حکم می‌کند خطِ `def _rg_search(` پیدا شود.

## فیکس (`_rg_search` در server.py)

- کوئریِ بدونِ واژه ⇒ `([], "empty-query")` — قبل از اجرای rg، مثلِ fallback.
- تک‌واژه ⇒ همان regex-capableِ همیشگی (رفتار قبلی حفظ شد).
- چندواژه ⇒ rg با الگوی ORِ واژه‌های escape‌شده فقط **خطوطِ کاندید** را می‌یابد
  (`-m 25` چون فیلتر می‌کُشد) و فیلترِ AND رویِ واژه‌ها در پایتون می‌نشیند —
  mirrorِ smart-case (`query == query.lower()`) با رفتارِ `-S` سازگار است.

## راستی‌آزمایی

| سنجه | نتیجه |
|---|---|
| `test_octopus_mcp_search.py` (۴ تستِ قبلی + ۲ پینِ نوِ rg) | **۶/۶ سبز** — از جمله: empty-query با engine=rg ⇒ صفر hit + علامتِ `empty-query`؛ «search rg» با ترتیبِ معکوس ⇒ `def _rg_search(` پیدا می‌شود و **هر hit هر دو واژه را دارد** |
| قرمزیِ پین‌ها روی کدِ قدیم | هر دو پینِ نو دقیقاً همان دو پروبِ قرمزِ baseline اند (pre-fix: ۵ hit جعلی / ۰ hit) |
| رگرسیونِ ترابردِ HTTP (STEP 2) | `test_octopus_mcp_http_stateless.py` همچنان **13/13** |
| رگرسیونِ fallback | بدونِ rg (env به مسیرِ ناموجود) همان مسیرِ `_py_search` دست‌نخورده می‌ماند — کدِ fallback تغییر نکرد |

## محدودهٔ صادقانه

- خطوطِ بلندتر از ۳۰۰ ستون: rg برش می‌دهد؛ اگر واژه‌ای فقط بعد از ستونِ ۳۰۰ باشد،
  فیلتر آن خط را می‌اندازد (خروجی هم‌پایانِ ۳۰۰ است — قابل‌قبول، ثبت شد).
- `-m 25` کاندید در فایل: در بدترین حالت چند خطِ one-term-only فیلتر می‌شوند؛
  سقفِ سراسریِ `cap` پابرجاست.
- ثبتِ تغییری در `run_all.py` ندادیم (WORKLOCK) — `test_octopus_mcp_search.py`
  همچنان فقط گزارش می‌شود.

## فایل‌های این کامیت

- `_ops/octopus_mcp/server.py` — فقط `_rg_search`
- `_ops/tests/test_octopus_mcp_search.py` — ۲ پینِ نو + به‌روزرسانیِ docstring
- همین evidence
