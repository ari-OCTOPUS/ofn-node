# 🗺️ MIGRATION MANIFEST — Consolidation 2026-07-13

نگاشتِ کاملِ «چه چیزی کجا رفت» برای consolidation پوشهٔ Desktop\1. هر تصمیم قابل‌ردیابی و قابل‌بازگشت است.

## ۱. خلاصهٔ اجرایی

- ورودی: **۱۹ zip** هم‌پوشان + فایل‌های loose در ریشه (سه طرح packaging موازی).
- استخراج: **۴۴۷ فایل** → فقط **۱۵۳ محتوای یکتا** (۲۹۴ کپی تکراری، ~۶۶٪).
- خروجی: سه node پاک (`Accounting`, `CryptoEtoro`, `_ecosystem`) + `_archive` با همهٔ اصل‌ها.
- **راستی‌آزمایی hash:** ۱۷۰ محتوای یکتای اصلی = ۱۴۸ در درخت پاک + ۲۲ فقط‌آرشیو (قرنطینه/stale). **صفر از دست‌رفته.**

## ۲. سه طرح packaging که کشف و reconcile شد

| طرح | تعلق | تصمیم |
|---|---|---|
| `ACC-01..05` + `Accounting-HANDOFF-COMPLETE` + `Accounting-updated-2026-07-12` | پروژهٔ **Accounting** | ACC-01..04 = canonical → `Accounting/`. ACC-05 (قرنطینه) و snapshot قدیمی → archive |
| `00_overview` … `04_data_snapshots` + `CryptoEtoro-Handoff` | پروژهٔ **CryptoEtoro** (کریپتو/ماینینگ) | union → `CryptoEtoro/` (جدا نگه‌داشته شد، به Accounting قاطی نشد) |
| `05-Finance-DropIn` (×۴) | دادهٔ مالی Accounting (FinOS) | canonical → `Accounting/finance/`؛ نسخهٔ واگرا → `_RECONCILE` |

## ۳. نگاشت canonical (source → destination)

| محتوا | منبع canonical انتخاب‌شده | مقصد |
|---|---|---|
| قانون اساسی (PROJECT/RUNBOOK/REGISTRY/VERDICT/MANIFEST/DecisionLog/OpenQuestions/INDEX) | `ACC-01-CORE-STATE` | `Accounting/` |
| xlsx خام + drafts + reports + flags | `ACC-02-DATA-and-DRAFTS` | `Accounting/data,drafts,reports,flags/` |
| کد (app بات + importer + adapter.yaml) | `ACC-03-CODE` | `Accounting/app,importer,contracts/` |
| اسناد (Tax Map/Tax-Loan/Agent-Arch/Rollout) | `ACC-04-DOCS-RESEARCH` | `Accounting/docs/` |
| بانک ANZ (Statements/Ledger/TaxPrompts/_events) | `05-Finance-DropIn-2026-07-13` (نه `_1/_2/_3`) | `Accounting/finance/` |
| meta اکوسیستم (INDEX/MEGA-PROMPT/graph.json/cockpit/README-apply) | ریشه (== `00_overview`) | `_ecosystem/` |
| FinOS blueprint + system map | ریشه | `_ecosystem/` |
| کریپتو (bots/webapp/docs/data) | `00..04` (superset از `CryptoEtoro-Handoff`) | `CryptoEtoro/` |
| handoff حسابداری (00-HANDOFF + MEGAPROMPT-Accounting) | ریشه | `Accounting/handoff/` |

## ۴. گروه‌های تکراری که به آرشیو رفتند (dedup)

| گروه | نسخه‌های تکراری (hash یکسان) | نگه‌داشته‌شد |
|---|---|---|
| Accounting HANDOFF | `Accounting-HANDOFF-COMPLETE.zip` == `_1` | محتوای درونش (ACC-01..04) |
| Finance DropIn | `05-Finance-DropIn.zip` == `_1` == `_2` | یک نسخه → `finance/` |
| Docs bundle | `03_docs.zip` == `03_docs_1.zip` | یکی → `CryptoEtoro/03_docs` |
| ledger-master xlsx | ۴ کپی یکسان (`` , `_1`, `_2`, `_3`) + کپی داخل DropIn | یک نسخه (a26a…) → `finance/Ledger` |
| snapshot قدیمی | کل `Accounting-updated-2026-07-12` (فقط ۲ فایل stale یکتا: DecisionLog/INDEX قدیمی) | نسخهٔ جدیدتر در ACC-01 |

## ۵. موارد عمداً از درخت پاک کنار گذاشته‌شده (اما در آرشیو محفوظ)

| مورد | چرا | کجا |
|---|---|---|
| `ACC-05-QUARANTINE` (۴ عکس + README) | خودِ آری در HANDOFF علامت زد «⛔ DO-NOT-FORWARD — اسکرین‌شات چت، رسید نیستند (ACC-V11)» | `_archive/…/ACC-05-QUARANTINE-DO-NOT-FORWARD.zip` |
| `Accounting/photos/` (همان ۴ عکس) | کپی همان قرنطینه | همان zip در آرشیو |
| DecisionLog/INDEX نسخهٔ 2026-07-12 | نسخهٔ کهنه (superseded توسط ACC-01) | `_archive/…/Accounting-updated-2026-07-12.zip` |

## ۶. واگرایی مالی که reconcile نشد (نیازمند verdict انسانی)

- **ledger-master**: نسخهٔ غالب `a26a…` (۸ کپی) در برابر `e03e…` (ریشه `_4` + DropIn`_3`).
- **transactions-all.csv**: دو نسخهٔ متفاوت، هر دو ۳۱۷ سطر (`2b27…` vs `abe2…`).
- طبق قاعدهٔ قفل‌شدهٔ آری («هیچ تصمیم خودکار روی دادهٔ مالی») **انتخاب نکردم**: غالب = canonical در `finance/`، واگرا در `finance/_RECONCILE-ledger-variants/`. جزئیات آن‌جا.

## ۷. راستی‌آزمایی (proof of no-loss)

```
original unique content hashes : 170
clean-tree unique hashes        : 148
missing from clean              : 22  → همگی ACC-05 قرنطینه (۱۸) + snapshot stale (۴/۲ یکتا)
all 22 present inside _archive  : ✅ (۱۹/۱۹ zip اصلی محفوظ)
```
