---
type: moc
project: "[[Accounting/PROJECT]]"
status: active
layer: truth-layer
tags: [accounting, moc, obsidian-first, octopus]
created: 2026-07-13
updated: 2026-07-13
---

# 00 · MOC — Accounting System (Truth Layer)

> این نوت **نقطهٔ ورودِ** پروژهٔ Accounting بعد از consolidation 2026-07-13 است. لایهٔ `obsidian/` = **منبع حقیقتِ معماری**؛ کد باید با آن هم‌خوان بماند، نه برعکس.

## این پروژه در یک خط
قلبِ مالیِ اکوسیستم (**tenant #1**) که درآمد همهٔ پروژه‌ها را برای ATO تجمیع می‌کند. فاز فعلی: **manifest-complete، data-partial، execution-not-started**. کف خودمختاری: **read-only / draft-only** تا انتخاب Registered Tax Agent.

## ناوبری لایهٔ حقیقت
- [[01-Architecture-Map]] — نقشهٔ ماژول‌ها و مرزها
- [[02-Data-Flow]] — جریان داده از بانک تا BAS draft
- [[03-Module-Registry]] — مالکیت canonical هر ماژول
- [[04-Dedup-Decisions]] — چه ادغام/آرشیو شد و چرا
- [[05-Octopus-Integration-Readiness]] — درزهای اتصال به مغز مرکزی
- [[06-Consolidation-Runbook]] — نگهداری همین ساختار

## قانون اساسی (source of truth واقعیِ آری — دست‌نخورده)
- [[../PROJECT|PROJECT.md]] — شناسنامه + Active Context
- [[../MANIFEST|MANIFEST.yaml]] — قرارداد ماشین‌خوان اتصال به مغز مرکزی
- [[../RUNBOOK|RUNBOOK.md]] · [[../REGISTRY|REGISTRY.md]] · [[../VERDICT_QUEUE|VERDICT_QUEUE.md]]
- [[../DecisionLog|DecisionLog.md]] · [[../OpenQuestions|OpenQuestions.md]] · [[../INDEX|INDEX.md]]
- [[../contracts/adapter|contracts/adapter.yaml]] — ★ درزِ Octopus

## قواعد قفل‌شده (immutable بدون verdict + حسابدار)
1. هیچ ایجنت **مشاورهٔ مالیاتی** نمی‌دهد — همه `[Unverified — accountant to confirm]`.
2. ایجنت هرگز به **ATO/ASIC lodge** نمی‌کند.
3. ایجنت هرگز **پول جابه‌جا/پرداخت** نمی‌کند.
4. **PII** (نام/مبلغ/شمارهٔ حساب) هرگز وارد LLM نمی‌شود — قبل از inference tokenize.
5. `GST = total / 11` (inclusive) — **نه** `amount * 0.10`.
6. ANZ import: dedup روی ستون `ID` + reconcile روی `Closing Balance`.
7. read-only تا باز شدن Security Gate.

## وضعیت (snapshot 2026-07-13)
| محور | وضعیت |
|---|---|
| importer (ANZ CSV → draft) | **BUILT + VALIDATED** (۱۳/۱۳ تست + ۱۶۰ tx واقعی، draft-only) |
| associates sub-ledger | DRAFT (AUG–NOV 2024) |
| دفتر زنده / BAS | هنوز نه (FY2025-26 خالی) |
| بلاکر #۱ | انتخاب **Registered Tax Agent** + رجیستر انطباق ناقص (ACN/ABN/GST) |
| verdictهای باز | ~۱۰ (ACC-V1..V7, V10..V12) |

## بلاکرهای P0 (از [[../MANIFEST|MANIFEST]])
انتخاب حسابدار · «یک Pty Ltd یا چند شرکت؟» · جداسازی حساب شخصی/بیزنس · تکمیل رجیستر انطباق · وضعیت کارگری (Behzad/Reza: employee یا contractor؟).

## کارِ باز از این جلسه
- [[../finance/_RECONCILE-ledger-variants/README-RECONCILE|حل واگرایی ledger]] (دو نسخه).
- تأیید [[../../_archive/DELETION-CANDIDATES|حذف تکراری‌ها]].
