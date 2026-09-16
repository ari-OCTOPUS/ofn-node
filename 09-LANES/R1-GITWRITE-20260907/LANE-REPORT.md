# LANE-REPORT — R1-GITWRITE-20260907

ORDER=v4.1 §۱۸.۵ کارت R1 · GO=مالک 2026-09-07 («gO») · GOV_VERSION=V8 · LADDER=L2
LANE_ID=R1-GITWRITE-20260907 · HEAD_AT_START=c74464d · AUTHORITY=owner chat GO

## تشخیص (اندازه‌گیری‌شده، نه حدس)

علت واقعی حادثهٔ GITWRITE **نه قفل یتیم بود، نه INC-2 (مجوز)**:

1. هر ران ساعتی `push --all` به `E:\germline\vault.git` با **REF_REJECTED** می‌مرد — دو ref غیر-FF: شاخهٔ `w1-money` (دوقلوی amend: offbox `700316f` 01:36 ⟷ local `2256a1e` 01:53، همان parent `2d6f95b`، local با +۱۴ خط EVIDENCE جدیدتر) و تگ `pre-deploy-2026-07-25` («already exists»).
2. هر رانِ شکست‌خورده می‌افتاد روی fallback = **باندل کامل repo ۹.۱GB** روی دیسک IO-پاتولوژیک F: — ران ۱۱:۴۹ روی **۱۹,۴۱۷ بایت تا >۹۰ دقیقه** قفل شد (دو اندازه‌گیری ls با ۱۵ ثانیه فاصله: صفر رشد؛ pack-objects ≈۰.۱۹ CPU-ثانیه بر ۲۰ ثانیه wall).
3. ران ساعتی بعدی ۴۰ بار روی قفل تلاش می‌کرد → فلگ `GITWRITE-FAILED` (۰۳:۵۰:۲۱) + نتیجهٔ تسک 2147946720؛ **daily هم از ۰۱ سپتامبر قرمز** (آخرین مانیفست سبز: 2026-09-01_0330، باندل ۲.۹۶GB، drill PASS).
4. تصمیم ثبت‌شده: فلگ «held-deliberately — تا سبزشدن مسیر AUTO hourly» (emit_cycle.py OWNER_PENDING؛ envelope: may_clear=False).

## اقدامات (همه با رسید در R1-REMEDIATION-RECEIPT.json)

| # | اقدام | کلاس | نتیجه |
|---|---|---|---|
| ۱ | جراحی ref در offbox **با حفظ**: `refs/backup/preserved-20260907-w1-money → 700316f` و `…-tag-pre-deploy → 9c49f1`؛ سپس `w1-money → 2256a1e` و تگ `→ dab81a` | WRITE (فقط E:) | dry-run `--all` = صفر ریجکشن؛ tags = up-to-date؛ صفر از‌دست‌رفتگی (local ابرمجموعهٔ محتوای همان تغییر است) |
| ۲ | کشتن پروسه‌های باندل متوقف (PID 3532/18440/13772 — شاهد: 19KB/90min) | SERVICE-AFFECTING (مستند) | اسکریپتِ والد تمیز unwind کرد (لاگ 13:21:32)؛ **قفل آزاد شد** (فایل حذف) |
| ۳ | پوش اسپاین به `E:/germline/octopus.git` (FF تأییدشده) | WRITE (E:) | `6fd777d..c74464d` — شکاف ۳روزهٔ unpushed-spine بسته شد |
| ۴ | اجرای دستی germline-hourly.ps1 | اجرای pipeline | rc=0 · لاگ **«13:33:23 OK push +state»** · دایرکتوری قفل تمیز |

## وضعیت فلگ — صادقانه

**پاک نشد.** شرط ثبت‌شده «سبزی مسیر AUTO» است؛ ران دستی سبز اثباتِ pipeline است نه AUTO. پایش پس‌زمینه برای ران زمان‌بندی‌شدهٔ **۱۳:۴۹:۰۴** مسلح است؛ با ثبت «OK» همان ران، فلگ با رسید پاک می‌شود (مجوزِ پاک‌سازی از همان تصمیم held-deliberately می‌آید، نه رأی جدید). recovery مسیر daily (۰۳:۳۰ فردا) نیز بعد از رفع برخوردها انتظار می‌رود — قابل‌راستی‌آزمایی با مهر مانیفست فردا.

## فنسینگ و توصیه‌های ساختاری (کارت مالک، اجرا نشد)

`git-serialize.ps1` از قبل: handle انحصاری + retry با backoff + stale-steal ایمن + fail-loud. شکاف باقی‌مانده: fencing token یکنوا در payload نویسنده‌ها (تک‌میزبان/تک‌نویسنده ⇒ ریسک عملی پایین). ریشهٔ ساختاری: **fallback باندل کامل برای کادر ساعتی روی این سخت‌افزار مناسب نیست** — پیشنهاد: باندل افزایشی (`--since=`) یا افزایش FALLBACK_MIN_HOURS؛ و رژیم لاغر کردن repo (R5: ‎۹.۱GB شامل ‎۳۴۵MB مimiasa) که مستقیماً fsck/bundle را کوتاه می‌کند.

MUTATIONS_PERFORMED=۴ ردیف جدول بالا + رسیدها/گزارش + commit این lane · AMBIGUOUS_EFFECTS=none · COUNTERS: EXTERNAL_ACTIONS=0 · MAY_AUTHORIZE=false
ROLLBACK=برگرداندن refهای offbox از `refs/backup/preserved-20260907-*`؛ پوش اسپاین صرفاً FF؛ پروسه‌های کشته‌شده فقط نویسندهٔ temp بودند
NEXT_SINGLE_ACTION=(خودکار با اعلان پایش) پاک‌سازی فلگ پس از ران AUTO سبز ۱۳:۴۹ + رسید؛ بعد: R2 (چرخش secretها) یا U2 — به انتخاب مالک
