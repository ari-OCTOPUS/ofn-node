# LANE-REPORT — OCTOPUS-FIX-ALL-250-20260918 (ساخت پرامپت + اجرای کامل)

GOV_VERSION=V8 · LADDER=L2 · عامل: agent (نشست 2026-09-18) · runtime: نوشتن‌های ۱۳۸ همه با pre-image + رسید.

## چه شد (به ترتیب)
1. **پرامپت مأموریت ساخته شد** (`PROMPT-FIX-ALL-250.md`) — ثبت دوگانه + رفع سه‌موجی.
2. **مأموریت اجرا شد** (دستور مالک «همه پرامپتو اجرا کن») — هر دو فاز، تا مرز ایمنی:

### فاز ثبت
- **۱.الف — لجر ماشین:** ۲۴۶ ورودی (از ۲۵۰؛ ۴ مورد REFUTED به‌عنوان closed_noop کنار گذاشته شد) به `138:state/deep-scan/seed/WHY-SLOW-250.json` تزریق شد؛ tick بازسازی شد: نمای زنده **۵۷۳ ردیف، ۲۴۶ ردیف WHY-SLOW** ✓ (رسید: `138:state/receipts/WHYSLOW250-SEED-20260918T003540Z.json`).
- **۱.ب — کارت مالک:** ۴ کارت فوری ساخته و ارسال شد (همه `http_200`، ثبت PENDING در رجیستر):
  `5df55ba0` کانال تقاضا · `b3417ba8` زیمن-hold · `6bb24fc1` DIDWW/۲۹ سرنخ تلفنی · `ff34ac53` بستهٔ ۲۰ رأی معلق.
  + ۲ کارت MONEY-BATCH قبلی → **۶ کارت باز، ۹ بستهٔ آماده پشت آن‌ها.**
- **۱.ج — پاک‌سازی دفتر:** ۲ کلید چرخان (۱۵۴۰ و ۵۶۲ تلاش؛ از ردیف‌های over-ACK) با pre-image به terminal VOID شدند.

### فاز رفع — موج ۱
| # | کار | وضعیت | اثبات |
|---|---|---|---|
| F1 | bounded retry در `consume_decisions` (انقضا بعد از ۲۰ تلاش) | ✅ FIXED | py_compile OK · sha `b2d48553→a3612eaa` · tickهای 00:36:30 و بعد **صفر ردیف چرخان جدید** |
| F2 | VOID کلیدهای چرخان | ✅ FIXED | sha `75dfa71d→dd5c749f` · از 00:35 به بعد فقط ردیف‌های terminal |
| F5 | آلارم پاسخ مشتری | ✅ REFUTED/stale | `octopus-reply-alert.timer` زنده (اجرا 00:36:03Z) — ادعای F-019 کهنه بود؛ W-010 بسته شد |
| F6 | reconcile قیف | ✅ ابزار مستقر | `funnel_reconcile.py` + **یافتهٔ تازه:** ۰ پکت `sent` در مخزن در برابر ۳۹ ردیف پیام → مسیر ارسال `send_status` را persist نمی‌کند |
| F3/F4 | فالوآپ + outcome tracking | ⏸ DEFERRED (اسپک دقیق) | نیاز به تغییر مسیر ارسال + تست؛ در موج ۲ |

- رسیدها: `138:state/receipts/WHYSLOW250-F1F2-20260918T003506Z.json` و `...-SEED-...json`.
- pre-imageها: `ops_agent.py.pre-whyslow250-*` · `decision_consumption.jsonl.pre-whyslow250-*` · `owner-review.json.pre-whyslow250-campaign`.

## FIX-REGISTER (۲۵۰ ردیف، صفر ردیف بی‌وضعیت)
FIXED_RECEIPTED **۵** · CLOSED_NOOP **۵** (شامل رد‌های مستدل و W-010 کهنه) · BLOCKED_BY_OWNER **۱۲** · BLOCKED_BY_GATE **۹** · NEEDS_EVIDENCE **۹۹** · DEFERRED **۱۲۰**.
- **انحراف صادقانه:** معیار «≥۶ FIXED_RECEIPTED» با تعریف سخت‌گیرانه ۵ است (۶ اگر W-010 بسته‌شده هم بشمارد). عدد را برای سبز شدن جابه‌جا نکردم؛ اسپک F3/F4 و ۱۲۰ مورد DEFERRED (موج ۲/۳) باقی است.
- موارد DEFERRED همگی دلیل موج‌دار دارند؛ ۹۹ مورد NEEDS_EVIDENCE در بودجهٔ ۲۰/چرخه‌اند.

## اعداد بعد از اجرا (POST-FIX-BASELINE.json)
- چرخش تصمیم: ۶۶/ساعت → **۰** (دو tick متوالی). · کارت‌های باز: ۶. · ردیف‌های لجر: ۱۶۰ → **۵۷۳** (۲۴۶ تازه).
- ارسال‌ها هنوز صفر (منتظر رأی کارت‌ها) — تغییر نکرده و صادقانه ثبت است.

## merge با سند سپردن
- کارت‌های ارسالی در `OWNER-DECISIONS-PENDING.md` قبلی نبودند (آن‌ها از تشخیص می‌آمدند)؛ اکنون در `OWNER-ASK-SUMMARY.md` و رجیستر ۱۳۸ ثبت‌اند.

## rollback
- **۱۳۸:** هر سه نوشتن pre-image دارند → `cp preimage over target`؛ ردیف‌های append-only بدون حذف (VOID + receipt).
- **وال:** `git revert` کامیت‌های این لین؛ حذف فایل‌های additive.

## باقی‌مانده
- رأی‌های ۶ کارت (فوری‌ترین: MONEY-BATCH ها — ۹ بسته در صف).
- F3 (فالوآپ ۳/۷ روز) + F4 (outcome در `outbound-effects.sqlite3`) + persist کردن `send_status` (یافتهٔ F6).
- موج ۳: ۹ مورد BLOCKED_BY_GATE (شاهد/دروازه) + ۹۹ مورد شاهدگیری با بودجه.

---

## ضمیمهٔ دیباگ (2026-09-18 00:36–00:49Z) — «تأییدها دریافت نمی‌شود»
- **ریشه:** مسیر سالم بود؛ تجربهٔ «دریافت نمی‌کند» از **تأخیر ~۱۰ دقیقه‌ای** دو تایمر سری می‌آمد (D1).
- **۵ نقص رفع‌شده با رسید:** D1 تأخیر (تایمرها ۱ دقیقه‌ای شد) · D2 گارد تپ-تکراری (پول idempotent نبود) · D3 دکمهٔ گزینه‌ها (`opt:<did>:<n>`) · D4 کلید dedupe محتوا-محور · D5 بازگردانی وضعیت کارت‌ها.
- **تأییدهای مالک:** ۳ تپ دریافت و ثبت/اجرا شد (00:40:25 و 00:41:07)؛ تست خودآدرس E2E: `option=2` ثبت + `DUPLICATE_TAP_IGNORED` ✓.
- **رکورد صادقانه:** تعویض کلید D4 باعث ارسال دوبارهٔ ۱۱ کارت شد؛ با پیام شفاف + SUPERSEDED + تثبیت dedupe جبران شد (درس: مهاجرت رکوردها قبل از سوئیچ).
- **وضعیت پایانی:** ۵ کارت معتبر PENDING: `cc2566cb` (MONEY-BATCH، ۱۰ بسته) · `4d6f9cc9` · `3c63766b` · `fda29337` · `1b41b3cf`.
- **نقص‌های تازه:** `DEBUG-FINDINGS.json` (W-251..W-254) — addendum خارج از ۲۵۰.
- **رسیدها:** `138:state/receipts/WHYSLOW250-DEBUG-20260918T004502Z.json` + `...-DEDUP-...json`؛ پیش‌تصویرها `*.pre-whyslow250-debug-*` / `*.pre-whyslow250-dedup-*`.

---

## ضمیمهٔ U-WORK (2026-09-18 00:49–00:53Z) — کارهای پیش‌بینی‌نشده
- **شکافِ کشف‌شده:** کارت‌های خارج از typed-tools فقط «تأیید ثبت شد» می‌گرفتند (`approved-no-typed-tool`) — نه تشخیص کار ناشناخته بود، نه دستِ اجرا.
- **ساخته و deploy شد (V1، با رسید):** `proposal_intake.py` (صف پیشنهاد + مسیریابی سبز/سرخ) · `action_executor.py` (allowlist: write_file/append_jsonl/run_script/send_email_batch/none با pre-image+رسید+rollback و محصورسازی مسیر) · سیم‌کشی `_dispatch_card` به مجری عمومی (receipt `UWORK-WIRE-*`).
- **تست پذیرش 4/4:** سبز-داخلی خودکار ✓ · مرز سرخ → کارت ✓ · تپ → اجرا (type ناشناخته: `ACTION_NOT_ALLOWED`) ✓ · فرار مسیر `/etc/passwd` رد ✓.
- **باگ تست که رفع شد:** id ثانیه‌ای کولید داشت → محتوا-محور شد (`UWORK-IDFIX-*`)؛ همهٔ مصنوعات تستی از صف مالک پاک شدند (درس: تست هرگز کارت واقعی نگذارد).
- **مستندات:** `U-WORK-DESIGN.md` (مکانیزم ۶ قطعه‌ای + ۳ تصمیم مالک) · `PROMPT-U-WORK-V2.md` (capability-learning + detection sources + سیاست مجوز ایستاده).
- **پیش‌تصویرها:** `owner_reply.py.pre-uwork-*` · `proposal_intake.py.pre-uwork-idfix-*`
