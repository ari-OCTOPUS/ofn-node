# RCA-1 — restore_drill: NOT_RUN

- **id:** RCA-1
- **علامت مشاهده‌شده (با رسید):** GOV-V8 §6.6 درخواست بازسازی-از-رسید به‌عنوان شرط L2؛ در تمام ledgers روی 138 (`/home/ari/ofn/state/receipts/`, ops-receipts 3954+ ردیف) هیچ رویداد `RESTORE_DRILL` یا خروجی `RESTORE-DRILL-*.json` وجود ندارد؛ `systemctl list-timers` روی 138 هیچ تایمر restore-drill ندارد (بررسی 2026-09-16T09:5xZ).
- **ریشهٔ واقعی (file:line):** مکانیزمِ ابزار وجود دارد — `octopus_recovery/restore_drill.py` + `tests/test_restore_drill_disposable.py` + `tools/restore_drill.sh` — اما هیچ consumere آن را اجباری نمی‌کند: نه CI gate، نه تایمر، نه شرط ladder. غیبتِ مکانیزمِ «اجبار»، نه غیبتِ ابزار. نقطهٔ گلوگاه: GOV-V8 درخواست کرده ولی مسیر L2-check هیچ تابعی را صدا نمی‌زند (جست‌وجوی `restore_drill` در کد لدر/گیت: صفر فراخوانی).
- **چرا تشخیص داده نشد:** گزارش سلامت سیستم به «وجود ابزار» بسنده کرد (E1)، نه «اجرای دوره‌ای» (E4). هیچ متریکِ «سن آخرین دریل» وجود ندارد که صفر بودنش دیده شود.
- **حداقل اصلاح:** R-1 در فاز REPAIR: اجرای واقعی دریل در فضای disposable (fixture)، خروجی `RESTORE-DRILL-1.json` با snapshot/diff/verdict؛ سپس یک تایمر ماهانه + یک invariant در CI (`assert days_since(last_restore_drill_receipt) <= 31`).
- **رسید اثبات اصلاح:** `RESTORE-DRILL-1.json` (diff باینری صفر یا گزارش صریح FAIL) + ردیف رسید ماشین‌خوان با timestamp.
- **دریل بازگشت‌ناپذیری:** هر ماه دریل با «تخریب کنترل‌شدهٔ فیکسچر + بازسازی + diff» اجرا می‌شود؛ اگر diff ناصفر بود، فاز جاری FAIL می‌شود و ladder قفل می‌ماند — یعنی رخداد مجددِ «ماه‌ها NOT_RUN» دیگر قابل‌پنهان‌شدن نیست چون CI/تایمر رسید تازه می‌خواهد.
