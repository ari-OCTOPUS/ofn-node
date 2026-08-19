# R01-OWNER-DECISION — کارت‌های بعدی، رتبه‌بندی‌شده (بدون کد)

run: R01-191-20260818-2217 · وضعیت: R01 کامل شد؛ هیچ کدی تغییر نکرد؛ صفر شبکه/راز/scheduler.

## نتیجهٔ یک‌خطی

زیرساخت واقعی و زنده است و گیت‌ها در کد اغلب fail-closed — ولی سه چیز مسلح/باز مانده (پرچم /sh، FREEZE بی‌اثر، tunnel بی‌identity)، لایهٔ ingest حافظه گیت ندارد، و «یادگیری» فعلاً انباشت است نه تغییر رفتار. دادهٔ هر تصمیم زیر، شاهد دارد.

## کارت‌های پیشنهادی (رتبه از بالا به پایین)

### CARD-A (اقدام مالک، امروز، بدون کد) — DISARM-/sh ceremony
حذف `_ops/ACTIVATION-RAW-SHELL.flag` با دست مالک (یا یک خط مجوز صریح تا ایجنت انجام دهد + ثبت در 02-DECISIONS). Rollback: بازساخت پرچم.
*چرا اول:* تنها مورد ناسازگارِ فعال با verdict امروزت (D2). شاهد: R01-GOVERNANCE-GAPS §1.

### CARD-B (اقدام مالک + انسانی) — mail_credentials: untrack + rotate
`git rm --cached _ops/legs/mail_credentials.py` + `.gitignore` + چرخش اعتبارنامه با دست انسان (طبق D3). شاهد: B1.

### CARD-C (نشست بعدی ایجنت، فقط-سند) — F2 CANONICAL_REGISTRY
دادهٔ خام آماده است (REALITY-MANIFEST + 01-d7-classification): ۵ worktree ثبت‌شده + ۱ یتیم + ۲ stub + ۷ باندل یکسان + آینهٔ germline + دو store حافظه. خروجی: یک CANONICAL_REGISTRY امضایی + قاعدهٔ placement.

### CARD-D (کارت کد اول — جانشین CARD-001 طبق D4) — B3: شکاف کشف تست
conftest.py قرنطینه‌ای برای collect توابع `t_*` در worktree ایزوله، با حلقهٔ کامل F5 (فرضیه → baseline → پچ → تست → امتیازدهی صادقانه). کاملاً قابل بازتولید (pytest exit=5 → 0)، کوچک، برگشت‌پذیر. شاهد: B3 + TEST-MATRIX.

### CARD-E (پس از F2) — F3 قراردادها
EVIDENCE_CONTRACT با provenance/timestamp/confidence/expiry اجباری + MEMORY_ADMISSION_RULE (بستن/گیت‌کردن self-loop-ingest) + wire کردن claim_hypothesis (پروپوزال موجود) + لایهٔ حافظهٔ منفی. شاهد: MEMORY-LEARNING-AUDIT §4.

### CARD-F (پس از F3) — F4 سطح ایمنی
ENFORCED/DECORATORY نهایی برای: FREEZE/ARCHITECT_SYS · تقدم HALT-ALL در runtime · auth و bind برای board_cp · policy دو tunnel عمومی · وضعیت ignore پنج .env دیگر. شاهد: GOVERNANCE-GAPS.

## تصمیم‌های باز از F1 که این run جدیدی به آنها اضافه نکرد (بدون تغییر)

D5 اجرا شد (sprint فقط inventory — رعایت، اجرا نشد) · D6 رعایت شد (صفر تماس برد) · D7 کامل شد (طبقه‌بندی + hash، بدون هیچ move/rename/delete).

## شرط توقف فعال بعدی

اگر مالک CARD-A را نپذیرد، هیچ کارت کدی نباید باز شود (D2 نقض باقی می‌ماند و F4 با یک مسیر مسلحِ مصوب‌نشده شروع می‌شود).
