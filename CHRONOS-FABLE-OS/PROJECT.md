---
type: project
kind: area
project: "[[CHRONOS-FABLE-OS/PROJECT]]"
status: active
owner: آری
risk_level: low
autonomy_level: read-only
tags: [chronos-fable-os, architecture, meta-synthesis, octopus, safety, knowledge]
created: 2026-07-08
updated: 2026-07-08
---

# پروژه: CHRONOS-FABLE OS (لایهٔ تئوری/معماریِ ارگانیسم زنده)

**هدف:** یک repositoryِ دانشیِ واحد و agent-ready که کل کورپوسِ معماریِ OCTOPUS/CHRONOS را به ساختارِ canonicalِ ۱۶‌پوشه‌ای در می‌آورد، تا هر ایجنتِ دیگری بتواند **پیش از implementation** با صفر context ادامه دهد. تز: `CHRONOS-FABLE OS = CHRONOS-VAULT (بسترِ زمان/اعتماد + شناخت) ⊕ Ari OS (حاکمیت + personal + business + research + worker)`.

**نقش در اکوسیستم:** این **لایهٔ تئوری** همان ارگانیسمِ زندهٔ [[_ops/ORGANISM-SPEC|ORGANISM-SPEC]] است (ledger زنجیرهٔ‌هش، budget/money gate، ضربان، germline). با area دانشیِ [[07 - Knowledge/Time-Architecture/PROJECT|Time-Architecture]] از راهِ DOC-01/DOC-03 هم‌پوشان است. زیر نظارتِ architect؛ فقط additive و read-only.

## Active Context

- money_status: infrastructure (بدون money_link مستقیم) · guard_flags: [RABBIT_HOLE_RISK]
- priority: medium · autonomy: read-only، additive-only
- تمرکز فعلی: بستهٔ agent-ready کامل شد؛ گره به vault و ingestِ منابعِ درون‌vault.
- تغییرات اخیر (2026-07-08، Cowork):
  - سازمان‌دهی کل کورپوس به درختِ ۱۶‌پوشه‌ای + بستنِ ۶ یافتهٔ audit (F-1..F-6). گزارش: [[CHRONOS-FABLE-OS/00_Executive/Audit_2026-07-08|Audit]].
  - **DOC-B حاضر بود** → MER-1 بسته؛ DDL واقعیِ LANGAR از §8 استخراج شد ([[CHRONOS-FABLE-OS/10_Implementation/DataSchemas|DataSchemas]]).
  - **MER-6 نیمهٔ زمان بسته شد** با منابعِ درون‌vault: [[07 - Knowledge/Time-Architecture/theory|theory (verbatim)]] + [[07 - Knowledge/Time-Architecture/experiments|experiments]] → E1..E5 + L/SOC/¼-test.
  - Heart design اضافه شد: [[CHRONOS-FABLE-OS/08_Safety/HeartDesign_PulseCore|HeartDesign_PulseCore]] (از `Octopus_Heart_Design_v1.md`).
- تصمیم‌های باز (verdict مالک): OQ-1 stasis · OQ-2 تأیید `age_tick=is_human` · OQ-4 نام · ratify کردن INV-17*/AP-14*.

## Progress

- چه کار می‌کند: درختِ کامل + navigation spine (README/HANDOFF/MANIFEST/CHANGELOG/index) + master prompt v2؛ شمارش‌ها سالم؛ صفر ارجاعِ شکسته.
- چه مانده: MER-2 (فیلدهای vault + جدول LiteLLM routing) و DOC-04/05/07 verbatim و registry کمّی (MER-3) هنوز BLOCKED؛ قلاب‌های upgrade فعال‌اند.
- مشکلات شناخته: سه فایلِ `.yaml` سبکِ «YAML-ish» غیرِ strict‌اند (از اصل چنین بودند، نه رگرسیون)؛ فقط `index.yaml` machine-parsable است.

## Agent interface

- **می‌خواند:** کل درختِ `CHRONOS-FABLE-OS/`.
- **می‌نویسد:** فقط additive (نوت/نسخهٔ جدید یا append + ثبت در CHANGELOG)؛ نسخهٔ کهنه به `_legacy/`.
- **ممنوع:** overwrite؛ fabricationِ مقدارِ BLOCKED؛ ویرایشِ منابعِ مقدس (`theory.md`)؛ هر اثرِ irreversible/پولی/live.

## Next actions

- [ ] verdict: OQ-1 stasis · OQ-2 `age_tick=is_human` · OQ-4 نام · INV-17*/AP-14*
- [ ] آپلود Survival-Stack اصلی (DOC-A) → بستنِ MER-2 (فیلدهای vault + routing)
- [ ] آپلود `lab seed data.json` → registry کمّی (MER-3)
- [ ] یافتنِ DOC-04/05/07 verbatim در vault یا re-supply → بستنِ کاملِ MER-6
- [ ] پس از Phase 0 ساخت: نگاشتِ L0 DataSchemas.sql به `_ops` زندهٔ موجود

## نوت‌های مرتبط

- [[CHRONOS-FABLE-OS/HANDOFF|HANDOFF — نقطهٔ ورودِ ایجنت]] · [[CHRONOS-FABLE-OS/README|README]] · [[CHRONOS-FABLE-OS/MANIFEST|MANIFEST]]
- [[CHRONOS-FABLE-OS/13_MasterPrompts/MasterSystemPrompt.v2|Master System Prompt v2]]
- ارگانیسم زنده: [[_ops/ORGANISM-SPEC|ORGANISM-SPEC]] · منبعِ زمان: [[07 - Knowledge/Time-Architecture/PROJECT|Time-Architecture]]
