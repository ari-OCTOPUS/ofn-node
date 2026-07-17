# SOP — ingest استیتمنت بانکی (همین پروتکل اجراشده)
> ⚠️ **[Unverified — Registered Tax Agent to confirm]** · ایجنت **draft-only** است: هرگز lodge نمی‌کند، هرگز پول جابه‌جا نمی‌کند، هر خروجی پیشنهاد است تا verdict آری. GST مبالغ inclusive = `total/11`. Epistemic tags اجباری.

1. PDF → text (`pdftotext -layout`) یا CSV مستقیم.
2. Parse: date/desc/withdrawal/deposit/balance (+ 'blank' placeholders ANZ).
3. **txn_id = sha1(account|date|desc|w|d|balance)[:12]** → dedup ایدمپوتنت؛ تکراری = ثبت نشود، فقط لاگ.
4. **Reconcile اجباری:** opening + Σdep − Σwdr = closing · running balance per-row · تطبیق با Total Deposits/Withdrawals هدر. هر mismatch → STOP + گزارش.
5. Continuity: closing هر statement = opening بعدی (gap → در Registry ثبت).
6. Categorize (rules→draft، confidence، flags: ASSOCIATE/DIV7A/AUSTRAC≥10k/REMITTANCE).
7. خروجی: append به `_events/ingest-<date>.jsonl` + Ledger xlsx rebuild + Registry update.
8. نام کانونی PDF: `ANZ-BE_stmt<NN>_<from>_<to>.pdf` — تاریخ‌ها همیشه حفظ.
