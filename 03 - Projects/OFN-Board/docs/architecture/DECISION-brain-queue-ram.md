# DecisionRecord — صف مغز RAM-only (یافته ۳۸)

**نوع: intentional · تاریخ: ۲۰۲۶-۰۸-۱۰**

## وضعیت
`WorkQueue` در `ofn/worker.py` RAM-only است؛ ledger فقط shadow دارد و
replay خودکار عمداً نیست.

## چرا عمدی
- کارهای صف مغز، کارهای «فکر کردن» هستند، نه ارسال. اگر وسط کار ری‌استارت
  بیاید، بدترین اتفاق این است که یک جواب آماده نشود — نه اینکه چیزی دوبار
  ارسال شود (ارسال‌ها از outbox می‌روند که بادوام است).
- replay خودکار از ledger خطر double-charge مغز را دارد (هر تماس هزینه دارد).

## حکم
**بدون تغییر.** صف RAM-only می‌ماند. اگر روزی کارهای صف مغز به‌قدری مهم
شدند که از دست رفتن‌شان هزینه دارد، آن وقت: SQLite queue یا owner-approved
replay از ledger — با هزینهٔ double-charge که صریح بپذیریم.

## شاهد
- `ofn/worker.py: WorkQueue` — RAM dict.
- این سند در `docs/architecture/`.
