# DecisionRecord — باز کردن گیت‌های secret_rotation و partner_precondition

**تاریخ: ۲۰۲۶-۰۸-۱۰ · حکم صریح آری · موقت**

## حکم
آری در جلسه صریح گفت: «همرو روشن کن، ریسک را می‌پذیرم» — یعنی:

- `secret_rotation` باز شد (توکن‌ها برای **یک هفته** بدون چرخش می‌مانند؛
  ریسک پذیرفته‌شده). بعد از یک هفته یا چرخش، دوباره بسته می‌شود.
- `partner_precondition` باز شد — آری گفت «دائم با همه در ارتباطم»؛
  پیش‌شرط انتشار استودیو = تأیید انسانی موجود (approval دو مرحله‌ای)
  که همان ساختار outbox است.
- `miner_isolation` **بسته می‌ماند** (D-8).
- شعاع کاری لید: **۵۰ کیلومتر** (pack به‌روزرسانی شد).

## ساختار امنیتی که حفظ می‌شود (با وجود باز بودن گیت‌ها)
- خروجی فقط از outbox؛ approval هرگز به‌تنهایی ارسال نمی‌کند
  (approved_manual → انسان).
- RED برای هر دو تأیید، confirmation دوم می‌خواهد.
- `require_release_context()` قبل از هر transport.
- یک tenant + یک platform + سقف یک آیتم + dry-run diff.
- WIRE روشن = فقط همان transport با تأیید.

## بازگشت
اگر یک هفته گذشت و رازها نچرخیدند: گیت‌ها را برگردان
(secret_rotation و partner_precondition به default config).
