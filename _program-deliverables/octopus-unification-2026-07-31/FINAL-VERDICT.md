# FINAL-VERDICT — مأموریتِ یکپارچه‌سازی · ۲۰۲۶-۰۷-۳۱

**وضعیتِ نهایی: `INTEGRATED_IN_SANDBOX` + `READY_FOR_OWNER_LIVE_GATE`**
(برای دو درزِ نو: فلگ خاموش و منتظرِ رأی؛ برای بقیه: در گیتِ شاخهٔ ایزوله، منتظرِ merge.)

## What changed

۱. شاخه از master ِ ۱۸۳-کامیت-عقب **ff شد به نوکِ tg-p2** (`ce35f61`) — نسخه‌ای
   که ارگانیسم واقعاً اجرا می‌کند. ماندن روی master یعنی duplicate ساختن از
   کارهای انجام‌شدهٔ ۰۷-۳۰ (ممنوعِ §۱۹).
۲. **نجاتِ ۶۳+۱ فایلِ کدِ زندهٔ بی‌گیت** (`2ac7e9b`+`f2fceee`): بستهٔ کاملِ
   owner_console (مسیرِ داغِ `center.py:1384` به فایلِ untracked وابسته بود)،
   `epoch_guard`، ۶ ماژول، و ۴۳ تستی که `run_all.TESTS` ِ tracked نامشان را
   داشت. کپیِ بایت‌به‌بایت؛ secret-scan پاک.
۳. **پذیرشِ کمینهٔ v2** (`a9492c7`): `mission_contract` + `memory/{gate,store}` —
   فقط چون کد/تستِ tracked بدونشان TypeError می‌داد؛ عیناً بایت‌های در حالِ اجرا.
۴. **VQ-STATE-WRITE-001** (`0a303af`): `LockedJson.write` = fsync + retry ِ محدود
   + رسیدِ شکست + blocker ِ snapshot. شکستِ نوشتن دیگر هرگز ساکت نیست.
۵. **دو درزِ نو، هر دو flag-off** (`830e38c`): mission ِ needs_approval → کارتِ
   صفِ ap: ِ موجود (content-free/idempotent) · retrieval ِ ساخت‌یافتهٔ مشورتیِ
   حافظه پیش از planning (بر plan صفر اثر؛ در دفترِ چرخه مشاهده‌پذیر).
۶. **حقیقتِ manifest** (`1247040`): MANIFEST_INVALID دلیل‌دار و قابلِ‌دیدن؛
   manifest ِ world_discovery؛ تصحیحِ probe ِ کهنهٔ unified_control؛ ثبتِ ۲۱
   سوییتِ یتیمِ سبز در run_all (از جمله ۷ سوییت/۸۵ سنجهٔ world_discovery که از
   روزِ تولد هرگز در سوییت ندویده بودند).

## What was tested

- **baseline پیش از هر patch**: run_all ِ کامل، ۳۹۹ سوییت، ایزولهٔ کامل
  (پین‌های env سندشده) → ۳۶ قرمز، همه طبقه‌بندی‌شده: **۲۹ CONFLICTED** (جفتِ
  dirty ِ درختِ زنده) + **۷ HEAD-red ِ pre-existing**. صفر نشت به درختِ زنده
  (فایلِ تازهٔ ledger نویسنده‌اش schedulerِ خودِ ارگانیسم بود — سنجیده شد).
- **بعد از همهٔ تغییرها**: run_all ِ کامل (۴۲۰ سوییت با ثبت‌های نو) →
  **۳۵ قرمز: یکی سبز شد (ccv2)، صفر قرمزِ نو**؛ هر ۵ سوییتِ نو سبز داخلِ ران.
- سوییت‌های هدف: bridge ۱۴/۱۴ · lockedjson ۶/۶ · card ۷/۷ · memory ۵/۵ ·
  manifest ۴/۴ · staleness ۱۰/۱۰ · beat ۱۴/۱۴ · S1-05 ۱۵/۱۵ · outcome ۱۰/۱۰.

## What mutation proved

**۱۹ جهش، همه قرمز، همه restore-سبز** (`05-MUTATION-EVIDENCE.md`):
retry-removed · silent-success · receipt-removed · blocker-removed ·
card-flag · card-dedup · status-broadened · goal-text-leak · beat-seam ·
memory-flag · raw-dump · fail-soft · invalid-listed · report-silenced
(+ نگاشتِ کامل به §۱۷.۲؛ سه موردِ باقی از تست‌های ۰۷-۳۰ ِ خودِ action_bridge پوشش دارند).

## What is integrated / not live

| | |
|---|---|
| **در گیتِ شاخه (merge-pending)** | نجات‌ها · v2 · LockedJson · درزها · manifest/رجیستری |
| **NOT LIVE** | همه‌چیز تا merge؛ دو درزِ نو حتی پس از merge تا arm+restart هیچ‌اند |
| **LIVE و لمس‌نشده** | organism · wiring · center · approval_channel · heart (shadow) · flags.cmd |

## What remains blocked (صادقانه)

۱. **VQ-LIVE-DIRTY-RECONCILE-001** — درختِ زنده ~۱۲۰ فایلِ tracked ِ کامیت‌نشده
   اجرا می‌کند؛ ۲۸ سوییتِ CONFLICTED فقط با آن آشتی سبز می‌شوند. تصمیمِ
   مالک/لِین‌های موازی؛ نقشه: `02-CONFLICT-MAP.md`.
۲. **۷ HEAD-red ِ pre-existing** (فهرست در `01-BASELINE-TESTS.md`) — لِین‌های
   دیگر؛ عمداً لمس نشد.
۳. **مصرفِ تصمیمیِ حافظه** — پشتِ A/B ِ §۱۰.۵ (دادهٔ ورودی‌اش با فلگِ
   memory-read جمع می‌شود).
۴. آشتیِ دو ماشینِ حالتِ mission (VQ-MISSION-RECONCILE-001) — مهاجرتِ واقعی؛
   دست نخورد.
۵. فازهای ۶ (tracer ِ سراسریِ واحد) و ۱۱ (heart) — خارج از ظرفیت؛ heart در
   shadow ماند.
۶. ۸۱ لینکِ شکستهٔ pre-existing در vault (هیچ‌کدام از این جلسه نیست؛ عمدتاً
   اشاره به فایل‌هایی که فقط untracked روی درختِ زنده‌اند — همان ریشهٔ ۱).

## Which owner decisions are required

| کارت | اثر |
|---|---|
| merge شاخه به tg-p2 | یکی‌شدنِ گیت با کارِ این مأموریت (کد=رأیِ مالک) |
| VQ-MISSION-CARD-ARM-001 | فلگ + restart → دو missionِ منتظر کارت می‌شوند |
| VQ-MEMORY-READ-ARM-001 | فلگ + restart → دادهٔ A/B جمع می‌شود |
| VQ-LIVE-DIRTY-RECONCILE-001 | آشتیِ درختِ زنده با گیت |

## Exact rollback

`11-ROLLBACK.md` — خلاصه: همه‌چیز روی شاخهٔ ایزوله؛ `git branch -f … 9f14901`
کلِ مأموریت را برمی‌گرداند؛ رفتارِ زنده از اول هیچ تغییری نکرده.

## ناوردی‌های حفظ‌شده

صفر push/merge/deploy/restart/arm/send/spend · صفر poller/bot/subsystem ِ نو ·
صفر لمسِ فایل‌های dirty ِ درختِ زنده · صفر فلگِ ست‌شده (هر دو فلگِ نو absent=off
و بیرونِ PAPER_FULL_FLAGS) · PRE-0/verifier دست‌نخورده · هیچ metric ای جعل نشد
(دو قرمزِ میانیِ تستِ خودم را با فیکسِ ریشه سبز کردم، نه با شل‌کردنِ سنجه).
