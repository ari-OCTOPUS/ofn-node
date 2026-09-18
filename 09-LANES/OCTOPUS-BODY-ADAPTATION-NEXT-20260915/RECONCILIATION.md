# آشتی شواهد و نقطه ادامه

Scope: local document/receipt/source review, 2026-09-15. No board SSH or benchmark rerun.

## چه چیزی جلو رفته است؟

- NEXT قبلی با hash `7ab84e03…` هنوز P5→P6 را آینده می‌داند. گزارش جدید EXEC می‌گوید P5 تمام و P6 measured/overall OPEN. P5/P6 receipts و gateها در دیسک موجودند.
- P5 یک echo_capability_probe روی worker 100 را به CLOSED رسانده؛ QA نوع واقعی و caveat را حفظ کرده است. این موفقیت را نگه می‌داریم؛ retrieval یا service دائمی از آن استنتاج نمی‌کنیم.
- مالک GO کامل طرح، GO P5 و GO P6 را قبلاً داده است. P5 seal قدیمی که «P6 مجاز نیست» نوشته، مربوط به زمان قبل از GO/gate P6 است؛ gate جدید P6 و دامنه دقیق آن باید مصرف شود.
- NPU نسبت به بازبینی اولیه پیشرفت کرده: ماتریس ذخیره‌شده اکنون 6/7 PASS با 138 NOT_RUN دارد. عبارت قدیمی «inference هیچ‌جا اندازه‌گیری نشده» برای این snapshot جاری نیست.

## چه چیزی هنوز اثبات نشده؟

| موضوع | دامنهٔ شاهد موجود | شکاف پذیرش |
|---|---|---|
| PB-1 | marker شروع و یک نمونه job | consumer زمان‌بندی‌شده، پیشرفت پیوسته و آزمایش واقعی عدم وابستگی لپ‌تاپ |
| PB-2 | kill یک sleep به‌عنوان stand-in، mark_unknown دستی، lease سال 2099 | fault واقعی consumer، انقضای عملی lease و reconcile خودکار بعد از persist/قبل ACK |
| PB-3 | انتقال/بررسی 9 فایل در 3 ثانیه؛ RPO=0 در لحظه snapshot | readback معنایی، replay کار و RTO تا سرویس قابل‌مصرف؛ RPO پیوسته |
| PB-4 | NOT_RUN، یک fact dry | corpus واقعی، harness، پرسش held-out و پاسخ با/بدون حافظه |
| NPU | rknn_run/outputs_get، checksum و load در نمونه 193 | صحت detection با مرجع و latency سرتاسری محصول |
| T3 | نقش model_infer | مدلِ درحال سرویس، ورودی/خروجی واقعی و مصرف آن توسط اختاپوس |
| P4 | روش mesh SSH و registry | هویت مستقل امضاشده برای هر worker یا HMAC اثبات نشده؛ تغییر scheme تصمیم جدا |
| QA P6 | seal در گزارش/attachment نام برده شده | فایل seal مستقل با hash کامل در درخت lane بررسی‌شده پیدا نشده |

## نقص منبع benchmark

در `sources/hw/T2-PILOT/src/rknn_infer_bench.c` حلقه timing روی خطا break می‌کند اما
summarization همچنان تعداد loops درخواستی را مصرف می‌کند و مسیر نهایی STATUS=PASS است.
این می‌تواند نمونه‌های ثبت‌نشده را در آمار وارد کند یا شکست را PASS نشان دهد. خروجی‌های
تاریخی را بازنویسی نمی‌کنیم و از این نقص نتیجه نمی‌گیریم اجرای ذخیره‌شده شکست خورده است.
آزمون جدید باید شمار موفقیت، خطای مراحل، bounds و exit code درست داشته باشد.

ورودی pseudo-image و checksum، وجود خروجی را می‌سنجند؛ دقت مدل به مرجع مستقل نیاز دارد.
زمان inputs_set+run، زمان صف/انتقال/postprocess/پاسخ نیست. نرخ نمونه را به throughput کل
ناوگان یا 42 TOPS قابل‌استفاده تعمیم نده.

## rollback و idempotency

رسید P5 پیشنهاد حذف کلید از index برای rollback را دارد. برای ادامه آن را کورکورانه اجرا
نکن: حذف dedup entry بدون reconcile می‌تواند کار را دوباره مؤثر کند. دستور ادامه به‌جای آن
حفظ ledger/index معتبر و ثبت cancel/tombstone/reconciliation صریح را می‌خواهد. منبع تاریخی
بدون تغییر نگه داشته شده؛ این یادداشت محدودیت روش را ثبت می‌کند.

## تفاوت «مرتب‌سازی» با مهاجرت

بسته جدید یک entry point و نمای machine-readable دارد. هیچ پوشه قدیمی حذف یا جابه‌جا نشد؛
هیچ registry، gate یا صف زنده تغییر نکرد. منابع به snapshotهای ثابت و hash‌شده متصل‌اند.
مسیرهای P0–P6 قدیمی برای provenance حفظ شده‌اند؛ اجرای بعدی باید تنها بخش باز و ضروری را ادامه دهد.
