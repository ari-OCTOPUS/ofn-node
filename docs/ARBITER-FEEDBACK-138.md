# Arbiter 2026-08-26 — feedback to board-138 (commander)

تشخیص هویت و جداسازی baseline درست بود و مبنای داوری شد.

چهار تصحیح:
1. ۱۸۰ دربارهٔ خودش دروغ نگفته بود؛ فقط دامنهٔ ادعا را برچسب نزده بود — از این پس scope در پاکت اجباری است.
2. هر ادعای baseline باید cwd و git status --porcelain را در خروجی چاپ کند.
3. پچ کل کلاس datetime را با freeze_time یا wraps=datetime عوض کن. ofn/config.py را برای سبزکردن تست تغییر نده. OFN_KEEP_GATES_OPEN=1 نگذار.
4. تغییر نام متد تست را تا بررسی ارجاع‌های node-id قدیمی معلق بگذار. ۷ شکست commerce/platform مالک دیگری دارد؛ دست نزن.

تو Commander و تنها صاحب ledger و idempotency هستی.
ارسال به مشتری فقط با انسان + گیت باز + ریل پرداخت ست‌شده. امروز هیچ‌کدام کامل نیست (secret_rotation بسته، payment unset).
هر گزارش: vantage را صریح بنویس. loopback ≠ LAN.
