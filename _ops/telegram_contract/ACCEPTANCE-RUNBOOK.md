# Runbook پذیرش نهایی دو بات تلگرام

> این سند دستور اجرای آینده است. در این دور هیچ تست شبکه، ارسال، restart یا arm انجام
> نشده است. نتیجه فقط وقتی PASS است که ایجنت ارشد پس از اتمام کارهای موازی این گیت‌ها
> را با fake transport و سپس تپ صریح مالک روی محیط زنده اجرا کند.

## گیت ۰ — مالکیت و ایمنی

- worktree و فایل‌های dirty مشخص باشند.
- تغییرات GLM، Action Bridge و integration کامل/تمیز شده باشند.
- هر توکن فقط در env و هرگز در گزارش نباشد.
- `TG_CENTER_BOT_TOKEN` و `TELEGRAM_BOT_TOKEN` متفاوت باشند.
- هر توکن دقیقاً یک `getUpdates` poller داشته باشد.
- `PATCH_CARD` و code apply تا رأی مستقل خاموش بمانند.

## گیت ۱ — ماتریس مقصد خروجی

با fake clients برای تمام streamها تست شود:

| جریان | بات | سطح | انتظار |
|---|---|---|---|
| chat | outer | DM | PASS |
| doctor-intent/diff | outer | DM | PASS |
| world-discovery | outer | DM | PASS |
| self-goal/action-draft | outer | DM | PASS |
| critical-alerts | inner | DM | PASS |
| doctor-daily/organ-digest | inner | DM | PASS |
| money-pulse/approvals | inner | DM | PASS |
| هر پا | outer | topic خودش در group | PASS |
| stream ناشناخته | هیچ‌جا | HOLD+ALERT | PASS |

هر fallback ناشناخته به گروه = FAIL.
هر core stream در گروه = FAIL.
هر leg stream در DM بدون دلیل = FAIL.

## گیت ۲ — ماتریس ورودی

### Outer DM

- پیام آزاد به chat/answer یا mission proposal برسد.
- read-only مستقیم جواب دهد.
- درخواست action حساس فقط کارت بسازد.
- سؤال مبهم clarify شود.
- capability تازه از manifest دیده شود.

### Inner DM

- `/status`, `/health`, `/queue`, `/wiring` پاسخ دهند.
- approval فقط مالک و با token/hash/expiry معتبر کار کند.
- free chat به Outer DM redirect شود؛ mission دوم ساخته نشود.

### Forum Group

- فقط owner پذیرفته شود، مگر read-only عمومی به‌طور صریح مجاز شده باشد.
- General → deny+redirect.
- topic ناشناخته → deny+redirect.
- topic پا + جمله بی‌نام → همان پا.
- topic پا + نام پای دیگر → clarify/redirect، نه cross-leg execution.
- core command (`/health`, `/flags`, `/doctor`, `/queue`, `/panic`) در گروه به هسته
  dispatch نشود.
- فقط فرمان/مأموریت leg-scoped پذیرفته شود.

## گیت ۳ — callback ownership

برای هر callback_data که هر دو بات تولید می‌کنند:

1. emitter bot مشخص باشد.
2. handler در poller همان bot وجود داشته باشد.
3. callback ≤64 byte باشد.
4. non-owner رد شود.
5. expired/replayed/tampered رد شود.
6. callback در chat/surface اشتباه رد شود.
7. callback معتبر receipt پایدار بسازد.

کارت بدون handler همان بات نباید اصلاً ارسال شود.

## گیت ۴ — دسترسی کامل و آینده‌پذیر

یک capability catalog واحد باید این منابع را پوشش دهد:

- zero-arg cards موجود
- `world_discovery`
- `action_bridge`
- self-goal/SGC
- doctor
- memory/recall
- Telegram diagnostics
- پاها
- قابلیت‌های بعدی با manifest

برای هر قابلیت:

- title
- status واقعی
- read handler
- owner phrases
- action contract
- owner gate
- runtime probe
- source/version

وجود کد بدون manifest یا runtime probe باید `IMPLEMENTED_NOT_WIRED` باشد، نه LIVE.

## گیت ۵ — آزمایش مکالمهٔ واقعی

مالک این ۱۲ پیام را در Outer DM می‌فرستد:

1. «الان چه هدفی داری؟»
2. «شاهد runtime بده.»
3. «چه چیزی مانع تکمیل هدف است؟»
4. «امروز چه کشف تازه‌ای کردی؟»
5. «World Discovery چه وضعی دارد؟»
6. «Action Bridge چه کاری می‌تواند انجام دهد؟»
7. «تمام قابلیت‌های قابل دسترسی را نشان بده.»
8. «این قابلیت کد است یا زنده؟»
9. «یک مأموریت read-only بساز.»
10. «برای ارسال پیام بیرونی کارت بساز.»
11. «بدون اجازه من چیزی نفرست.»
12. «اگر نمی‌دانی، UNKNOWN بگو.»

قبولی:

- پاسخ بی‌ربط یا «متوجه نشدم» کاذب نباشد.
- انجام‌نداده را انجام‌شده نگوید.
- برای action حساس اجرا نکند.
- در پاسخ status، timestamp/generation داشته باشد.
- capabilityها را از catalog بگیرد، نه منوی hardcoded کهنه.

## گیت ۶ — آزمایش واقعی گروه پاها

در هر topic یک پیام «وضعیتش چیه؟» فرستاده شود و فقط همان پا پاسخ دهد. سپس:

- در General بپرس «سلامت اختاپوس چطوره؟» → redirect به DM.
- در Mining بپرس «سلامت کل اختاپوس؟» → redirect به DM.
- در Lead بپرس «ماینینگ را متوقف کن» → cross-leg action رد/clarify.
- در Accounting یک outcome مربوط به همان پا ثبت کن → کارت/receipt صحیح.

صفر core mutation از گروه شرط سخت است.

## گیت ۷ — ضدتداخل و 409

- دو process/poller مستقل با توکن‌های مستقل.
- lock تک‌نمونه هر poller.
- webhook رقیب وجود نداشته باشد یا با رأی مالک مدیریت شود.
- نبض هر poller تازه باشد.
- 409 باعث alert شود، نه سکوت.
- restart یکی، دیگری را بی‌دلیل نکشد.

## گیت ۸ — رسید و مشاهده‌پذیری

برای هر پیام/عمل:

- attempted
- sent/held/blocked
- bot role
- surface
- stream
- topic key
- timestamp
- receipt id/hash

بدون ذخیره متن حساس یا token.

## گیت ۹ — تست زنده محدود

فقط پس از سبزی fake/integration:

1. مالک اجازه یک پیام تست از Outer DM می‌دهد.
2. مالک اجازه یک status از Inner DM می‌دهد.
3. مالک اجازه یک پیام read-only در topic یک پا می‌دهد.
4. هیچ action حساس اجرا نمی‌شود.
5. delivery receipt و ورودی callback مشاهده می‌شود.

## گیت ۱۰ — تعریف Done

فقط اگر همه برقرار است:

- Outer DM = دسترسی مکالمه‌ای کامل به کاتالوگ اختاپوس.
- Inner DM = سلامت/approval/receipt.
- Group = فقط پاها.
- یک poller برای هر token.
- unknown fail-closed.
- قابلیت جدید با manifest خودکار دیده می‌شود.
- action حساس همیشه owner-gated است.
- docs/code/runtime هرکدام جدا گزارش می‌شوند.
- هیچ مسیر مرده، callback یتیم یا fallback به سطح اشتباه وجود ندارد.

وضعیت پیش از تست زنده: `READY_FOR_TELEGRAM_ACCEPTANCE`.
وضعیت بعد از همه گیت‌ها: `TELEGRAM_ACCESS_LIVE`.
