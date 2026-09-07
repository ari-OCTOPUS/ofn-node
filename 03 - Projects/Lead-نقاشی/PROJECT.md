---
type: project
kind: area
project: "[[03 - Projects/Lead-نقاشی/PROJECT]]"
status: active
owner: آری
risk_level: low
autonomy_level: read-only
tags: [lead-gen, painting, sydney, business, painting-os]
created: 2026-07-03
updated: 2026-09-07
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

1. **🎨 Painting-OS — محصول اصلی بیزنس نقاشی (2026-07-12, P1-P3 ساخته شده):**
   - **P1 کوتیشن:** `pricing.py` + `lead_quote.py` — نرخ‌های واقعی سیدنی ($18-65/m²)، QuoteIntake 14 فیلدی، QT-YYYYMMDD-NNN
   - **P2 فاکتور:** `invoice.py` — ATO Tax Invoice، ABN، GST 10%، INV-FY{YY}-{NNN}، PAID از attribution CONFIRMED
   - **P3 ایمیل:** `email_inbound.py` — Gmail OAuth readonly، flag-gated (OCTOPUS_WIRE_EMAIL)، parse_lead_from_email
   - **reconcile v2:** گروه‌بندی CSV بر lead_id → پرداخت جزئی (deposit + balance)
   - **42 تست سبز** (pricing 10 + lead_quote 9 + lead_intake 6 + invoice 8 + email 9)
   - **محدودیت‌ها:** propose-only، $0 stdlib-only، صفر راز جدید، backward-compat
   - **نقشهٔ راه ۱۰ مرحله‌ای:** `کاریابی/08_Painting-OS_Roadmap_v2.md`
   - **تحقیق بازار:** ServiceM8 ($29-79)، Tradify ($70+/user)، AroFlo ($120+)، QuoteIQ ($150-700 USD)، hipages ($129+/ماه)

2. **🦵 پا (Worker):** `_ops/legs/lead_leg.py` — `LeadLeg(Leg)` حلقهٔ paper: `intake` → `draft_quote` → `claim` → `reconcile`. **propose-only:** فقط draft تولید؛ ارسال/پول human-gated. اولین دلارِ paper CONFIRMED شد.

3. آزمایش #۱: کشف segment — کدام بخش بیشترین ارزش per lead می‌دهد.

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


- master-73 کانونیکال؛ مجوز top-5 outreach + PayPal Invoice؛ رجیستری به‌عنوان زمین ACD استاندارد شد (hash a77dadba).
- ۳ قدم بعدی: (۱) اجرای outreach؛ (۲) هم‌ردیف کردن شمارش لید؛ (۳) اتصال به learning_gate.
- باز: بودجه outreach؛ #197.

## Progress

- 2026-09-07: رجیستری ACD استاندارد؛ حکم قابلیتی ACD-01 صادر شد؛ انتقال مهارت SKILL-TOOL-GUARD-V1.
- 2026-09-07: رجیستری منابع به‌عنوان زمین ACD استاندارد شد (hash a77dadba)؛ v4.1 assets_ref پیوست شد.
- **۲۰۲۶-۰۸-۰۱ — چه کار می‌کند:** ماشینِ لیدِ خودمختار زنده (`lead_pipeline` مسلح، کارتِ READY در تاپیکِ 🎨 اثبات‌شده، «گیر=سؤال» کار می‌کند) · سقفِ ۱۰/روزِ دو-لایه با شمارندهٔ durable · transport ِ SMTP نوشته و تست‌شده (ولی تاریک) · Painting-OS ‏P1-P3 · هشت فعلِ قیف از منوی DM برداشته شد («بیزنس هرگز در DM») ولی تایپی زنده است و در `INTENTIONALLY_HIDDEN` با دلیلِ تک‌تک ثبت شده.
- **۲۰۲۶-۰۸-۰۱ — چه مانده:** رأیِ مالک روی `OCTOPUS_SMTP_*` + `OCTOPUS_WIRE_LEAD_OUTBOUND` · پر کردنِ bank details (بلاکرِ فاکتورِ قابلِ پرداخت) · producerهای واقعی به‌جای کاندیدِ synthetic · Gmail OAuth ‏E2E · build اولِ APK ِ TradeQuote · برداشتنِ PARK از reconcile تا `confirmed_revenue_aud` از `null` دربیاید.
- **۲۰۲۶-۰۸-۰۱ — مشکلات شناخته:** تا وقتی producerِ واقعی وصل نشده ورودیِ قوس synthetic است، پس KPIهای «لیدِ واقعی/هفته» همچنان `[To measure]`اند · الگوی «دو مصرف‌کننده روی یک inbox» یک بار بی‌صدا مسیرِ پول را خورد و می‌تواند در producerِ بعدی تکرار شود · ~~ABN وارد نشده~~ تصحیح شد (`abn_valid=true`).
- چه کار می‌کند: Painting-OS P1-P3 کامل (کوتیشن + فاکتور + ایمیل) · زیرساخت brushline · چارچوب آزمایش
- چه مانده: وایر `/lead` تلگرام · Gmail OAuth E2E · فرم وب‌سایت · PDF کوتیشن · فاکتور خودکار · داشبورد · SEO · **build اولین APK از `tradequote_local/` (R30) + پل lead_leg→TradeQuote (flag-off)** · **فاز C پیاده شد؛ مانده: رأیِ مالک روی قراردادها + secretهای ingestion + workerِ outboundِ واقعی (فاز D، رأیِ جدا) + جذبِ producerها (harvest/email → submit_candidate) + freezeِ lead_leg_inbox**
- مشکلات شناخته: ABN واقعی هنوز وارد نشده · Gmail token هنوز صادر نشده

## Next actions

- [ ] (مالک) build اول TradeQuote روی PC: `tradequote_local/docs/BUILD_AND_RELEASE.md` §1 → APK روی S23 FE
- [ ] (ایجنت، بعد از delta-scan) bridge پیشنهادی flag-off: draft کوتیشنِ `lead_quote.py` → قالب سازگار با TradeQuote (فقط فایل خروجی، صفر ارسال)
- [ ] وایر `/lead` تلگرام → `parse_lead_intake()` + `render_quote_html()` (مرحله ۱ roadmap)
- [ ] پر کردن ABN واقعی در `budgets.yaml` (مرحله ۲ roadmap)
- [ ] Gmail OAuth token → تست E2E ایمیل لید (مرحله ۳ roadmap)
- [ ] rotation کلیدها (مالک): Anthropic + Telegram + Tavily + PlanningAlerts + Serper
- [x] تعمیر symlink (2026-07-03)
- [x] Painting-OS P1-P3 ساخته و تست شده (2026-07-12)

## نوت‌های مرتبط

- [[03 - Projects/Lead-نقاشی/Lead Pipeline & Experiments|Lead Pipeline & Experiments]] · [[03 - Projects/Lead-نقاشی/Outreach Compliance|Outreach Compliance]]
- [[03 - Projects/Lead-نقاشی/Report - Lead-نقاشی - Sydney Lead Channels 2026|Report - Sydney Lead Channels 2026]]
- [[03 - Projects/Lead-نقاشی/knowledge-base|knowledge-base]] · [[03 - Projects/Lead-نقاشی/AiFarm-Lead/ARCHITECTURE_MASTER|AiFarm ARCHITECTURE_MASTER]]
- [[03 - Projects/Lead-نقاشی/Lead-نقاشی|لاگ پیام‌های تلگرام]]
- [[03 - Projects/Lead-نقاشی/کاریابی/07_Painting-OS_P1_Quotation_Design|P1 Quotation Design]]
- [[03 - Projects/Lead-نقاشی/کاریابی/08_Painting-OS_Roadmap_v2|10-Stage Roadmap v2]]
