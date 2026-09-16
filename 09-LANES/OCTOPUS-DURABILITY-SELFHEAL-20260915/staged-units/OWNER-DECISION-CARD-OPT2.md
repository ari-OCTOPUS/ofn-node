# کارت تصمیم مالک — OPT2 نصب لایهٔ دوام (یک تصمیم، ۳۰ ثانیه)

**چه چیزی آماده است (همه staged، هیچ‌کدام اعمال‌نشده):**

1. **unitهای watchdog برای ۱۱۴/۱۶۰** (`octopus-evaluator-114.service`, `octopus-ingestion-160.service`)
   + shim بدون وابستگی (`octopus_notify_shim.py`): Type=notify، WatchdogSec=30
   (hang ⇒ خودکار restart)، Restart=on-failure با StartLimit ضد-loop، ساندباکس.
   → بعد از نصب، reboot دو سرویس حلقهٔ یادگیری را دیگر نمی‌کشد.
2. **reaper چرخهٔ job** (`durable_jobs.py` روی ۱۳۸، تست ۱۵/۱۵): فقط dry-run اجرا شده؛
   با `--apply` فقط به ledger جدای transitions می‌نویسد (bus دست‌نخورده).
   شمارش واقعی: از ۲۱ job متمایز فقط ۳ مورد اقدام‌خواه (۲ UNKNOWN→FAILED + ۱ lease-expired).
3. **پچ canonical-breaker** برای ops_agent (دستهٔ RY) — عمداً **بعد از TRIO-002** ساخته
   می‌شود تا stale-base نسازیم (درس امروز).

**گزینه‌ها:**

- **الف (پیشنهادی):** نصب unitها روی ۱۱۴/۱۶۰ + فعال‌سازی reaper به‌صورت تایمر
  ۱۵دقیقه‌ای dry-run-report (فقط گزارش، بدون apply) — rollback هر دو = یک disable.
- **ب:** فقط unitها؛ reaper بعداً.
- **ج:** هیچ‌کدام فعلاً؛ همه staged بماند.

**عواقب:** بدون الف، بعد از reboot بعدی همان دست‌راه‌اندازی دستی ۱۱۴/۱۶۰ از نو
تکرار می‌شود و bus همچنان بدون بازبینی خودکار می‌ماند.

rollback در INSTALL-PLAN آمده است. پاسخ: الف / ب / ج
