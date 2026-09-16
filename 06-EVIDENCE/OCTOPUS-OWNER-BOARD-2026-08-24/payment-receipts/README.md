# payment-receipts — پوشهٔ رسید مستقل پرداخت (رأی مالک ۶، ترکیبی)

قرارداد `external_receipt_hash` — سکلت آماده، provider API متصل نیست (2026-09-02).

## مالک چطور یک رسید ثبت می‌کند

1. فایل رسید واقعی (تصویر/PDF/صورت‌حساب بانک/ایمیل پرداخت) را با همین نام‌گذاری در این پوشه بگذار:
   `PAY-<YYYYMMDD>-<کدکوتاه>.<pdf|png|jpg|eml>`
2. در کنارش یک فایل `<همان‌نام>.receipt.json` بساز (الگوی زیر).
3. مقدار `receipt_sha256` باید دقیقاً sha256 محتوای فایل رسید باشد (فرمان راستی‌آزمایی پایین).

## الگوی receipt.json

```json
{
  "payment_id": "PAY-20260902-001",
  "amount": 0.0,
  "currency": "AUD",
  "received_at": "2026-09-02T00:00:00Z",
  "payer": "نام دقیق پرداخت‌کننده",
  "lead_id": "lead:nsw_ocp_buyer:...",
  "source": "owner-receipt-file",
  "receipt_file": "PAY-20260902-001.pdf",
  "receipt_sha256": "<sha256 فایل رسید>"
}
```

## قرارداد هش (عین فرمول کد — ofn/learning/receipts.py)

`external_receipt_hash = SHA256("payment_id|amount|currency|received_at|payer")`

این همان هشی است که `ReceiptVerifier` از رسیدِ مستقل بازمی‌سازد؛ ادعای پرداخت فقط
وقتی VERIFIED می‌شود که (۱) چنین receipt.json معتبری با فایلِ موجود موجود باشد،
(۲) هش ادعا با هش بازسازی‌شده یکی باشد، و (۳) اتصال به lead قابل‌اثبات باشد.

## قواعد آهن

- تا رسید مستقل نیاید: همهٔ ادعاها `payment_claim_unverified` می‌مانند — مطلق.
- `VERIFIED_PAYMENT_COUNT=0` باید صفر بمانَد تا اولین رسید واقعی.
- هیچ فایل رسیدی توسط ایجنت ساخته/ویرایش نمی‌شود — فقط مالک.

## راستی‌آزمایی فایل رسید (PowerShell)

```powershell
Get-FileHash 'F:\backup\06-EVIDENCE\OCTOPUS-OWNER-BOARD-2026-08-24\payment-receipts\PAY-XXXXXXXX-XXX.pdf' -Algorithm SHA256
```

خروجی باید با `receipt_sha256` در receipt.json یکی باشد.
