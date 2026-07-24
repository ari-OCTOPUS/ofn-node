# OWNER-GATE CARD — Stage 3.2: beat parallelism

> شاخه: `claude/octopus-beat-parallel`
> تاریخ: 2026-07-24
> وضعیت: **PROPOSED — منتظرِ رأیِ مالک**
> از `claude/c7-continuity` @ `67f1a71` (clean).

## چه تغییری داده شد
اجرای **موازیِ organs مستقلِ یک فاز** در `beat_scheduler`، پشتِ flag:
- `OCTOPUS_BEAT_PARALLEL` (پیش‌فرض **خاموش** = serial، بایت‌به‌بایتِ امروز).
- وقتی روشن: organs مستقلِ یک فاز (read/write-set ناهمپوشان) با ThreadPoolExecutor
  موازی اجرا می‌شوند. phase ordering، budget_ms، circuit breaker، quarantine،
  halt_behavior همگی حفظ می‌شوند.
- conflict detection: دو organ با write-set مشترک → serial (safe).

## چرا
- این موازی‌کردنِ هدف‌مند است (نه big-bang): فقط organs مستقل سریع‌تر می‌شوند،
  رقابت‌ها امن (serial) می‌مانند.
- باید با داده‌های probe (stage-3.۱) هدف‌مند فعال شود — فعلاً آماده ولی خاموش.

## functional test (سبز)
4 organs × 0.1s: serial=0.40s، parallel=0.13s (~۳× سریع‌تر). `_independent`
read-only=True، write-overlap=False (conflict detection کار می‌کند).

## held-out
- ✅ count: ۲۲۹۶. تمامِ تست‌های beat_scheduler سبز (restart continuity، every_n_beats،
  committed-not-rerun، و غیره).
- تنها ۲ failure: همان **pre-existing** heartstate (اثبات‌شده روی clean parent).
- صفر regression.

## امنیت و برگشت
- flag خاموش = serial (رفتارِ امروز). برگشت: flag=0.
- thread-safety: هر organ به selfِ خودش می‌نویسد؛ ticks خود سریال‌اند (organism loop
  یکی‌یکی tick می‌زند) → هم‌پوشانیِ بین-beat نیست.
- failure isolation حفظ می‌شود (هر organ در futureِ جدا، شکستش بقیه را نمی‌کشد).

## رأیِ لازم
کد بدونِ flag-on هیچ اثری ندارد. فعال‌سازی = `OCTOPUS_BEAT_PARALLEL=1` + restart،
ترجیحاً بعد از جمع‌آوریِ دادهٔ probe برای تأییدِ سود.
