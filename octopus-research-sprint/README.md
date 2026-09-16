# octopus-research-sprint — رشته‌پژوهش ده‌مگاپرامپتی OCTOPUS
ساخته‌شده: 2026-08-18 (موج صفر) · وضعیت: WAVES BLOCKED UNTIL MISSING INPUTS ARRIVE (ببین `00-inputs/PROJECT-EVIDENCE-MANIFEST.md`)

قانون اصلی: **پژوهش‌ها می‌توانند موازی باشند، ولی پیاده‌سازی باید روی critical path و هر بار تنها یک کارت جلو برود.** هیچ کدنویسی تا خروجی مگاپرامپت ۱۰ و تأیید `CARD-001` شروع نمی‌شود.

ترتیب قطعی: اول حقیقت پروژه، سپس قرارداد و ایمنی، بعد حافظه و شناخت، و در پایان آزمایشگاه و نقشهٔ جامع.

## ترتیب موج‌ها

| موج | مگاپرامپت | موضوع | وابستگی | اجرا |
|---|---:|---|---|---|
| 0 | آماده‌سازی | ساخت بستهٔ شواهد و پوشه‌ها | ندارد | یک‌بار روی لپ‌تاپ — **انجام شد 2026-08-18** |
| A | 01 | حقیقت عملیاتی، GAP-001 و ممیزی معماری | موج 0 | اول و مستقل |
| B | 02 | Contract Spine و Envelopeها | R01 | موازی با R08 |
| B | 08 | امنیت، قانون اساسی و Autonomy Ladder | R01 | موازی با R02 |
| C | 03 | حافظه، یادگیری و Negative Memory | R01 + R02 | موازی با R04 و R09 |
| C | 04 | Homeostatic Core | R01 + R02 + R08 | موازی با R03 و R09 |
| C | 09 | Sensorium، grounding و صد حس | R01 + R02 | موازی با R03 و R04 |
| D | 05 | World Model، Active Inference و Prediction Ledger | R04 | موازی با R06 |
| D | 06 | شناخت چندعاملی، routing و self-improvement محدود | R02 + R03 + R08 | موازی با R05 |
| E | 07 | Digital Twin و آزمایشگاه ارزیابی | R02 تا R06 + R08 + R09 | بعد از موج D |
| F | 10 | ادغام، رفع تناقض و Master Roadmap | تمام گزارش‌ها | آخرین پژوهش |

## روش اجرا (هر موضوع)

1. مگاپرامپت موضوع را کامل به **Kimi** بده → خروجی خام در `R*/kimi-report.md`.
2. بدون نشان‌دادن خروجی Kimi، همان مگاپرامپت را به **GLM** بده → `R*/glm-report.md`.
3. `comparison.md` را طبق قالب `00-inputs/COMPARISON-TEMPLATE.md` بساز.
4. قاعدهٔ ضدارتقا الزامی: توافق دو مدل = `CLAIMED` با منبع `MODEL_CONVERGENCE_NOT_RUNTIME_EVIDENCE` — هرگز VERIFIED نمی‌شود. داوری اختلاف‌ها فقط با ماتریس A1–A15 در `agent-prompts/DISCOVERY-PHASE1-04-ARBITRATION-CONFLICT-MATRIX-2026-08-18.md`.
5. در طول موج‌های پژوهشی **هیچ فایل پروژه‌ای تغییر نمی‌کند**.

گیت‌های عبور موج‌ها: `00-inputs/WAVE-GATES.yaml` (شامل `WAVE0_SETUP_GATE` تازه که ورودی‌های گمشده را بسته نگه می‌دارد).

## تفاوت‌های ثبت‌شده نسبت به متن برنامه (اصلاح با شواهد مخزن)

برنامهٔ اصلی چند فرض دارد که با آخرین حقیقت مخزن (2026-08-18) نمی‌خوانند؛ ورودی‌ها با نسخهٔ تصحیح‌شده پر شده‌اند:

1. **وضعیت بردها** — برنامه: `UNKNOWN / UNREACHABLE_NO_LAN`. واقعیت: `.182` زنده و فعال (کانال exchange تأییدشده 2026-08-17)، `.138` خاموش‌صدا از 2026-08-16 (wire b003 قطع؛ فرضیه: CIFS)، `.180` بدون هیچ لبهٔ اثبات‌شده، لپ‌تاپ `.191` زنده. جزئیات: `00-inputs/CURRENT-CONSTRAINTS.md`.
2. **GAP-001** — برنامه از R01 «تعریف‌های نامزد» می‌خواهد. واقعیت: تعریف‌شده در D5 (OWNER-DECISIONS) با معیار بسته‌شدن اجرایی؛ فقط امضای رسمی مالک باقی است + هشدار هم‌نامی با GAP-001 تلگرام. راستی‌آزمای آماده: `_ops/world_discovery/gap001_closure_verify.ps1` (حکم فعلی: `PENDING_OWNER_SIGNATURE`).
3. **هم‌پوشانی با باندل DISCOVERY-PHASE1** — R01 به‌جای اختراع دوباره، از خروجی‌های `agent-prompts/DISCOVERY-PHASE1-00…06` استفاده می‌کند (field_id های فریزشده، پاکت شواهد، سیاست فرمان‌ها، ماتریس داوری).
4. **ورودی‌های گمشده** — مگاپرامت‌های 01–10، چک‌لیست ۲۰۰تایی و OBSIDIAN-REBUILD در مخزن نیستند؛ موج A تا رسیدن‌شان مسدود است (فهرست دقیق در مانیفست).

## ترتیب ساخت پس از R10 (خلاصه)

مراحل 0 تا 16 در متن اصلی برنامه: Discovery و canonical ← NOW/GAP-001/Decisions ← Constitution/TCB/Owner Gate ← Contract Spine ← Typed Event/Evidence ← Effect Ledger ← Memory Read Loop ← Digital Twin پایه ← Homeostatic Shadow ← World Model ← Virtual Sensorium ← Multi-agent Routing ← Self-improvement Sandbox ← Canary محلی ← Discovery بردها ← Migration ← Autonomy review.
فعلاً فقط مراحل 0 تا 12 روی لپ‌تاپ قابل پیشبردند؛ مرحلهٔ 14 به بعد تا دسترسی فیزیکی و Owner Decision مسدود می‌ماند. شرط خروج هر مرحله در جدول اصلی برنامه؛ هر بار فقط یک کارت.

## برنامهٔ سریع

- **۴ ساعت اول:** پوشه‌ها ✅ · مانیفست ✅ · اجرای R01 روی Kimi ⏸ (نیازمند مگاپرامپت 01) · R01 مستقل روی GLM ⏸ · comparison ⏸ · سؤال‌های مالک و وضعیت GAP-001 ✅ (در `00-inputs/OPEN-QUESTIONS.md`)
- **۲۴ ساعت:** بستن موج A ← اجرای موازی R02+R08 ← مقایسهٔ چهار گزارش ← contract catalogue و governance invariants موقت
- **۴۸ ساعت:** R03+R04+R09 موازی ← ممیزی organهای موجود ← نقاط reuse ← Now/Next/Later/Reject حس‌ها
- **۷۲ ساعت:** R05+R06 ← R07 پس از گیت‌ها ← R10 ← بیست کارت اول ← بررسی مالک ← شروع فقط `CARD-001`
