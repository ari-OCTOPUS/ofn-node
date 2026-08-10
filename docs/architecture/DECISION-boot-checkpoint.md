# DecisionRecord — boot TRUNCATE checkpoint

**یافته ۳۴ (intentional) · تاریخ: ۲۰۲۶-۰۸-۱۰**

## سؤال
boot هر DB را با `PRAGMA wal_checkpoint(TRUNCATE)` می‌بندد. این پنجرهٔ
پرریسک checkpoint است — آیا بعد از قطع برق، فایل سازگار می‌ماند؟

## شبیه‌سازی (روی برد)
```
write ۱۰۰ ردیف در WAL با synchronous=FULL
→ اتصال بدون close تمیز رها شد (معادل kill -9)
→ reopen + quick_check
quick_check: ok
rows: 100
```

## نتیجه
فایل بعد از crash شبیه‌سازی‌شده سازگار است و هیچ ردیفی از دست نرفته.
boot checkpoint (TRUNCATE) روی این برد امن است: WAL با `synchronous=FULL`
نوشته می‌شود، پس هر commit یا کامل است یا اصلاً نیست.

## حکم
**boot checkpoint باقی می‌ماند.** دلیل: بعد از قطع برق، WAL باید fold شود
تا فایل واحد باشد؛ انجامش در boot به‌معنای باز کردن فایل تمیز در همان
اول کار است. شبیه‌سازی واقعی قطع برق (خاموش‌کردن برد وسط نوشتن) هنوز
انجام نشده — این یک چک «منتظر قدرت واقعی» است، نه جایگزین آن.

## شاهد
- `ofn/adapters/boot.py: _check_dbs` — checkpoint بعد از quick_check.
- این سند در `docs/architecture/`.
