---
type: knowledge
project: "[[04 - Architect System/architect/PROJECT]]"
status: active
source: "[[06-EVIDENCE/OCTOPUS-TELEGRAM-WEBAPP-PHASE0-2026-08-29]]"
tags: [octopus, telegram, webapp, debugging]
created: 2026-08-29
updated: 2026-08-29
created_by: agent
sources:
  - "[[06-EVIDENCE/OCTOPUS-TELEGRAM-WEBAPP-PHASE0-2026-08-29]]"
  - "[[06-EVIDENCE/OCTOPUS-REUSE-AUDIT-2026-08-29/P1-RESULT]]"
---

# ۹۶ — Telegram/WebApp Phase 0 — evidence first

چهار نود با RUN_ID مشترک خوانده شدند. EDGE-6 هنوز بسته نیست: registry روی
۱۸۰ آخرین مرحلهٔ same-run است و transport ACK یا receipt امضاشده به‌تنهایی
effect completion را ثابت نمی‌کند.

سه درس:

1. approval countها و beatها aggregate/namespaceهای متفاوت‌اند؛ UI باید
   source/freshness را نشان دهد، نه اعداد را برابر کند.
2. root cause قدیمی EDGE-6 کامل نبود؛ ۱۸۰ اکنون دو مسیر transmit دارد و مسیر
   داخلی run ID اصلی را حفظ نمی‌کند. قبل از patch باید در worktree ایزوله به
   یک مسیر همگرا شود.
3. باگ‌های قطعیِ کوچک جدا بمانند: `undefined` از حذف `rfc_id`، queue scan
   truncation روی ۱۳۸، timeout/policy labeling و redaction واژهٔ `BEARER`.

پچ امنیتی `BEARER` در branch
`fix/bearer-secret-redaction-20260829`، commit `00c4fbf`، تست 34/34 سبز شد.
runtime deploy نشد. branch فقط به germline محلی publish شد؛ GitHub remote برای
این repository وجود ندارد.

پچ UI مستقل نیز ساخته شد: branch
`fix/miniapp-undefined-card-20260829`، commit `0016cdf`. card بی‌شناسه
read-only می‌شود و دیگر `undefined` را به `/api/actions` نمی‌فرستد؛ 28/28
تست مرتبط سبز. live branch fast-forward شد؛ gateway PID `20800→26892`؛
loopback `/miniapp` و `/app.js` هر دو 200. تأیید WebView واقعی هنوز مانده.

WebView root نیز versioned شد (reference `c43bc91`). پس از پذیرش WIP مرکز،
۱۱ suite ترکیبی پاس شد و Center `22352→23808` restart شد. poll conflict
نخستین نمونه transient بود و نمونهٔ بعد failures=0 داد. Center source هنوز
dirty است؛ provenance با SHA فایل ثبت شده، نه ادعای commit-clean.

در WebView تازه، `/api/lifecycle` واقعاً hit شد و مالک نبودِ `undefined` را
تأیید کرد. instrumentation حذف و cleanup commit `1c163ea` به germline رفت.
Persistent Menu Button هنوز شیء ثبت جدا و unversioned است؛ مسیر ثابت‌شده،
Dashboard پیام تازهٔ `/start` است.

شواهد: [[06-EVIDENCE/OCTOPUS-TELEGRAM-WEBAPP-PHASE0-2026-08-29]].
