# EQUIP-G5A-MCPV2-STATELESS-HTTP Evidence Report

**Date:** 2026-08-16
**Group:** G5 -- Infrastructure (sub-phase الف/MCPv2, STEP 2 of 2)
**Wave:** D (G5-INFRA)
**Branch:** `equip/g5-infra-20260816`
**Verdict:** PASS

---

## Executive Summary

STEP 2 فاز ۵-الف با **مسیر A** بسته شد: ترابردِ HTTP stateless (Streamable HTTP ِ
spec ِ 2025-06-18 در حالتِ stateless) **دستی و فقط با stdlib** روی همان
`_ops/octopus_mcp/server.py` پیاده شد — **پکیج `mcp` اضافه نشد** (صفر وابستگیِ نو،
همان فلسفهٔ birth این سرور). ترابردِ stdio پیش‌فرض ماند و کلاینتِ `.mcp.json`
بدونِ هیچ تغییری کار می‌کند.

## چی پیاده شد (فقط stdlib: `http.server`)

| قاعده | پیاده‌سازی |
|---|---|
| stateless واقعی | هیچ session ای نگه داشته نمی‌شود؛ `Mcp-Session-Id` نه صادر می‌شود نه پذیرفته (ارسالش توسط کلاینت ⇒ 400) — طبقِ DO NOT مگاپرامپتِ G5 |
| POST /mcp | یک پیامِ JSON-RPC در بدنه (سقفِ 1MB)؛ پاسخِ عدد‌دار ⇒ 200 + `application/json`؛ notification ⇒ 202 + بدنهٔ خالی |
| batch | list ⇒ 400 (batching در 2025-06-18 حذف شده) |
| GET /mcp · DELETE /mcp | 405 — سرورِ stateless استریمِ مستقلِ SSE نمی‌دهد و session ای برای بستن نیست |
| negotiation نسخه | `initialize` نسخهٔ کلاینت را اگر در `(2025-06-18, 2025-03-26, 2024-11-05)` باشد همان‌طور برمی‌گرداند؛ وگرنه پیش‌فرضِ سرور — مشترک بینِ هر دو ترابرد |
| health ≠ readiness | `/healthz` = liveness (پروسه زنده) · `/readyz` = readiness (موتور جستجو، fail-closed بودنِ agentignore، degradedها) — الزامِ صریحِ G5 |
| دفاعِ DNS-rebinding | Host خارج از `{localhost, 127.0.0.1, [::1], bind-host}` ⇒ 403 |
| Accept | بدونِ `application/json` (یا `*/*`) ⇒ 406 |
| اجرا | `python -X utf8 _ops/octopus_mcp/server.py --http [HOST:]PORT` — bind پیش‌فرض 127.0.0.1:8809؛ بدونِ `--http` = stdio (بی‌تغییر) |

نکتهٔ مهندسی: ردّهای زودهنگام (4xx) قبل از خواندنِ بدنه، `close_connection` می‌زنند تا
بایت‌های باقیماندهٔ بدنه، درخواستِ بعدیِ keep-alive misparse نشود (علتِ نویز
«Bad request version» در پاسِ اول — پیدا و رفع شد قبل از کامیت).

## راستی‌آزمایی

| سنجه | نتیجه |
|---|---|
| `test_octopus_mcp_http_stateless.py` (نو، ۱۳ تست، سوکتِ واقعی روی ephemeral port) | **13/13 سبز** — negotiation · بدونِ session-header · tools/list = همانِ ۵ ابزارِ stdio · hash_file روی HTTP · -32601 ابزار ناشناس · 202 برای notification · 405 برای GET/DELETE · جدا بودنِ healthz/readyz · 403 host بیگانه (GET و POST) · 406 Accept · 400 برای JSON خراب/batch/session-id جعلی |
| پروسهٔ واقعی `--http 127.0.0.1:18823` + curl | healthz/readyz/initialize/405 همه مطابق قرارداد؛ `readyz` صادقانه `engine: "rg"` و `agentignore_fail_closed: false` را گزارش کرد |
| رگرسیونِ stdio | smoke زنده: negotiation روی 2025-03-26 echo شد، notification بلعیده شد، tools/list سالم؛ **تستِ search دقیقاً همانِ baseline: ۱ شکستِ pre-existing، نه بیشتر** (کوئریِ خالی با rg — فیکسِ آن قدمِ بعد است، عمداً در این کامیت نیست) |
| وابستگی | `git diff` روی imports: فقط `http.server` از stdlib اضافه شد؛ `pip` دست نخورد |

## محدودهٔ صادقانه

- stdio مسیرِ اصلیِ ثبت‌شده در `.mcp.json` ماند؛ HTTP هنوز به هیچ کلاینتی وصل نیست
  (فقط در دسترس است: `--http`). اتصالِ واقعیِ کلاینت = رأیِ جداگانهٔ مالک.
- auth رویِ HTTP نیست — جبران: bind پیش‌فرضِ 127.0.0.1 + allowlistِ Host. اگر روزی
  رویِ شبکه‌ی غیرمحلی باز شود، token لازم دارد (یادداشت شد، انجام نشد).
- OTel/RFC 9207/SEP-990 از فهرستِ PRIMARY مگاپرامپت، features پکیجِ SDK هستند —
  در مسیرِ A (دستی) موضوعیت ندارند؛ ترجیحِ مالک: بدونِ پکیج.
- ثبتِ تستِ نو در `run_all.py` نشد (WORKLOCK) — نام برایِ ثبتِ مرکزی:
  **`test_octopus_mcp_http_stateless.py`**.

## فایل‌های این کامیت

- `_ops/octopus_mcp/server.py` — ترابردِ HTTP stateless + negotiation + readiness
- `_ops/tests/test_octopus_mcp_http_stateless.py` — ۱۳ تستِ نو
- همین evidence
