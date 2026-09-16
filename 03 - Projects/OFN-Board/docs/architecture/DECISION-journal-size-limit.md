# DecisionRecord — journal_size_limit و checkpoint

**یافته ۳۳ (verify) · تاریخ: ۲۰۲۶-۰۸-۱۰**

## سؤال
`PRAGMA journal_size_limit = 4MB` با سیاست «checkpoint به‌ندرت» tension دارد
یا نه؟ آیا باعث checkpoint های ناخواسته می‌شود؟

## اندازه‌گیری (روی برد، Python 3.13، SQLite همان نسخهٔ سرویس)
```
WAL size بعد از ۲۰۰ commit کوچک:  1,240,152 bytes
WAL size بعد از ۴۰۰ commit کوچک:  1,236,032 bytes
```

## نتیجه
WAL به ~۱.۲MB می‌رسد و بعد پایدار می‌ماند — یعنی SQLite در مرز limit
(۴MB) checkpoint ضمنی می‌زند، ولی این اتفاق فقط بعد از ~۶۵۰ commit کوچک
می‌افتد و WAL هرگز به حد limit نمی‌رسد. روی این برد که حجم نوشتن روزانه
پایین است (لجر + outbox + inbox)، این یعنی در عمل **چند checkpoint در روز،
نه بیشتر**.

## حکم
`journal_size_limit = 4MB` **باقی می‌ماند** — رفتار سنجیده شد و پایدار است.
اگر روزی حجم نوشتن چند برابر شد (مثلاً vendor واقعی با وب‌هوک سنگین)،
دوباره اندازه بگیر؛ حد را حذف نکن مگر شواهد جدید بگوید.

## شاهد
- `ofn/adapters/sqlite_base.py: PRAGMAS` — limit سر جای خود.
- این سند در `docs/architecture/` — جواب «چرا این عدد» اینجاست.
