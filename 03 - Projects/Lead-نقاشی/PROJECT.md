---
type: project
kind: area
project: "[[03 - Projects/Lead-نقاشی/PROJECT]]"
status: active
owner: آری
risk_level: medium
autonomy_level: read-only
tags: [lead-gen, painting, sydney, business]
created: 2026-07-03
updated: 2026-07-06
---

# پروژه: Lead-نقاشی

> 🏗️ **رکنِ ساخت:** [[04 - Architect System/MYCELIAL-MASTER-SPEC|MYCELIAL-MASTER-SPEC]] — این پروژه یک node در §۳ رجیستریِ اتصال است (build/test/delete پشتِ verdict).

## Mission

درآمد اصلی — لیدگیری برای بیزنس نقاشی ساختمان در سیدنی با آزمایش‌های کنترل‌شده (یکی در هر زمان). معیار موفقیت: **لید واقعی، نه کلیک.** tenant #2 سیستم architect (D-26).

## Current state (شواهد)

- زیرساخت AiFarm: `AiFarm-Lead/` (نسخه canonical) شامل brushline (60_code) و `SERVER_ARCHITECTURE.md` `[Verified: وجود فایل‌ها]`
- ربات کاریابی: `کاریابی/bot/` — بازسازی کامل فازهای ۰-۴ (2026-07-03): امنیت (کلیدها فقط در .env + fail-fast)، حلقه تایید تلگرام (approve/reject/save/skip)، ۳ منبع فعال (PlanningAlerts + AusTender OCDS + NSW eTendering RSS) با زمان‌بندی per-source، `/draft` (فقط پیش‌نویس، ارسال دستی)، `/report` هفتگی، لاگ توکن، ۳۳ تست pytest → تا rotation خاموش `[Verified: tests green]`
- باگ‌های حیاتی رفع‌شده: job هارvest که با next_run_time=None برای همیشه pause بود؛ فریز event loop توسط Hunter؛ crash پیام‌های Markdown؛ حافظه Hunter که قدیمی‌ترین (نه جدیدترین) را می‌خواند؛ تجاوز از سقف ۱۰۰۰ درخواست/روز PlanningAlerts `[Fixed: 2026-07-03]`
- symlink خراب `کاریابی/bot/data/paint-data` → حذف شد `[Fixed: 2026-07-03]`
- pipeline ساختاریافته لید: تا امروز وجود نداشت → [[03 - Projects/Lead-نقاشی/Lead Pipeline & Experiments|Lead Pipeline & Experiments]] (امروز ساخته شد، خالی)
- آزمایش فعال: هیچ — آزمایش #۱ (SEGMENT-DISCOVERY طبق D5) پیش‌ثبت شد و منتظر شروع است

## Assets & resources

مهارت اجرا (نقاشی/renovation خود آری) · brushline (ایجنت لیدگیری، خاموش تا rotation) · بودجه از سقف کلی architect (D-25)

## Active workstreams

1. آزمایش #۱: کشف segment — کدام بخش (residential/strata/builder) بیشترین ارزش per lead می‌دهد. 2. احیای brushline بعد از rotation. 3. تعمیر symlink دیتا.

## KPIs

لید واقعی/هفته `[To measure]` · هزینه per lead per کانال `[To measure]` · نرخ تبدیل لید→quote→کار `[To measure]`

## Agent interface

- **می‌خواند:** این manifest، pipeline، لاگ آزمایش‌ها، `SERVER_ARCHITECTURE`.
- **می‌نویسد:** draft پیام/کمپین، به‌روزرسانی pipeline (پیشنهادی)، گزارش هفتگی آزمایش.
- **verdict انسانی:** ارسال هر پیام outreach به مشتری واقعی، هر خرج تبلیغ، تماس تلفنی.
- **قید قانونی:** هر outreach طبق [[03 - Projects/Lead-نقاشی/Outreach Compliance|Outreach Compliance]] (Spam Act 2003 + DNCR Act 2006).
- **Security Gate:** read-only تا بسته شدن CRITICALها.

## Open blockers

کلیدهای Anthropic/Telegram در چرخش · segment هدف = `[To measure]` تا پایان آزمایش #۱

## Active Context

- **2026-07-06 (جلسه ۱۷):** کد پروژه به `_code/` منتقل شد (B1 پلن NONMD-TRIAGE؛ propose→executed با verdict آری). لاگ کامل: `00 - Inbox/nonmd-move-log-2026-07-06.csv`.

- تمرکز فعلی: rotation کلیدها → روشن کردن ربات → آزمایش #۱ (SEGMENT-DISCOVERY)
- تغییرات اخیر: 2026-07-03 — بازسازی کامل ربات (فازهای ۰-۴، ۳۳ تست سبز) + ۱۰ پرامپت تحقیقاتی در `کاریابی/06_پرامپت‌های_تحقیقاتی_گسترش_لیدگیری.md` · 2026-07-04 — [[03 - Projects/Lead-نقاشی/Report - Lead-نقاشی - Sydney Lead Channels 2026|Report - Sydney Lead Channels 2026]] از Inbox منتقل شد (Google LSA هنوز در AU نیست) · 2026-07-04 — کیت مغز پروژه (INDEX·DecisionLog·OpenQuestions طبق LIVING-BRAIN-BLUEPRINT) ساخته شد
- ۳ قدم بعدی: (۱) rotation ۵ کلید + `pytest tests/ -q` + `python test_run.py` (۲) اجرای main.py و بررسی push های تلگرام (۳) شروع آزمایش #۱ با دیتای واقعی ربات
- تصمیم‌های باز: کانال آزمایش #۱ (letterbox/آنلاین/ارجاع؟)

## Progress

- چه کار می‌کند: زیرساخت brushline موجود؛ چارچوب آزمایش تعریف شد
- چه مانده: rotation، آزمایش #۱، pipeline با دیتای واقعی
- مشکلات شناخته: symlink خراب paint-data؛ هیچ لید ساختاریافته ثبت نشده

## Next actions

- [ ] rotation کلیدها (مالک): Anthropic + Telegram (revoke در BotFather) + Tavily + PlanningAlerts + Serper → مقادیر جدید در `کاریابی/bot/.env`
- [ ] شروع آزمایش #۱
- [x] تعمیر symlink (2026-07-03)

## نوت‌های مرتبط

- [[03 - Projects/Lead-نقاشی/Lead Pipeline & Experiments|Lead Pipeline & Experiments]] · [[03 - Projects/Lead-نقاشی/Outreach Compliance|Outreach Compliance]]
- [[03 - Projects/Lead-نقاشی/Report - Lead-نقاشی - Sydney Lead Channels 2026|Report - Sydney Lead Channels 2026]]
- [[03 - Projects/Lead-نقاشی/knowledge-base|knowledge-base]] · [[03 - Projects/Lead-نقاشی/AiFarm-Lead/ARCHITECTURE_MASTER|AiFarm ARCHITECTURE_MASTER]]
- [[03 - Projects/Lead-نقاشی/Lead-نقاشی|لاگ پیام‌های تلگرام]]
