---
type: project
kind: project
project: "[[03 - Projects/اونلی فنز/PROJECT]]"
status: active
owner: آری
risk_level: high
autonomy_level: read-only
tags: [creator-business, faceless]
created: 2026-07-03
updated: 2026-07-12
aliases: ["Project-F", "پروژه اونلی فنز", "Active Context"]
---

# پروژه: اونلی فنز

> 🏗️ **رکنِ ساخت:** [[04 - Architect System/MYCELIAL-MASTER-SPEC|MYCELIAL-MASTER-SPEC]] — این پروژه یک node در §۳ رجیستریِ اتصال است (build/test/delete پشتِ verdict).

**وضعیت:** creator brand با مدل faceless (فقط پا در فاز فعلی) — تیم دونفره ۵۰/۵۰، فاز validation. سند کامل: [[03 - Projects/اونلی فنز/project-master-reference|master-reference]].

**نقش در اکوسیستم:** درآمد آزمایشی؛ زیر نظارت architect (رئیس کل). کد ارجاع در خروجی‌های cross-domain: **«Project-F»**.

## 🎛 رابطِ کنترلِ ایجنتِ مادر (Architect) — cross-domain
- قراردادِ ماشین‌خوان: `PROJECT-F-CONTROL-MANIFEST.json` (صفر-PII، کدِ A/C) · روایت: [[03 - Projects/اونلی فنز/AGENT-CONTROL-INTERFACE|AGENT-CONTROL-INTERFACE]].
- مدلِ کنترلِ مادر: **رصد + صف‌بندیِ verdict + قطعِ اضطراری** — اجرای هیچ اکشنِ بیرونی، بدونِ دورزدنِ GATE 0/Hard-Gated، بدونِ تغییرِ قاعدهٔ قفل‌شده. مجریِ نهاییِ کارِ پرمخاطره = انسان (A).

## Agent interface (تا پیش از ARCHITECT_CHARTER — نسخه حداقلی)

- **خواندن مجاز:** PROJECT.md، master-reference، نوت‌های validation و لاگ آزمایش‌ها.
- **نوشتن مجاز:** فقط پیشنهاد (proposal)، گزارش و draft داخل همین پوشه؛ هیچ اکشن خارجی (پست، پیام، ساخت اکانت، پرداخت) بدون verdict انسانی.
- **ممنوع مطلق:** echo هویت پارتنر، عکس/محتوا، یا هر جزئیات شناسایی‌پذیر در تلگرام، داشبورد یا هر خروجی خارج از این پوشه — فقط کد «Project-F».
- **Security Gate:** تا وقتی ردیف‌های CRITICAL در [[ROTATION_CHECKLIST]] باز است، همه ایجنت‌ها روی این پروژه read-only هستند.

## KPIs (فاز validation)

delivery-rate پارتنر در trial sprint `[To measure]` · engagement روی teaserها `[To measure]` · نتیجه Track B (payment/banking پایدار: بله/خیر) — متریک درآمد از ابتدا به صبا گزارش شود (شرط تعهد او).

## Open blockers

**GATE 0: محل اقامت پارتنر ثبت و شاخه A/B انتخاب شود** — «محل اقامت پارتنر: ___ · تاریخ: ___ · پیامد: Branch A/B» ([[03 - Projects/اونلی فنز/architecture-blueprint-2026-07-04|بلوپرینت §۱]]) · ریسک #۱ (consistency زیر friction) هنوز تست‌نشده · مرز body در production plan با رضایت فعلی صبا در تضاد `[OPEN]` · سؤال آخر پرسشنامه نامفهوم ماند · Security Gate بسته

## Active Context

- تمرکز فعلی: اسکلتِ موتورِ اکتساب ساخته/تست‌شده؛ **منتظر G0** برای زنده‌شدن
- **2026-07-12 — موتورِ اکتساب + تحقیقِ رقبا + ROADMAP:** اسکلتِ کدِ propose-only ساخته و تست شد (commitها `1d5b363`/`c7124df`/`ae31bfd`؛ ۲۲/۲۲ تست): `brain/acquisition_pipeline.py` (draft→صف→approve→آمادهٔ پستِ دستی، بدونِ افکتورِ بیرونی) + `studio/affirm.py` + سیم‌کشیِ `/pf_*` در لنگر + `affirm` در استودیوی صبا. **تحقیقِ رقبا/بازار** → [[03 - Projects/اونلی فنز/02 - Research/COMPETITOR-MARKET-LANDSCAPE-2026-07-12|COMPETITOR-MARKET-LANDSCAPE]] (dual-platform؛ FeetFinder = موتورِ فروشِ سریعِ ۷–۱۴روزه؛ پولِ واقعی در PPV/custom؛ **retention = گافِ اصلیِ ما**). **دستورالعملِ کاملِ ۱۰-مرحلهٔ بعدی** → [[03 - Projects/اونلی فنز/00 - Control/ROADMAP-10-STAGES-2026-07-12|ROADMAP-10-STAGES]]. همه پشتِ GATE 0.
- **2026-07-12 — Brand pack (propose-only):** لایهٔ هویتِ برند در [[03 - Projects/اونلی فنز/01 - Strategy/Identity/_INDEX|01-Strategy/Identity]] ساخته شد (IDENTITY، BRAND-CHARTER، VOICE-AND-STYLE، CLAIMS-REGISTER، BRAND-NAME-DECISION) با ورک‌فلوِ ۴-ایجنتهٔ کالیبراسیون. یافته‌ها: نامِ #۱ = **Anar Soles** / reserve Yalda Arch (تنها صفر-collision؛ منتظر verdict #۶، به #۹ گره‌خورده) · نام‌های شهری (Softly Sydney/Harbour Soles) حذف شدند (نقضِ #۶) · #۹ نامتقارن است (قاعدهٔ #۶ حاکم؛ سیگنالِ دیاسپورا فقط غیرمتنی) · صدا = warm/unhurried/wry · گافِ AI-image بسته شد (قفلِ human-only پیشنهادی) · نقصِ انطباقِ «Sydney light» در Playbook برای اصلاحِ گیت‌دار flag شد. هیچ انتشار/اکانت/کپیِ فارسی.
- **2026-07-12 — نقشه‌برداری (Cartography) + بستهٔ handoff:** نقشهٔ راستی‌آزمایی‌شده در [[03 - Projects/اونلی فنز/00 - Control/CARTOGRAPHY-2026-07-12|CARTOGRAPHY]] (dedup دقیق md5: ۱۳ identical + ۹ stale mirror؛ root = canonical تأیید شد؛ code deep-read: project_f_brain مرده در runtime، learning سیم‌نشده، drafts.json = ۲۴۴ ردیف تستی، secretها پاک، kill-switchها واقعی) · [[03 - Projects/اونلی فنز/00 - Control/SOURCE-OF-TRUTH-MATRIX|SoT-Matrix]] · [[03 - Projects/اونلی فنز/00 - Control/RISK-LADDER|RISK-LADDER]] · [[03 - Projects/اونلی فنز/00 - Control/MIGRATION-MAP-2026-07-12|MIGRATION-MAP]] (⛔ اجرا نشده — verdict ‏PF-STRUCT-V2) · برنامهٔ ایجنت بعدی: [[03 - Projects/اونلی فنز/00 - Control/HANDOFF-NEXT-AGENT|HANDOFF-NEXT-AGENT]] · ۳ verdict جدید در VERDICT_QUEUE (STRUCT-V2 / STATE-RESET-V1 / CODE-REFACTOR-V1)
- **2026-07-10 — Round 2 تحقیق جامع ۷-محوره integrate شد** → [[03 - Projects/اونلی فنز/RESEARCH-INTEGRATION-round2-2026-07-10|round2]]: تأیید سوم مسیر (dual-platform/Reddit-engine/AI-درفت-انسان-می‌فرستد) · ریسک جدید R4 (فوت Radvinsky + فروش سهم OF ‏>$3B) · AU زیر-۱۶ live · یافتهٔ free-page/price-lock → تقویت EXT-04 برای #۱۰ · کاتالوگ ۵۸-روشی جذب + unit-economics + spec تکمیلی مغز (~AUD 8–12/ماه) + سؤالات مشاور AU · سؤال‌های باز جدید #۱۷–#۲۰
- **2026-07-10 — M2/M3/M4 + PROMPT D + لنگر:** ماتریس تصمیم ‏[[03 - Projects/اونلی فنز/DECISION-MATRIX-M2-2026-07-10|M2]] · پلن ‏[[03 - Projects/اونلی فنز/COMPLIANT-PLAYBOOK-M3-2026-07-10|M3]] · بستن threadها ‏[[03 - Projects/اونلی فنز/THREAD-CLOSURE-D-2026-07-10|THREAD-CLOSURE-D]] (T1–T8) · ۵ درفت در `drafts-awaiting-gate/` · **کاکپیت تلگرامی «لنگر»** در `langar/` (propose-only، خودآگاه، مسئول ارتقا، ۸/۸ تست منطق سبز، فعال‌سازی گیت‌دار). ساعت صبا بسته (~۳h). ۱۱ verdict منتظر تصمیم آری (THREAD-CLOSURE §۹).
- تغییرات اخیر: 2026-07-03 — ثبت [[03 - Projects/اونلی فنز/پرسشنامه پارتنر - پاسخ‌های صبا|پاسخ‌های صبا]]؛ مرز محتوا قفل شد: فقط پا، بدون صورت/بدن + geo-block ایران · 2026-07-04 — کیت مغز پروژه ساخته شد · 2026-07-05 — [[03 - Projects/اونلی فنز/STATE-REPORT-2026-07-05|STATE-REPORT]] + verification pass (۸/۹ تناقض تأیید، ۱ اصلاح) + اعمال patch بلوپرینت §۱۱ · **2026-07-06 — Round 1 تحقیق بیرونی integrate شد → [[03 - Projects/اونلی فنز/RESEARCH-INTEGRATION-round1|RESEARCH-INTEGRATION-round1]]**: مسیر فعلی تأیید مستقل؛ REJECT تلگرام/کریپتو (قاعدهٔ #۳)؛ ToS ‏OF ممنوعیت AI-chat را [FACT] کرد → الگوی «درفت در کنسول جدا + paste دستی» ابقا؛ ۳ سؤال باز جدید (#۱۴ شفافیت DM، #۱۵ ‏C2PA، #۱۶ ‏B2B)؛ KPI کاندید: unlock-rate، $/script-start، چرخهٔ Custom، $/ساعت DM
- ۳ قدم بعدی: (۱) Track B/C — تحقیق desk درباره payment/banking و automation-fit، time-box یک هفته (۲) بازپرسیدن سؤال آخر پرسشنامه به زبان ساده‌تر (۳) طراحی Track A sprint با متریک صریح و گزارش‌دهی زودهنگام نتیجه مالی به صبا
- تصمیم‌های باز: «مسیر safe expansion به body» در production plan — صبا فعلاً بدن را رد کرده؛ منجمد یا حذف؟

## Progress

- چه کار می‌کند: master-reference کامل، production plan، funnel دیاسپورا، رجیستر ۵ ریسک، پرسشنامه پارتنر پاسخ‌داده‌شده
- چه مانده: Track A/B/C validation، زیرساخت legal/banking (مشروط به عبور از گیت‌ها)
- مشکلات شناخته: تعهد پارتنر مشروط به دیدنِ مسیر پول‌دهی است؛ تضاد مرز body با production plan

## Next actions

- [ ] 🗺 **دستورالعملِ اجرا = [[03 - Projects/اونلی فنز/00 - Control/ROADMAP-10-STAGES-2026-07-12|ROADMAP ۱۰-مرحله]]** — مرحلهٔ ۱ (بستنِ GATE 0) کلِ زنجیره را باز می‌کند
- [ ] **۱۱ verdict منتظر تو** (THREAD-CLOSURE §۹): G0 · Playbook+M3-a · قاعدهٔ بالانس >$100 · سقف مغز AUD 15 · نردبان EXT-04 · برند Anar Soles · Fansly discovery-first · حالت labeling X · بلاک AU · فعال‌سازی لنگر · انجماد body
- [ ] **G0** — ثبت محل اقامت پارتنر + انتخاب Branch A/B (بلوپرینت §۱)
- [ ] ارسال پیام آماده به صبا (بازپرسیدن سؤال آخر + انتظارات — بلوپرینت §۴.۲) و ثبت جواب
- [ ] توافق مکتوب دونفره (بلوپرینت §۴.۱) — فقط بعد از Branch A
- [ ] تصمیم: انجماد/حذف «expansion به body» + تعیین hours واقعی (30h vs 3–5h)
- [ ] روز صفر زیرساخت (بلوپرینت §۵، ~۴–۵ ساعت) → شروع warm-up هفته ۱
- [x] Track B + C (desk research) — انجام شد 2026-07-04: GO conditional / GO limited

## نوت‌های مرتبط

- [[03 - Projects/اونلی فنز/پرسشنامه پارتنر - پاسخ‌های صبا|پرسشنامه پارتنر — پاسخ‌های صبا]]
- [[03 - Projects/اونلی فنز/اونلی فنز|لاگ پیام‌های تلگرام — اونلی فنز]]
- [[03 - Projects/اونلی فنز/Knowledge_Base_Memory_Synthesis|Knowledge_Base_Memory_Synthesis]]
- [[03 - Projects/اونلی فنز/project-master-reference|project-master-reference]]

## مرتبط

<!-- Tier A · CONNECTIONS-MAP (_memory) · اعمال 2026-07-04 -->
- [[04 - Architect System/architect/ARCHITECT_CHARTER|ARCHITECT_CHARTER]]

## 🎛 کابین کنترل (two-brain)

- کابین مشترک: ارتیفکت `fleet-live-dashboard` · نقشه: [[_memory/TWO-BRAIN-CONTROL-BLUEPRINT|TWO-BRAIN]] · نقشهٔ ساخت: [[_memory/FRANKENSTEIN-BUILD-PLAN|FRANKENSTEIN-BUILD-PLAN]]
- عملیات استاندارد از کابین (intent → sendPrompt): «تست <پروژه>» = validators + چک کد + تست قرارداد · «بساز» = اسکلت از `_Templates` + ثبت همین‌جا · «آرشیو» = فقط انتقال به `_Archive`/`_Duplicates` (هرگز حذف واقعی).
- تست قرارداد این پروژه: هنوز تعریف نشده — طبق BUILD-PLAN §۲ تعریف شود.