# _ops/reconcile — دراپ‌زونِ CSVِ تطبیقِ پول (نیمه‌دستی، offline)

`reconcile.py` فایل‌های `*.csv` این پوشه را می‌خواند و پولِ نشسته را با attribution تطبیق می‌دهد.
**هیچ اتصالِ شبکه/بانک/scrape نیست** — انسان CSV را این‌جا می‌گذارد (verdict #10: reconcile نیمه‌دستی).

## فرمتِ قفل‌شده (verdict آری 2026-07-07)

هدر دقیقاً این چهار ستون (به همین نام):

```csv
date,amount_aud,lead_id,source
2026-07-05,480.00,LEAD-20260703-001,bank
```

- `date` — تاریخِ نشستنِ پول، `YYYY-MM-DD`.
- `amount_aud` — مبلغِ AUD (باید **دقیقاً** با مبلغِ CLAIMED بخورد).
- `lead_id` — همان carrier که سیستم mint کرده: `LEAD-YYYYMMDD-NNN`.
- `source` — منبعِ مستقل (bank / stripe / accounting-export / …).

## قاعدهٔ تطبیق (fail-closed، ضدِ گیم)

یک ردیف فقط وقتی `CONFIRMED` می‌شود که **هر چهار** برقرار باشند: `lead_id` موجود · attribution در وضعیتِ
`CLAIMED` · مبلغ دقیقاً match · تاریخ در **پنجرهٔ ۷ روز** از تصمیم/claim. هر چیزِ دیگر → `UNMATCHED`
(گزارش در `_ops/state/reconcile-latest.json`)، **هرگز** کریدیتِ fitness. دابل‌کلیمِ یک lead → نادیده،
CONFIRMEDِ اصلی محفوظ. `CONFIRMED` را فقط همین job می‌نویسد؛ خودگزارشیِ ایجنت هرگز معتبر نیست.

## اجرا

```powershell
python -X utf8 "F:\backup\_ops\budget\reconcile.py"          # تطبیق + نوشتنِ گزارش
python -X utf8 "F:\backup\_ops\budget\reconcile.py" --dry    # فقط گزارش، بدونِ نوشتن به ledger
```

> این پوشه tracked است تا مسیر پایدار بماند؛ فایل‌های CSVِ واقعیِ مالی را — اگر PII/حساب دارند —
> در `.gitignore` بگذار یا بیرونِ repo نگه‌دار (این README تنها راهنماست، نه دیتا).
