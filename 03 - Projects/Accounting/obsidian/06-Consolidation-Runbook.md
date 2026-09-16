---
type: runbook
project: "[[Accounting/PROJECT]]"
status: active
layer: truth-layer
tags: [accounting, runbook, maintenance]
created: 2026-07-13
updated: 2026-07-13
---

# 06 · Consolidation Runbook — نگهداری این ساختار

> این runbookِ **عملیاتِ حسابداری** نیست (آن = [[../RUNBOOK|RUNBOOK.md]] canonical، دست‌نخورده). این نوت فقط می‌گوید چطور ساختارِ consolidated را **پاک نگه‌داری**.

## قواعد نگهداری (تا chaos برنگردد)
1. **هیچ zip جدیدی در ریشه رها نکن.** خروجی export → مستقیم به `_archive/` یا extract در جای درست.
2. **یک canonical به‌ازای هر مسئولیت** ([[03-Module-Registry]]). نسخهٔ دوم = یا آپدیت canonical یا آرشیو.
3. **بدون suffix `_1/_2/_3`.** اگر فایل جدیدتری داری، جایگزین کن و قدیمی را به `_archive` ببر.
4. **دادهٔ مالیِ واگرا** همیشه به `finance/_RECONCILE-*` می‌رود، نه overwrite.
5. **`obsidian/` = منبع حقیقت.** کد را تغییر دادی؟ نوت مربوطه را همان لحظه آپدیت کن.

## وقتی export جدید ANZ رسید
`finance/TaxPrompts/08-bank-statement-ingest-SOP.md` → `importer/anz-import.js` → dedup+reconcile → draft به صف verdict. جدول `business_transactions` تا verdict دست‌نخورده.

## وقتی consolidation بعدی لازم شد
از پرامپت آماده استفاده کن: [[../../_ecosystem/CONSOLIDATION-PROMPT-v2-FA-EN|CONSOLIDATION-PROMPT-v2]].

## بهداشت state (بعد از هر کار معنادار)
آپدیت: `PROJECT.md#Active-Context` · `DecisionLog.md` · `OpenQuestions.md` · و در تصمیم بزرگ، `MANIFEST.status_snapshot`.

## کارهای باز از consolidation 2026-07-13
- [ ] حل [[../finance/_RECONCILE-ledger-variants/README-RECONCILE|واگرایی ledger]] → ثبت به‌عنوان ACC-V13.
- [ ] تأیید [[../../_archive/DELETION-CANDIDATES|دستهٔ A حذف]] (~۴٫۷MB).
- [ ] تصمیم دربارهٔ نگهداری/حذف `_archive` بعد از یک هفته کار با درخت پاک.
