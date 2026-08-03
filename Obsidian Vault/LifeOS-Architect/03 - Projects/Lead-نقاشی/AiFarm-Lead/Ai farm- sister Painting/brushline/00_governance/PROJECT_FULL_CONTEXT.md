# PROJECT FULL CONTEXT — Brushline (فایلِ مرجعِ کامل پروژه)

> **هدفِ این سند:** یک فایلِ تک و self-contained که ساختارِ کاملِ دایرکتوری + خلاصهٔ نقش/محتوای هر فایل را در خود دارد. هر chat/agent جدید با خواندنِ **فقط همین یک فایل** باید کلِ نقشهٔ پروژه را داشته باشد — بدونِ نیاز به وصل‌کردنِ پوشه یا بازکردنِ ۴۲ فایلِ جدا.
> **این سند جایگزینِ `PROJECT_MANIFEST`/`PROJECT_OVERVIEW` نیست؛ تکمیل‌کننده است.** آن دو نقطهٔ ورودِ رسمیِ کاری‌اند (readiness gate / one-pager)؛ این یکی **context-loader کامل** برای هر مدل/chat تازه.
> ساخته‌شده: 2026-06-30 · پوشش: تمامِ ۴۲ فایلِ `.md` + ۱ PDF داخلِ `brushline/`. اگر فایلِ جدید اضافه/حذف شد، این سند باید **به‌روزرسانی شود** (§۷).

---

## ۰. این پروژه چیست — یک پاراگراف

**Brushline** = مغزِ marketing/lead-gen چندایجنتیِ یک کسب‌وکارِ نقاشیِ ساختمان (داخلی/بیرونی) در سیدنی، NSW، استرالیا. محتوا/پاسخ/quote/follow-up را **draft** می‌کند، از سه دروازه رد می‌کند (Constitution Gate → Human Approval → Audit Log)، و به ServiceM8/Tradify **sync** می‌شود — بدونِ بازسازیِ آن‌ها. معماری = **reuse از LANGAR** (ماژولِ خواهر)، نه از صفر. درگاهِ Operator (آرمین) = **ربات تلگرام**، تنها کانال. لایهٔ تئوری **کامل و سازگار** است؛ هیچ کدی هنوز نوشته نشده — پروژه منتظرِ ورودیِ Operator (R11/R12، §۵) برای شروعِ فاز ۰ است.

## ۱. سه Invariant + تصمیم‌های قفل (روحِ پروژه — هرگز نقض نشود)

- **INV-1** — هیچ publish/spend/پیام بدونِ human approval.
- **INV-2** — PII/مالی هرگز در LANGAR/memory؛ دادهٔ حساس در AU.
- **INV-3** — هر auto-execution = kill switch + spend cap + hash-chained audit.

تصمیم‌های قفل (Decision Record): ۱) خواهرِ LANGAR (reuse)، نه از صفر. ۲) `draft → human approval → publish/send/sync`. ۳) owned-first؛ rented فقط پل. ۴) integrate, don't duplicate (ServiceM8/Tradify). ۵) AU compliance (Spam Act/APP7/ACL). ۶) سه Invariant غیرقابل‌حذف. ۷) Capital Works = سگمنتِ strata، نه برندِ جدا. ۸) رابطِ Operator = ربات تلگرام، تنها کانال (TG-01).

## ۲. نقشهٔ کاملِ دایرکتوری

```
brushline/
├── README.md                              ← نقطهٔ ورودِ سریع
├── 00_governance/        (۹ فایل)          ← حاکمیت، entry point، instructions
│   ├── PROJECT_MANIFEST.md                ← فهرست/decision record/readiness gate
│   ├── PROJECT_OVERVIEW.md                ← one-pager وضعیت
│   ├── PROJECT_FULL_CONTEXT.md            ← همین سند
│   ├── BLUEPRINT.md                       ← معماری + تصمیم‌های قفل
│   ├── ROADMAP.md                         ← فازها (v3) + DoD
│   ├── MASTER_INSTRUCTIONS.md             ← custom instructions دائمی
│   ├── CLAUDE_PROJECT_SETUP.md            ← راه‌اندازیِ CoWork project
│   ├── GLOSSARY.md                        ← کانونِ اصطلاحات
│   └── CONFIG_parameters.md               ← تک‌منبعِ پارامترها
├── 10_knowledge_base/    (۱۵ فایل: KB-00..KB-14) ← سیستمِ AI + بازار + انطباق
├── 20_specs/             (۲ فایل)          ← MVP spec + Threat Model
├── 30_process/           (۳ فایل)          ← پرامپتِ تکمیل، ممیزی، تحقیقِ عمیق
├── 40_operations/        (۱۰ فایل: OPS-00..09) ← عملیاتِ واقعیِ نقاشی
├── 50_interface/         (۱ فایل)          ← TG-01 (تلگرام)
├── 90_reference/         (۱ md + ۱ pdf)    ← مراجعِ خارجی/checklist
└── 99_archive/           (۱ فایل یادداشت)  ← بایگانیِ نسخه‌های قدیمی
```

**خلاصهٔ آماری:** ۴۳ فایلِ Markdown شاملِ همینِ سند (۴۲ فایلِ پیشین، ≈ ۳٬۰۰۰ خط) + ۱ PDF. منبعِ حقیقت = فقط `.md`های داخلِ `brushline/`؛ PDFها صرفاً بایگانی/مرجع‌اند.

---

## ۳. خلاصهٔ هر فایل، به‌تفکیکِ پوشه

### `00_governance/` — حاکمیت و نقطهٔ ورود

| فایل | نقش/خلاصه |
|---|---|
| `PROJECT_MANIFEST.md` | فهرستِ کامل + readiness gate پیش‌از‌کد. R1–R10 ✅؛ فقط R11 (verify CONFIG) و R12 (سه عددِ مالیِ واقعی) باز — ورودیِ Operator. |
| `PROJECT_OVERVIEW.md` | one-pager: پروژه چیست، ۱۲ نقشِ agent، وضعیتِ هر لایه، قدمِ بعدی. نقطهٔ شروعِ سریع برای anAI تازه‌وارد. |
| `PROJECT_FULL_CONTEXT.md` | همین سند — context-loader کامل (ساختار + خلاصهٔ هر فایل). |
| `BLUEPRINT.md` | معماریِ مفهومی (00-Orchestrator → Workers A-F → Gate → Queue → Publish/Audit)، تصمیم‌های load-bearing، governance-risk غیرقابل‌حذف. |
| `ROADMAP.md` | ROADMAP v3: ۱۵ پیش‌نیازِ تئوری (همه ✅)، ۷ فازِ ساخت (۰ تا ۶) با گیتِ ایمنی، سگمنت‌ها، milestones، cost checkpoints. |
| `MASTER_INSTRUCTIONS.md` | دستورِ دائمیِ CoWork project — نقش/لحن، نحوهٔ استفاده از KB، نحوهٔ ساختِ خروجی، ضدِ توهم، DO NOT list، قراردادِ session. |
| `CLAUDE_PROJECT_SETUP.md` | راه‌اندازیِ خودِ Project (محدودیتِ پلن، خلاصهٔ custom instructions برای paste، manifest، قراردادِ session). |
| `GLOSSARY.md` | کانونِ اصطلاحات: نام‌ها (Brushline/LANGAR)، سگمنت‌ها، سه Invariant، شناسه‌ها (KB-NN/INV-N/US-N)، اصطلاحاتِ کلیدی، مدل‌های LLM. |
| `CONFIG_parameters.md` | تک‌منبعِ پارامترها: مالی (fx_aud_usd و...)، SLA صف، انطباق، memory، audit، eval. هیچ‌جای دیگر hard-code نشود. |

### `10_knowledge_base/` — سیستمِ AI، بازار، انطباق (KB-00 تا KB-14)

| KB | نقش/خلاصه |
|---|---|
| KB-00 | Master Synthesis — نقشهٔ متصلِ همهٔ KBها، context diagram، data flow (sequence)، ER مدلِ داده، و بخشِ استراتژیکِ «Capital Works به‌عنوان pre-intent wedge». |
| KB-01 | Architecture + Tool Registry + Integration — augmented-LLM، پنج الگوی Anthropic، tool registry در ۷ namespace، integration با ServiceM8/Tradify. |
| KB-02 | Financial Model (AUD) — هزینهٔ core ~AUD ۱۵–۶۵/ماه، cost-per-booked-job به‌جای cost-per-lead، جدولِ pricing مدل‌ها. |
| KB-03 | Publishing & AU Governance — مسیرِ امنِ انتشار پس از approval + recheckِ دومرحله‌ای پیش از send. |
| KB-04 | Agent Memory — scoped per-task context (نه دائمی)، فایل‌سیستمِ `/memories`، هیچ PII در memory (INV-2). |
| KB-05 | Human Approval Queue — state machine `DRAFT→PENDING_REVIEW→(APPROVED|EDITED|REJECTED)`، تنها نقطهٔ مجازِ publish/send/sync. |
| KB-06 | Audit Log — رکوردِ append-only و hash-chained؛ مدرکِ انطباق برای ACMA/OAIC/ACCC. |
| KB-07 | Constitution Gate — چهار خانوادهٔ بررسی: ACL، Spam Act، Privacy/APP7، Data Sovereignty؛ معادلِ Evaluator-Optimizer. |
| KB-08 | Evaluation — eval-driven، Wilson lower-bound برای A/B، north metric = cost-per-booked-job. |
| KB-09 | Leads, Consent & CRM — چرخهٔ کاملِ lead: capture→consent→speed-to-lead→follow-up(۲/۵/۱۰)→sync→review request. |
| KB-10 | Prompt Library — کتابخانهٔ پرامپت (creativity injectors + copy/content با گاردِ ACL/Spam). |
| KB-11 | Engineering Excellence — اصولِ Anthropic «Building Effective Agents»؛ تا وقتی workflow کافی است، agent نساز. |
| KB-12 | Australia Compliance — Spam Act 2003، Privacy Act 1988+۲۰۲۴، ACL، Do Not Call؛ ⚠️ نه مشاورهٔ حقوقی. |
| KB-13 | Market Research — owned vs rented channel، سفرِ خریدار، کانال‌ها، رقبا (سیدنیِ نقاشی). |
| KB-14 | Ecosystem + Lead Signals + Capital Works — pre-intent signals، hot-spotهای سیدنی، Capital Works به‌عنوان سگمنتِ strata. |

### `20_specs/` — مشخصاتِ فنی و امنیت

| فایل | نقش/خلاصه |
|---|---|
| `MVP_system_requirements.md` | تبدیلِ KB-00 به functional spec: C4-style context، مدلِ داده، سطحِ API/UI، user storyها — هیچ کدی نیست. |
| `THREAT_MODEL.md` | STRIDE سبک، مرزِ اعتماد، جدولِ تهدید×کنترل×KB؛ خانهٔ اصلِ ۴/۵ حاکمیتی (tool gateway/least-privilege/no-SPOF). |

### `30_process/` — فرایند و ممیزی

| فایل | نقش/خلاصه |
|---|---|
| `BRUSHLINE_theory_completion_prompt.md` | پرامپتِ اجراییِ مادر برای تکمیلِ نقاطِ ناقصِ تئوری؛ هر Work Package یک KB می‌سازد. |
| `CONSISTENCY_REPORT.md` | گذرِ ممیزیِ کلِ مجموعه + «Operating Picture» بصری (استعارهٔ خطِ تولیدِ اعتماد). |
| `DEEP_RESEARCH_PROMPT.md` | پرامپتِ پژوهشیِ مباحثی که تحقیقِ عمیق‌تر می‌خواهند (حقوقِ AU، APIهای واقعی، LANGAR، go-to-market). |

### `40_operations/` — عملیاتِ واقعیِ کسب‌وکارِ نقاشی (۲۰٪ گم‌شده‌ای که اضافه شد)

| فایل | نقش/خلاصه |
|---|---|
| `OPS-00_operations_index.md` | فهرستِ لایهٔ عملیاتی + نگاشتِ هر سند به agent/KB مربوط. |
| `OPS-01_quoting_estimation_framework.md` | منطقِ برآورد/قیمت‌گذاری؛ Brushline قیمتِ نهایی نمی‌دهد، فقط draft با بازهٔ قیمت می‌سازد. |
| `OPS-02_site_inspection_checklist.md` | چک‌لیستِ بازدیدِ سایت پیش از quote نهایی (m²، prep، ریسکِ ایمنی). |
| `OPS-03_job_workflow_sop.md` | SOP گام‌به‌گام از دریافتِ lead تا warranty؛ هیچ ارسالی بدونِ تأییدِ تلگرام. |
| `OPS-04_customer_journey.md` | سفرِ مشتری در ۵ سگمنت؛ مدلِ ۶ مرحله (Unaware→Post-job). |
| `OPS-05_sales_scripts_objections.md` | اسکریپت‌های فروش/صلاحیت‌سنجی/پاسخ‌به‌اعتراض؛ صداقت > فشار. |
| `OPS-06_marketing_content_system.md` | سیستمِ محتواییِ owned-first؛ ستون‌های محتوا برای ۵ سگمنت. |
| `OPS-07_website_landing_structure.md` | ساختارِ sitemap وب‌سایت + suburb pages + GBP. |
| `OPS-08_crm_pipeline.md` | پایپ‌لاینِ CRM (state machine از NEW تا booked) + sync به ServiceM8/Tradify. |
| `OPS-09_nsw_operational_compliance.md` | انطباقِ سطحِ تردِ فیزیکی: مجوز، HBCF، WHS، lead-paint/asbestos؛ ⚠️ نه مشاورهٔ حقوقی. |

### `50_interface/` — رابطِ Operator

| فایل | نقش/خلاصه |
|---|---|
| `TG-01_telegram_single_channel_design.md` | تصمیمِ ۸: ربات تلگرام = تنها کانالِ Operator (kickoff/approve/edit/reject/گزارش). جایگزینِ UI وب در MVP. |

### `90_reference/` و `99_archive/`

| فایل | نقش/خلاصه |
|---|---|
| `90_reference/_REFERENCE_NOTE.md` | یادداشت: `LANGAR_kit_1/2.pdf` و `fusion-multiagent-2026-checklist.pdf` باید جدا آپلود شوند تا bundle کامل شود. |
| `90_reference/fusion-multiagent-2026-checklist.pdf` | ۷ اصلِ حاکمیتیِ fusion multi-agent (موجود؛ LANGAR kit هنوز آپلود نشده). |
| `99_archive/DEDUP_NOTE.md` | یادداشتِ بایگانی/رفعِ تکرار؛ منبعِ کانونیک = فقط `.md`های داخلِ `brushline/`. |

---

## ۴. وضعیتِ فعلیِ پروژه (Phase Gate)

لایهٔ تئوری **کامل و سازگار** (۱۵ پیش‌نیاز ✅ در ROADMAP، ۱۰ شرطِ معماری ✅ در MANIFEST). تنها بازماندهٔ پیش‌از‌کد:

| # | شرط | وضعیت |
|---|---|---|
| R11 | سه قلمِ «verify» در CONFIG (`fx_aud_usd`، Google Places per-request، `spam_penalty_units`) | ⏳ با Operator |
| R12 | سه عددِ اقتصادِ واقعی در KB-02 (`avg_margin_per_job`، `enquiry→quote rate`، `quote→job rate`) | ⏳ با Operator |

با بسته‌شدنِ R11/R12 → شروعِ **فاز ۰** (scaffold/reuse از LANGAR).

## ۵. ورودی‌های بازِ Operator (آرمین) — چیزهایی که فقط تو می‌دونی

این‌ها تنها چیزهایی‌اند که بین پروژه و شروعِ کدنویسی مانده‌اند؛ هیچ‌کدام کارِ مدل نیست:

- **CONFIG:** `fx_aud_usd` (نرخِ روز)، Google Places API per-request، `spam_penalty_units`، `allowed_operator_chat_ids`، `telegram_bot_token`.
- **KB-02 (مالی):** `avg_margin_per_job`، نرخِ `enquiry→quote`، نرخِ `quote→job`.
- **مرجع:** آپلودِ `LANGAR_kit_1.pdf` و `LANGAR_kit_2.pdf` به `90_reference/`.
- **تأییدِ حقوقیِ NSW:** همهٔ قلم‌های تگ‌شدهٔ `[verify-NSW]` در `OPS-09` و `KB-12` (لیستِ کامل در `30_process/DEEP_RESEARCH_PROMPT.md`، بلوکِ R-1).
- **تصمیمِ استراتژیک:** آیا Capital Works (KB-00 §۵) به‌عنوان سگمنتِ اولویت‌دارِ فاز ۵+ ثبت شود در ROADMAP؟ (ریسک/فرصت در KB-00 شفاف شده؛ تصمیم با توست.)

## ۶. قدمِ بعدی

۱. پرکردنِ ورودی‌های §۵. ۲. ثبتِ تصمیمِ Capital Works در BLUEPRINT اگر مثبت بود. ۳. شروعِ فاز ۰ طبقِ `ROADMAP.md` §۲ (scaffold + reuse interfaceهای LANGAR + جدا DB/process؛ گیت: تستِ «هیچ LANGAR» با JOIN جدولِ شخصی).

## ۷. نگه‌داریِ این فایل

این سند یک snapshot است، نه live sync. هر بار که فایلی در `brushline/` اضافه/حذف/جوهریاً تغییر کرد، این فایل باید به‌صورتِ دستی (یا با درخواستِ «این فایل رو آپدیت کن») بازسازی شود — در غیرِ این صورت drift می‌کند و خودش به منبعِ تعارض تبدیل می‌شود (برخلافِ §۱۰ از `MASTER_INSTRUCTIONS`).
