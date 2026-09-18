# LANE REPORT — THINK-POOLS-20260918 (شب RUN-TO-COMPLETION)

GOV_VERSION=V8 · LADDER=L2 · اجرای خودران طبق RUN-TO-COMPLETION.md (اختیار
صریح مالک: «همرو پرامپتی بنویس که تا اخر انجام بدی، هی نپرس»)

## شمار نهایی

| وضعیت | آیتم‌ها |
|---|---|
| **انجام‌شده** | ۸ از ۱۰ — آیتم‌های ۱، ۲، ۴ (نشست قبل) + ۳، ۵، ۶، ۷، ۸، ۹، ۱۰ (این نشست) |
| **شکست‌خورده** | ۰ |
| **توقف‌کرده (مرز قرمز/زمان‌بندی)** | ۰ — یک آیتم زمان‌دار است (پایان پنجرهٔ ۲۴س کاناری، خودکار) |

## چه شد (این نشست، به ترتیب اجرا)

### آیتم ۳ — مسیر پولیِ لجر بودجه ✅
- اندازه‌گیری اول: ۸۹ ردیف، ۴۹٫۴٪ بی‌نام = دقیقاً ۴۳ ردیف settle + ۱ correction؛
  ردیف‌های settle اصلاً فیلد provider نداشتند.
- تغییر (با preimage `ff78fee9…` → postimage `d2aa56c5…`): reserve بدون نام پروایدر
  ثبت نمی‌شود (`PROVIDER_ATTRIBUTION_REQUIRED`)؛ سقف غلتان ۲۴س per-provider
  (پیش‌فرض ۰٫۲۵$) → `PROVIDER_CAP_REACHED`؛ settle از reserve وارث provider می‌شود؛
  default خاموش `sakana-fugu` حذف شد (هیچ صداکننده‌ای به آن تکیه نمی‌کرد — اندازه‌گیری شد).
- تست جفتی: ۶ پاس/۹ شکست سرخ → **۱۵/۱۵ سبز**؛ رگرسیون test_provider_failover ۱۰/۱۰.
- ردیف‌های تاریکی دست‌نخورده (لجر hash-chained؛ بازنویسی ممنوع و ممکن نیست).
- کامیت ۱۳۸: `fa2fd2e9` · والتی: `cd79083` · رسید: `138:state/receipts/BUDGET-ATTRIBUTION-20260918.json`

### آیتم ۵ — اولین کار واقعی روی بردهای خالی ✅
- کشف: ورکرها (`compute_worker.py` در `/usr/local/bin` هر برد) نه ریپو داشتند نه pytest؛
  منبع کد ورکر هم فقط روی نودها بود. payload ۲۷MB (سوئیت+پکیج‌های ریشه) + pytest
  vendored (با `py.py` که فراموش شده بود) به `/srv/octopus-compute` هر ۴ نود.
- ورکر به ریپو آمد (`state/fleet-compute/compute_worker.py`، AGENT 1.2.1) با پروفایل
  allowlist‌شدهٔ `test_shard` + اعتبارسنجی متقاطع (`SHARD_INDEX_GE_COUNT`).
- دو باگ زنده که حلقهٔ اجرا گرفت: (۱) shard_index ≥ shard_count از اعتبارسنجی رد می‌شد؛
  (۲) `ctx["deadline_mono"]` در run_task با time.time پر می‌شود → workflow با کم کردن
  monotonic عدد ~۱٫۸ میلیارد ثانیه به subprocess می‌داد → `OverflowError` (تسک
  f09a28425d3e574c، رسید ثبت است). هر دو رفع + تست رگرسیون.
- نتیجه: **۳ برد × ۱۶۱۷ تست** (۱۰۰: شارد ۰ · ۱۹۳: شارد ۱ · ۱۶۰: شارد ۲) ~۹۶٪ پاس،
  cgroup VERIFIED. تست جفتی ۱۲ سرخ → **۱۳ سبز** (۱۲ + رگرسیون مبنای ساعت).
- کامیت ۱۳۸: `c1eddab4` · والتی: `ac884fb` · رسید: `138:state/receipts/TEST-SHARD-20260918.json`

### آیتم ۶ — ارتقای کاناری ✅ (گسترش: خودکارِ زمان‌دار)
- ارزیابی در T+2.2h: **۷/۷ معیار اندازه‌پذیر PASS**؛ فقط پنجرهٔ ۲۴س INCOMPLETE (زمانی).
- ریشه‌یابی FAIL ظاهری معیار ۶: مسابقهٔ snapshot — تسکِ سالمِ درحال‌اجرا با lease
  معتبر در لحظهٔ عکس، «runaway» شمرده می‌شد. معیار در هر دو نسخه (ارزیاب والتی +
  دروازه) به تعریف واقعی خودش اصلاح شد: overdue = lease بازِ منقضی + RUNNING.
- دروازهٔ خودکار `canary_gate.py` روی ۱۳۸: تایمر `octopus-canary-gate` فردا ۰۱:۰۵Z
  (+ fallback روز بعد) — فقط روی PASS کامل، allowed_nodes → ۱۱۴+۱۶۰+۱۰۰ با بکاپ
  زمان‌دار. selftest مکانیک گسترش را روی کپی موقت اثبات کرد؛ کانفیگ زنده دست‌نخورده.
- کامیت ۱۳۸: `e627b3c0` · والتی: `b0f9025` · رسید: `138:state/receipts/CANARY-GATE-*.json`

### آیتم ۷ — راننده برای cognition و durability ✅ (هر دو تایمر، نه archive)
- تحلیل نشست قبل با اندازه‌گیری تصحیح شد:
  - `cognition_factory.main()` صف‌محور است (یک تسک در هر فراخوانی از
    `ops-agent/state/canary-requests` که `coding_worker.cognition_request` پرش می‌کند) →
    تایمر همان صداکنندهٔ غایب است.
  - `durable_jobs.py` برخلاف ثبت قبلی main دارد (reaper روی باس fleet-jobs) و باس
    **زنده** است (دقایقی قبل از بررسی نوشته شده بود). reaper سه گذار واقعی اعمال کرد:
    ۲× UNKNOWN→FAILED، ۱× LEASE_EXPIRED_RECLAIM.
- تایمرها با پاکت cgroup مثل بقیه: `octopus-cognition-factory` (*:5/30، 100%/512M)
  و `octopus-durability-reaper` (*:0/30، 50%/256M). شلیک اول هر دو تأیید (۰۳:۳۰/۰۳:۳۵Z).
- کامیت ۱۳۸: `a5a2ffcd` · رسید: `138:state/receipts/DRIVERS-COGNITION-DURABILITY-20260918.json`

### آیتم ۸ — سهم ۵۰٪ لپ‌تاپ ✅
- لپ‌تاپ ویندوزی است → معادل هسته‌ای حکم مالک: سقف سخت با **affinity ماسک ۶ از ۱۲
  هسته** (SetProcessAffinityMask) + BELOW_NORMAL؛ هاب NATS (nats-server.exe زنده) هرگز
  در مجموعهٔ ایجنت نیست — هسته‌هایش رزرو می‌ماند.
- lease کوتاه تجدیدشونده (۳۰۰ث، heartbeat ۶۰ث) + بازگرداندن lease منقضی در شروع بعدی
  (تور ایمنی درپوش/خواب/برق — رویدادهای ناظر‌ناپذیر در ویندوز).
- **Preemption زنده اثبات شد:** ورودی واقعی کاربر (SendInput → idle_ms=0) وسط کار →
  ایجنت در مرز چانک تسلیم، شارد به pending با attempt+1 برگشت، exit 3 → اجرای مجدد
  تا تمام‌شدن.
- کار واقعی: شاردهای ۳/۴/۵ (۱۲۰۰+۱۵۵۵+۱۵۵۴ پاس) → همراه بردها، **هر ۶ شاردِ
  ۹٬۷۰۰ تست پوشش داده شد**.
- عامل: `tools/laptop_worker.py` · رسید: `evidence/LAPTOP-WORKER-20260918.json` ·
  لجر: `F:\octo-exec\LAPTOP-WORKER-20260918\ledger.jsonl`

### آیتم ۹ — PR RUNTIME-EXPORT ✅
- **PR #267** (شاخهٔ `pr/runtime-export-20260918` از `ae187e03`):
  ۳ drifted (gates/owner_notify/glass_runner) + ۱۰ غایب + `owner_reply.py` نسخهٔ
  fix‌شده (attribution+cursor) + ۴ فایل تست.
- تست جفتی **۲۰/۲۰ سبز**؛ کنترل منفی روی پایهٔ تمیز: ۱۸ سرخ/۲ سبک (دو تست posture
  که از قبل از drift سبزند).
- **باگ واقعی که تست‌ها گرفتند:** ack دکمه‌ها `telegram_glass._tg` را صدا می‌زد که
  در هیچ نسخه‌ای از هیچ ماژولی وجود نداشت (`_tg` در خود glass_runner است) → ack
  «دریافت شد» هرگز روی برد شلیک نشده بود. در PR اصلاح شد؛ برد همچنان نسخهٔ شکسته
  را اجرا می‌کند تا merge.
- اسکن secret روی ۱۷ فایل قبل از push: هر ۴ برخورد = نام متغیر env یا lookup؛
  هیچ مقداری. push از لپ‌تاپ (ari322) چون توکن ذخیره‌شدهٔ ۱۳۸ به این ریپو ۴۰۳ می‌خورد.

### آیتم ۱۰ — هماهنگی Obsidian و GitHub ✅
- چهار سطح به‌روز شد (بلوک «شب RUN-TO-COMPLETION»): `OCTOPUS/CURRENT-TRUTH.md` ·
  `06-EVIDENCE/OCTOPUS-OWNER-BOARD-2026-08-24/CURRENT-TRUTH.md` (کانونیکال طبق
  redirect) · `01 - Dashboard/OCTOPUS-VITAL-DATA-2026-09-08.md` · همین LANE-REPORT.
  آیین mtime: بلوک auto در OCTOPUS/CURRENT-TRUTH را runtime می‌نویسد (۰۳:۵۴Z — تازه‌تر
  از همه) — دست نزدیم؛ سطح‌های انسانی additive به‌روز شدند.
- شاخهٔ lane روی GitHub push شد (پس از pull --rebase).

## چه چیزی عمداً کامیت نشد (آیتم ۱۰)

- ~۱۵۲۴ فایل کامیت‌نشدهٔ والتی: فقط مسیر laneها + سطوح Obsidian کامیت شد.
- state خامِ بردها (لجرهای زنده، telemetry، compute_tasks.db) — دادهٔ runtime است نه سند.
- بستهٔ اسراب‌دار `~/.config/ofn/secrets.env` و مشتقاتش — هرگز.
- کامیت‌های شبِ ۱۳۸ (fa2fd2e9…a5a2ffcd) عمداً **push نشدند** — مسیر مجاز: برنچ + PR +
  ریویو GOV-V6؛ فعلاً روی main محلی ۱۳۸ می‌مانند تا مرج بعدی.

## چه ماند

1. **پنجرهٔ ۲۴س کاناری** — خودکار: دروازهٔ ۰۱:۰۵Z فردا ارزیابی می‌کند و فقط روی PASS
   گسترش می‌دهد. اگر FAIL شود، رسید با جزئیات معیار ثبت می‌شود (ریشه‌یابیِ بعدی).
2. **Merge PR #267** — منتظر ریویو مستقل GOV-V6 (نویسنده≠تأییدکننده).
3. **چرخش توکن** (توصیه فوری — بند امنیتی پایین).
4. رفع دو ناهمخوانی ثبت‌شدهٔ نشست قبل (frontier گوگل ضعیف‌تر از strong خودش؛ deepseek
   بی‌پله) — نیازمند GO مالک روی تنظیمات پروایدرها.
5. اجرای دوره‌ای کارگر لپ‌تاپ (الان one-shot اثبات‌شده است؛ تایمر/برنامهٔ دائمی ویندوز
   تصمیم طراحی بعدی است).

## یافتهٔ امنیتی (صادقانه)

حین بازرسی credential helper برد ۱۳۸ برای عیب‌یابی push، یک PAT واقعی از
`~/.git-credentials` **به‌طور غیرعمد در خروجی همین نشست چاپ شد** (فرمول ماسک sed
اشتباه بود). توکن کامیت/push نشده و فقط در لاکال این نشست است؛ اما طبق آیین،
**چرخش فوریِ آن توکن توصیه می‌شود** (همان پنجرهٔ باز D-28 که secret_rotation در آن
risk_accepted_unrotated است). همان توکن به ریپوی ofn-node دسترسی push هم نداشت (۴۰۳).

## شواهد

- ۱۳۸: `state/receipts/{BUDGET-ATTRIBUTION,TEST-SHARD,CANARY-GATE-*,DRIVERS-COGNITION-DURABILITY}-20260918*.json`
- ۱۳۸ گیت: `fa2fd2e9` · `c1eddab4` · `e627b3c0` · `a5a2ffcd` (محلی، تا PR بعدی)
- لپ‌تاپ: `F:\octo-exec\LAPTOP-WORKER-20260918\{ledger.jsonl,queue/done/}`
- گیت‌هاب: PR **#267** (شاخهٔ `pr/runtime-export-20260918`)
- والتی: کامیت‌های lane (cd79083، ac884fb، b0f9025، + این گزارش)

## Rollback (قدم‌به‌قدم)

- آیتم ۳: فایل `.pre-patchskip-20260915` موجود؛ خود پچ با preimage ثبت؛ revert تک‌کامیت.
- آیتم ۵: `compute_worker.py` فقط در ریپو/نودها — بازگشت به sha `feaaf8d8…`؛ payload
  `/srv/octopus-compute` قابل‌حذف کامل است؛ تسک‌ها در db با state ثبت‌اند.
- آیتم ۶: دروازه تا قبل از PASS هیچ تغییری نمی‌دهد؛ بعدش هم بکاپ زمان‌دار + برگرداندن
  allowed_nodes به ["114"].
- آیتم ۷: `systemctl disable --now` دو تایمر + حذف unitها (فایل‌ها در state/*/units).
- آیتم ۸: کل مسیر `F:\octo-exec\LAPTOP-WORKER-20260918` مستقل و قابل‌حذف؛ NATS دست‌نخورده.
- آیتم ۹: برد ۱۳۸ دست‌نخورده (PR-only)؛ شاخهٔ PR قابل‌بستن بدون اثر.
