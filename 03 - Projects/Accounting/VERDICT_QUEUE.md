# ✅ Accounting VERDICT_QUEUE

> تصمیم‌های انسانی مخصوص Accounting. Secret/PII ننویس.

---

| ID | تصمیم | گزینه‌ها | وضعیت | چرا مهم است |
|---|---|---|---|---|
| ACC-V1 | Tax Agent انتخاب شده؟ | yes/no + code/name غیرحساس | open | قواعد مالیاتی تا آن زمان unverified |
| ACC-V2 | ساختار کسب‌وکار | one Pty Ltd / multiple / sole+company / ask accountant | partial-resolved (2026-07-16: one Pty Ltd, entity_id=armin-abn) | تعیین ledger و liability |
| ACC-V3 | ABN فعال؟ | yes/no/unknown | open (placeholder در policy-profile — مالک) | invoicing و compliance |
| ACC-V4 | GST registered؟ | yes/no/unknown | partial-resolved (2026-07-16 RD-002: yes, gst_registered=true؛ basis/فرکانس BAS هنوز unknown — حسابدار) | BAS/GST workflow |
| ACC-V5 | حساب بانکی جدا؟ | yes/no | open | audit readiness |
| ACC-V6 | نرم‌افزار حسابداری | Xero/MYOB/Excel/other/none | partial-resolved (2026-07-16 ARCHITECTURE-TWO-RAILS: Xero برای ریل A انتخاب شد؛ کلیدها هنوز تنظیم‌نشده) | importer/dashboard |
| ACC-V7 | قطع MYOB اگر Xero انتخاب شود | yes/no/later | open | جلوگیری از هزینه تکراری |
| ACC-V8 | pilot 10 receipts مجاز است؟ | yes/no | open | تست OCR/categorization |
| ACC-V9 | ساخت ANZ CSV importer skeleton مجاز است؟ | yes/no | open | کاهش کار دستی |
| ACC-V10 | آیا Crypto-eToro شخصی بماند؟ | yes/no/ask accountant | open | CGT و Pty Ltd ساختار |

---

## Default recommendation

تا تصمیم حسابدار:

```text
Accounting = read-only / draft-only / no live integration
```

اولویت‌ها:

1. ACC-V1
2. ACC-V2
3. ACC-V3/4/5
4. ACC-V8 pilot
5. ACC-V9 importer skeleton
