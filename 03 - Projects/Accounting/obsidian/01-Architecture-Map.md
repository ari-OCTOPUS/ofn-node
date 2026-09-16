---
type: reference
project: "[[Accounting/PROJECT]]"
status: active
layer: truth-layer
tags: [accounting, architecture, obsidian-first]
created: 2026-07-13
updated: 2026-07-13
---

# 01 · Architecture Map

> واقعیتِ فنی بعد از consolidation. **توجه:** برخلاف فرضِ اولیه، این پروژه **Node.js** است نه Python/pandas.

## مرزهای ماژول (module boundaries)

```
Accounting/  (node = tenant #1)
├── [حاکمیت/state]   PROJECT · MANIFEST · RUNBOOK · REGISTRY · VERDICT_QUEUE · DecisionLog · OpenQuestions · INDEX
├── app/             بات تلگرام + داشبورد (Node.js + better-sqlite3 + express + chart.js)
│                    bot.js · database.js · personal-dashboard.js · business-dashboard.js
├── importer/        ANZ CSV → draft ledger (Node.js، بدون شبکه/secret)
│                    anz-import.js · config.js · anz-import.test.js (۱۳/۱۳✅)
├── contracts/       adapter.yaml  ← رابط read-only به Octopus (تنها سطحِ اتصالِ ماشین‌خوان)
├── data/            xlsx خام «حساب کتاب» (PII) — هرگز وارد LLM
├── finance/         FinOS drop-in: Statements(ANZ PDF) · Ledger · TaxPrompts(۱۳) · _events(JSONL)
├── docs/            Tax Map · Tax-and-Loan · Agent-Architecture · Ecosystem-Rollout
├── drafts/·reports/·flags/   خروجی‌های draft/[Unverified]
├── handoff/         MEGAPROMPT ایجنت + HANDOFF-README
└── obsidian/        ★ لایهٔ حقیقت (این نوت‌ها)
```

## اصولِ جداسازی (چه چیزی از چه چیزی جداست)
- **business logic ⟂ I/O**: قواعد مالیاتی/GST در `importer/config.js` + منطق در `anz-import.js`؛ ذخیره‌سازی در `database.js`/SQLite. UI (بات/داشبورد) از منطق جداست.
- **draft ⟂ committed**: importer فقط `draft-<date>.json` می‌سازد؛ جدول `business_transactions` تا **verdict** دست‌نخورده.
- **PII ⟂ LLM**: دادهٔ حساس در `data/` و `finance/` می‌ماند؛ فقط مقادیر tokenize‌شده به مدل می‌رسند.
- **node ⟂ node**: `CryptoEtoro/` عمداً بیرون از Accounting نگه‌داشته شد؛ اتصال فقط از مسیر tax-touchpoint (نه merge کد).

## Model tiering (از MANIFEST)
`Haiku (OCR/extract) → Sonnet (categorize) → Opus (compliance-risk)`.

## آنچه ساخته‌شده در برابر طراحی‌شده
| قابلیت | وضعیت |
|---|---|
| `anz_csv_importer` | ✅ BUILT + VALIDATED |
| `associates_registry` | 🟡 DRAFT (پنجرهٔ تاریخی) |
| `compliance_monitor` | ⚪ DESIGNED — not built |
| `receipt_ocr_pipeline` | ⚪ DESIGNED — blocked-on-data (صفر رسید واقعی) |
| `vendor_category_learner` | ⚪ PROPOSED |
| `p_and_l_dashboard` (ecosystem) | ⚪ DESIGNED — blocked on upstream |

## وابستگی‌های خارجی نیازمند auth
ANZ bank CSV export (PS Export = منبع حقیقت) · Xero API (proposed) · Registered Tax Agent (انسان — بلاکر #۱).
