---
type: payment-verified-receipt
created: 2026-09-02T14:10Z
rule: R6 — پرداخت فقط با رسید مستقل VERIFIED · external_receipt = ANZ Transaction Report
statement: ANZ-654214278-2026-05-06_to_2026-09-02-TRANSACTION-REPORT.pdf
statement_sha256: 12e11bf23e89d79875538503 5545f474ee1c76ce0f3e3ced287d92604489fb91
account: MASTER PAINTING AND MAINTENANCE AND DESIGN PTY LTD · ANZ BSB 012233 · Acc 654214278 (balance 2 Sep 2026: $7,953.29)
privacy: ⛔ صورت‌حساب بانکی — فقط والت + بورد؛ هرگز مخزن عمومی
---

# اولین پرداخت‌های VERIFIED تاریخ اختاپوس — ۵ ردیف، سطح شاهد A (بانک)

| record_id | تاریخ | پرداخت‌کننده | مبلغ | receipt_hash (R6) | یادداشت |
|---|---|---|---|---|---|
| PAY-20260710-MPCONSTRUCT-00270 | 2026-07-10 | MP CONSTRUCT PTY | **$18,414.00** | `f2265bfd…` | Manly claim؛ ارجاع بانکی «00270» (بریده) |
| PAY-20260807-MPCONSTRUCT-002701 | 2026-08-07 | MP CONSTRUCT PTY | **$24,858.90** | `b78cae76…` | Manly فاکتور 002701 |
| PAY-20260826-MPCONSTRUCT-002702 | 2026-08-26 | MP CONSTRUCT PTY | **$16,193.10** | `de15c360…` | Manly فاکتور **002702** (= Claim No 3)؛ فاکتور $16,500 گفت، بانک $16,193.10 — اختلاف $306.90 ثبت شد، علت unknown |
| PAY-20260507-MARLBOROUGH-PAINT | 2026-05-07 | 15 Marlborough S | $637.37 | `ba11600c…` | نقاشی/آب‌بندی |
| PAY-20260506-MARLBOROUGH-PATCH | 2026-05-06 | 15 Marlborough S | $315.00 | `9a52830f…` | patching + waterproof |

- **جمع واریزی‌های Manly = $59,466.00** (از قرارداد $93,000+GST) · جمع کل پنجمی = **$60,418.37**
- قرارداد R6 برای هر ردیف: `SHA256("ANZ-654214278-<YYYYMMDD>-<PAYER>|<amount>|AUD|<received_at>|<payer>")` — payload از خود خطوط صورت‌حساب، بدون هیچ حدسی.
- هر ۵ ردیف با این شماره‌ها به `ECONOMIC-LEARNING-LEDGER.jsonl` الصاق شد (kind=payment، outcome=PAYMENT_RECEIVED_VERIFIED، snapshot_sha256 = هش صورت‌حساب) — لجر الان ۲۱ ردیف.

## تفکیک صادقانه
- **business-wide verified_payment_count = 5** (بانک‌تأیید، پنجرهٔ مه تا سپتامبر ۲۰۲۶)
- **کمپین PAINT-L5-001 = هنوز 0** (این پول‌ها از قرارداد Manly و مشتری Marlboroughند، نه کمپین DET/TfNSW)
- شرط freeze فود-فرست («تا verified_payment_count = 1») در سطح کسب‌وکار **پنج برابر** برآورده شد؛ بازکردن فریز اندام‌ها همچنان رأی مادهٔ ۱۰ مالک می‌خواهد — ایجنت خودش باز نمی‌کند.

## اثر روی زنجیرهٔ R0
حلقهٔ receipt (حلقهٔ پنجم) برای اولین بار با شاهد سنگین (بانک) بسته شد. زنجیرهٔ کامل حالا یک‌بار در دنیای واقعی طی شده است: lead → قرارداد → progress claim → payment → bank receipt → hash. حالالا (بعد از merge #101) همین مسیر برای کمپین‌های جدید قابل‌تکرار است.
