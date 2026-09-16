---
type: decision-record
project: "[[Accounting/PROJECT]]"
status: active
layer: truth-layer
tags: [accounting, dedup, migration, decisions]
created: 2026-07-13
updated: 2026-07-13
---

# 04 · Dedup Decisions

> هر حذف/ادغام/آرشیو با دلیل. مرجع کامل: [[../../_archive/MIGRATION-MANIFEST|MIGRATION-MANIFEST]].

## آمار
- ۱۹ zip → ۴۴۷ فایل استخراجی → **۱۵۳ محتوای یکتا** (۶۶٪ تکراری).
- راستی‌آزمایی hash: **صفر داده از دست رفت** (۱۴۸ در درخت پاک + ۲۲ فقط‌آرشیو، همه در `_archive`).

## تصمیم‌های canonical
| مسئله | تصمیم | دلیل |
|---|---|---|
| سه طرح packaging موازی (`ACC-*`, `Accounting-*`, `Accounting-updated`) | canonical = `ACC-01..04` | جدیدترین، کامل‌ترین، مطابق HANDOFF-README خودت |
| snapshot `Accounting-updated-2026-07-12` | آرشیو | فقط ۲ فایل stale یکتا داشت (DecisionLog/INDEX قدیمی) |
| `CryptoEtoro` در برابر `Accounting` | **جدا نگه‌داشته شد** | دو پروژهٔ متفاوت‌اند؛ merge کد اشتباه بود |
| meta اکوسیستم (graph/cockpit/MEGA-PROMPT) | به `_ecosystem/` | سطحِ Octopus، نه Accounting |
| `05-Finance` | زیر `Accounting/finance/` | دادهٔ مالیِ همین node (FinOS) |

## آرشیو (نه حذف)
| مورد | چرا نگه‌داشته شد |
|---|---|
| `ACC-05-QUARANTINE` (۴ عکس + README) | خودت علامت زدی «⛔ DO-NOT-FORWARD» — اسکرین‌شات چت، رسید نیستند (ACC-V11) |
| همهٔ ۱۹ zip اصلی | backup تا اطمینان کامل به درخت پاک |
| نسخهٔ واگرای مالی (`_4`/`e03e` + DropIn`_3`) | نیازمند verdict — [[../finance/_RECONCILE-ledger-variants/README-RECONCILE|RECONCILE]] |

## تکراری‌های امنِ حذف (byte-identical، منتظر تأیید تو)
`Accounting-HANDOFF-COMPLETE…_1.zip` · `05-Finance-DropIn…_1/_2.zip` · `03_docs_1.zip` · `ledger…_1/_2/_3.xlsx` → **~۴٫۷MB**. جزئیات: [[../../_archive/DELETION-CANDIDATES|DELETION-CANDIDATES]].

## قواعدی که رعایت شد
- قواعد قفل‌شده با هیچ سند بیرونی overwrite نشد.
- هیچ تصمیم خودکار روی **دادهٔ مالی** (واگرایی فقط flag شد).
- هر حذفِ نهایی پشتِ verdict انسانی می‌ماند.
