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
