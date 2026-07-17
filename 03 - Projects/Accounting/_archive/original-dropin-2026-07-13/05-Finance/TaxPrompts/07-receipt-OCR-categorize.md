# رسید → OCR → دسته‌بندی draft
> ⚠️ **[Unverified — Registered Tax Agent to confirm]** · ایجنت **draft-only** است: هرگز lodge نمی‌کند، هرگز پول جابه‌جا نمی‌کند، هر خروجی پیشنهاد است تا verdict آری. GST مبالغ inclusive = `total/11`. Epistemic tags اجباری.

**ورودی:** عکس/PDF رسید در Inbox. **استخراج:** {date, vendor, ABN, total, GST(=total/11 اگر inclusive و مشمول), items}.
**قدم‌ها:**
1. OCR (tier: Haiku) → فیلدها با confidence.
2. match با Ledger (تاریخ±3روز، مبلغ دقیق) → لینک txn_id؛ نبود match → «unmatched-receipt».
3. دسته از CoA + scope پیشنهادی؛ vendor جدید → به vendor-map اضافه (پیشنهادی).
4. فایل رسید → `05-Finance/Receipts/<FY>/<date>_<vendor>_<amount>.jpg` + ثبت در ledger note.
**قرارداد:** هیچ رسیدی دور انداخته نمی‌شود؛ نگهداری ≥5 سال؛ خروجی همیشه draft.
