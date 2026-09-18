# PROMPT-U-WORK-V2 — از «اجرا با تأیید» به «تشخیصِ خودکارِ کارِ ناشناخته»

**GOV_VERSION=V8 · LADDER=L2 · Lane پیشنهادی: OCTOPUS-U-WORK-V2-20260918**
**مأموریت: V1 زنده است (proposal_intake + action_executor + کارت‌دار‌شدن + اجرای تپ). این مأموریت دو قطعهٔ باقی‌مانده را می‌سازد و allowlist را آموزش‌پذیر می‌کند.**

## ۰ — تازه‌خوانی
1. `09-LANES/OCTOPUS-FIX-ALL-250-20260918/U-WORK-DESIGN.md` (مکانیزم ۶ قطعه‌ای)
2. `138:state/revenue-drive/action_executor.py` + `proposal_intake.py` + `proposals.jsonl`
3. `138:state/receipts/UWORK-*.json` (رسیدهای سیم‌کشی و تست)
4. `138:state/revenue-drive/owner_reply.py` — برنچ `it.get("action")` در `_dispatch_card`

## ۱ — قطعهٔ ۵: Capability Learning (allowlist آموزش‌پذیر)
1. روی `ACTION_NOT_ALLOWED` یک **کارت کلاس جدید** بساز (id: `NEW-CLASS-<type>`):
   - متن: نوع کار، دامنهٔ اثر واقعی، چه فایل/هاستی، برگشت‌پذیر یا نه، نمونهٔ dry-run.
   - گزینه‌ها (دکمهٔ هر گزینه): «این کلاس را دائمی مجاز کن» / «فقط همین یک‌بار» / «رد».
2. تأیید → نوع به allowlist اضافه شود، **ولی با guard اختصاصی** (مثل بقیه: مسیر محصور، pre-image، رسید).
   allowlist در `state/revenue-drive/action-allowlist.json` ذخیره شود (append-only + sha در رسید).
3. رد → نوع در `denied-classes.json` ثبت شود تا دوباره پرسیده نشود (نه اسپم).
4. هر افزودن کلاس = رسید + قابلیت rollback (حذف کلاس).

## ۲ — قطعهٔ ۶: Detection Sources (خودش ببیند)
1. **Surprise log:** پایان هر چرخهٔ درآمدی، یک ردیف در `state/revenue-drive/surprises.jsonl`:
   `{at, loop, expected, actually_needed, evidence}` — «چه چیزی پیش‌بینی نشده بود؟»
2. **Deep-scan → proposal:** findings با action مشخص خودکار به `proposal_intake.submit` بروند
   (فقط اگر `action.type` در allowlist است؛ وگرنه کارت کلاس جدید).
3. **Session debrief:** هر ایجنت در `LANE-REPORT` سه «کار ناشناخته‌ای که وسط راه لازم شد» بنویسد و
   اگر action مشخص دارد، submit کند. (این خط در پرامپت‌های بعدی اجباری شود.)
4. **نرخ سنجش:** هفتگی بسنج: چند پیشنهاد ساخته شد، چند خودکار رفت، چند کارت خورد، چند کلاس جدید.
   اگر «پیشنهاد/چرخه» صفر ماند، تشخیص کار نمی‌کند — خودش یک یافته است.

## ۳ — سیاست «مجوز ایستاده» (نیازمند رأی مالک)
- یک کارت با سه گزینه بساز: مجوز ۱۴ روزه برای ارسال ≤۱۰ ایمیل/روز از قالب‌های مصوب / فقط سرنخ‌های موجود /
  رد. با cost-of-delay عددی.
- اگر تأیید شد: در `channel-authorization.json` (یا فایل جدید `standing-authorization.json`) ثبت و
  مسیر گیت آزادسازی به آن وصل شود — **بدون برداشتن هیچ مرز سرخ دیگری**.

## ۴ — سخت‌سازی (نصف روز کار)
- `action_executor`: قید حجم/زمان/تعداد برای هر کلاس جدید + تست منفی برای هر کلاس (path escape، symlink escape،
  خروجی بزرگ، اسکریپت خارج از ریشه).
- تست‌ها را به `tests/` منتقل کن (فعلاً تست‌ها اسکریپت پذیرش‌اند): `tests/test_action_executor.py`.
- لاگ ردها: هر رد با دلیل (`ACTION_NOT_ALLOWED`, `PATH_OUTSIDE_*`, `RED_BOUNDARY_*`) در رسید — برای ممیزی.

## ۵ — گیت پایان
1. یک کلاس جدید end-to-end: type ناشناخته → کارت → تأیید (شبیه‌سازی تپ) → کلاس مجاز → اجرا با رسید.
2. `surprises.jsonl` با ≥۳ ردیف واقعی از چرخه‌های امروز (با شاهد).
3. صفر کارت تستی در صف مالک (تست‌ها همیشه cleanup شوند — درس امشب: `PROP-...-600`).
4. tests/test_action_executor.py سبز + py_compile + rollback مستند.
5. LANE-REPORT با اعداد: n پیشنهاد، n خودکار، n کارت، n کلاس جدید، n رد.

## ۶ — مرزهای سرخ (تکرار: بدون استثنا)
secret چاپ نمی‌شود · هیچ فلگ/دروازه تغییر نمی‌کند · خرید/ارسال/انتشار فقط با تپ مالک ·
مسیر همیشه محصور در `state/**` · pre-image + رسید + rollback برای هر نوشتن · شکست‌ها حفظ می‌شوند.

## ۷ — تله‌ها
- id پیشنهاد باید محتوا-محور باشد (باگ امشب: ثانیه‌ای بود و کولید می‌داد).
- تست‌ها هرگز نباید کارت واقعی برای مالک بگذارند (cleanup اجباری).
- کلید dedupe ارسال محتوا-محور است؛ کارت تغییریافته می‌رود، کارت یکسان نمی‌رود.
- تپ تکراری: وضعیت رجیستر غیر-PENDING → `DUPLICATE_TAP_IGNORED` (پول idempotent نیست).
- ssh+heredoc: فایل را با `cat >` بفرست، کوتیشن تودرتو نگذار.
