# TERRITORY-REPORT — T5-governance-friction (حاکمیت و اصطکاک)

`checked: 20 hypotheses · sources: 19 file/probe families · refuted: 0 · confirmed: 9 · partial: 3 · unverified: 8 · owner-needed: 4 · verified-this-session: 3`

## چرا این قلمرو مشکوک بود

> هر اثر خارجی رسید می‌خواهد؛ صف رأی/قفل باز

## یافته‌های تأییدشدهٔ برتر

- **W-120** (I3×F3) — کلید B5 (circuit breaker) باز است و مسیر repair مربوطه قطار FAIL تولید می‌کند
  - دلیل: F-011 + R-BREAKER-B5: (False,'CIRCUIT_BREAKER_OPEN')
  - شاهد: 138:ops-receipts, budget_allows('B5') (F-011)
  - مخرج: root-cause-3 (mv از منبع readonly) را رفع و cycle را تأیید کن تا کلید قانونی بسته شود
- **W-121** (I3×F3) — نقص starvation اجراکننده (OW-8): یک درخواست بلاک‌شده کل دستهٔ B8 را می‌خواباند
  - دلیل: F-002: 'return budget-blocked' aborts whole category loop; g22-probe 34+ min بدون رسید
  - شاهد: 09-LANES/OCTOPUS-FORENSIC-REORIENTATION-20260915/OPEN-WORK.json (F-002)
  - مخرج: دسته را به صف مستقل هر request تبدیل کن (کد موجود است، deploy لازم)
- **W-128** (I3×F3) — هیچ SLA/انقضا روی آیتم‌های حاکمیتی باز وجود ندارد (رأی، دروازه، قفل) — صف باز بی‌کران رشد می‌کند
  - دلیل: F-009 (۲۰ رأی) + F-039 (15+ قفل) + F-040 هر سه بدون expires_at
  - شاهد: F-009, F-039, F-040
  - مخرج: قاعدهٔ انقضا: هر آیتم باز باید owner+deadline داشته باشد وگرنه UNVERIFIED_PARKS
- **W-111** (I4×F2) — آزادسازی دومرحله‌ای برای هر دستهٔ ارسال، فرکانس ارسال را به فرکانس رأی مالک گره می‌زند
  - دلیل: PROMPT-REVENUE-R1: sending is two-step release; owner vote per batch
  - شاهد: 09-LANES/OCTOPUS-REVENUE-R1-20260918/PROMPT-REVENUE-R1.md
  - مخرج: مجوز دوره‌ای (W-109) جایگزین رأی هر دسته شود
- **W-113** (I3×F2) — کارهای کلاس B بدون شاهد اجرا نمی‌شوند و شاهد (۱۸۲) یک صف مشترک دارد — همهٔ deployها سریال می‌شوند
  - دلیل: GOV-FREEDOM-V2: شاهد پیش از deploy کلاس B الزامی؛ F-006: restore_drill وابسته به شاهد
  - شاهد: AGENTS.md (GOV-FREEDOM-V2), F-006
  - مخرج: برای تغییرات غیرحساس، کلاس A را پیش‌فرض کن و شاهد را فقط برای اثر عام مصرف کن
- **W-116** (I3×F2) — فاز ۲ آزادی (no-witness recovery، cross-node apply، push autonomy) هنوز باز است — ظرفیت ماشین کامل استفاده نمی‌شود
  - دلیل: F-040: freedom-v2 phase 2 open
  - شاهد: 06-EVIDENCE/OCTOPUS-OWNER-BOARD-2026-08-24/CURRENT-TRUTH.md (F-040)
  - مخرج: یک کارت برای فاز ۲ با ریسک‌های مشخص — هر آیتم جدا

## سایر ورودی‌ها (خلاصه)

- W-112 [PARTIAL] هر اثر خارجی رسید + pre-image می‌خواهد؛ سربار دائم روی هر قدم ارسال
- W-115 [UNVERIFIED] رجیستر UNLOCK با ۱۵+ قفل PROPOSED که هرگز EXECUTED نشده — دروازه‌های بازنشده انبار شده‌اند
- W-122 [UNVERIFIED] TRIO-002 و W3G30 (مصرف‌کنندهٔ تصمیم + precondition freeze + CATSCOPE) دیپلوی‌نشده در صف مانده
- W-118 [UNVERIFIED] پوشهٔ محرمانه‌زدایی نشده: ۷۶ فایل commit‌شده IP/نام‌های داخلی را لو می‌دهد و با status risk_accepted رها شده
- W-119 [UNVERIFIED] گیت G8-021 به‌صورت request کهنه خودزنده می‌ماند و هر tick بودجهٔ کامپوننت می‌سوزاند
- W-123 [UNVERIFIED] ۲۴ verify FAIL از دورهٔ GAP/VBAA باز مانده؛ بدهی کیفیت روی مسیر تصمیم‌گیری سایه انداخته
- W-125 [UNVERIFIED] زنجیرهٔ پذیرش EX1 با NOT_PASSED و سه تناقض ثبت‌نشده رها شده
- W-127 [PARTIAL] کارهای پارک‌شده به دلیل قاعدهٔ «blocked is a decision, not a defect» هیچ مرور دوره‌ای ندارند
- W-S15 [PARTIAL] هزینهٔ اصطکاک رسید/شاهد با کار درآمدی هم‌مقیاس شده؛ حجم رسید بر حجم اثر می‌چربد
- W-124 [UNVERIFIED] سه xfail در ۴ کپی مختلف ماژول VBAA باقی است — تناقض کیفیت در چند نسخه
- W-126 [UNVERIFIED] ستون verified_in_code در دفتر 02-DECISIONS هرگز پر نشده — ردیابی تصمیم→کد قطع است
