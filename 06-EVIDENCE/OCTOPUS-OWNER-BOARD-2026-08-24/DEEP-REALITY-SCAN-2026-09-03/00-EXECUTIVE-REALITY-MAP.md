---
type: deep-reality-scan
created: 2026-09-03 17:2x-17:5x AEST (07:2x-07:5x UTC)
mode: READ_ONLY_DISCOVERY (صفر تغییر در سیستم‌های تحت‌بررسی؛ فقط این پوشهٔ گزارش ساخته شد)
scanner: ZCode GLM-5.3 — ایجنت لین B/اقتصادی
evidence_window: 2026-09-03 07:22-07:55 UTC (لپ‌تاپ/۱۳۸/گیت‌هاب) + رسیدهای ۲۰۲۶-۰۹-۰۲/۰۳ نشست‌های موازی (برچسب REPORTED_WITH_RECEIPT)
interpretation_note: «هیچ تغییر فایل» روی سیستم‌های تحت‌بررسی اعمال شد؛ خروجی‌ها آرتیفکتِ جدیدِ گزارش‌اند در محل append-only جاافتادهٔ خانه.
---

# ۰۰ — نقشهٔ واقعیت (Executive)

## پنج حلقهٔ واقعاً بسته (VERIFIED)
1. **تایمرهای خودمختاری برد138** — ۱۰ تایمر octopus-* فعال؛ آخرین trigger سه تا ۲۳ دقیقه پیش (list-timers 07:25Z).
2. **mesh-drain روی 138** — outbox=0/inbox=0 (دیروز 17/3 بود)؛ ۱۵ آیتم در state=retry. producer→transport→consumer بسته.
3. **timesync 138** — NTPSynchronized=yes (دیروز census گفته بود خاموش؛ ترمیم شده).
4. **orphan-watchdog لپ‌تاپ** — receipts.jsonl با ts امروز؛ pid 19176 را ORPHAN ثبت کرده و همان pid هنوز روی 8774 زنده است (تشخیص درست، نگه‌داری ناتمام).
5. **backup روزانهٔ 138** — ofn-backup موفق (رسید‌های پوشهٔ backups)؛ لهجهٔ ISO: «backup exists ≠ restore proven».

## پنج حلقهٔ بحرانیِ باز
1. **138→182 mesh sender** — هنوز مرده (رسید دیروز)؛ وابستهٔ اصلی همگام‌سازی شاهد.
2. **inbox-consumer نداریم روی 138** — پیام‌های دریافتی هضم نمی‌شوند (census #40؛ outbox خالی شده ولی مصرف‌کنندهٔ ورودی سیم نشده).
3. **OWNER-QUEUE.md هیچ‌جا رندر نمی‌شود** (census #16) — صف تصمیم مالک بی‌نمایش.
4. **telegram_glass پوسته بدون runner** (census #26) — گلاس مالک در عمل کور.
5. **NATS روی 182: یک کلاینت، صفر ترافیک بین‌بردی** (census #42) — transport خریده شده و بلااستفاده.

## پنج تناقض مهم
1. «اولین ارسال Sep 1 تأیید شد» (رأی Q-05) در برابر «first send PENDING» در دو سند قدیمی — روایت کهنه هنوز زنده.
2. journal 138 صفر firing نشان می‌دهد در برابر list-timers که ۱۰ اجرای تازه نشان می‌دهد — علت: ari خارج از گروه systemd-journal (دید، نه واقعیت).
3. دیروزی: «NTP خاموش» در برابر امروز: «NTPSynchronized=yes» — ترمیم بین دو اسکن رخ داده؛ سند census هنوز کهنه را می‌گوید.
4. «fullest tree = fix/demand-harvest لپ‌تاپ» در برابر «deployed main = 60dce961» — کدام منبع حقیقت deploy؟
5. README دکتر: «157/157» در برابر اندازه‌گیری مستقیم: 168/168 — عدد کهنه در سند کانونی.

## سه خطر P0
1. **دو دکتر، دو رانتایم**: دکتر میراثی ۱۵۰۰خطی در _ops لپ‌تاپ + پکیج ofn/doctor تازه‌مرج‌شده — بدون interlock؛ خطر دوباره‌کاری/تناقض verdict.
2. **deploy lag امنیتی**: main=6e2bfd50 (repair_api داروخانهٔ خودترمیم) ولی 138 روی 60dce961 — ترمیم‌ها به برد نمی‌رسند.
3. **والت ریپو با ۴۰۰ فایل dirty روی برنچ rescue** — لغزندگی نسبت به سیاست append-only؛ یک نشست اشتباه = دست دادن رسیدها.

## سه اقدام فقط‌خواندنی بعدی
1. اجرای `verify_live_store.py`/معادل روی دیتابیس زندهٔ 138 (رسید سطح-C برای زنجیرهٔ شاهد).
2. hash-diff دوقلوهای phase0 (A-halt vs isolated) برای تعیین дلتای دو اسنپ‌شات.
3. snapshot مالکیت پر机场ها روی 138: `ss -tlnp` + `systemctl cat` هر یونیت → جدول کد-به-سرویس.
