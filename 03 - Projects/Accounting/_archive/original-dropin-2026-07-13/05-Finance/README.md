# 💰 05 - Finance — لایهٔ مالی عرضی (FinOS drop-in)
> طبق `FINANCIAL-OS-BLUEPRINT-v1 §5` — event-sourced، draft-only، [Unverified تا Registered Tax Agent].
> **کشف کلیدی این ingest:** نام حساب = «MASTER PAINTING AND MAINTENANCE AND DESIGN **PTY LTD**» → شواهد بانکی برای سؤال ساختار (C3/A1)؛ حکم نهایی با مالک+حسابدار.

```
05 - Finance/
├── README.md              ← تو اینجایی
├── Statements/            ← REGISTRY.md + PDFهای کانونی (تاریخ‌ها در نام فایل حفظ)
├── Ledger/                ← ledger-master xlsx + CSV + reconciliation-meta
├── _events/               ← ingest JSONL (append-only — هرگز ویرایش نکن)
└── TaxPrompts/            ← ۱۳ پرامپت مالیاتی استرالیا (00-INDEX را ببین)
```

**گردش‌کار:** statement جدید → `TaxPrompts/08-bank-statement-ingest-SOP.md` → dedup+reconcile خودکار → Ledger rebuild → فلگ‌ها به صف verdict.
**قواعد قفل:** GST=total/11 · dedup(txn_id) · هرگز lodge/پرداخت · PII به بیرون نمی‌رود · هر عدد برنامه‌ای و قابل بازتولید.
