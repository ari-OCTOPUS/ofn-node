# PROJECT MANIFEST — Brushline (نسخهٔ مرجعِ پیش‌از‌کدنویسی)

> این سند، فهرستِ مرجعِ همهٔ فایل‌هایی است که **باید** قبل از شروعِ کدنویسی (فاز ۰) در پروژه باشند. نقشِ README/index + decision record + readiness gate. هر فایل: نقش، وضعیت، وابستگی.
> قاعده: هیچ کدی شروع نشود تا «گیتِ آمادگی» (§۵) سبز باشد.

---

## ۰. ساختارِ canonical پروژه

```
brushline/
├── 00_governance/
│   ├── PROJECT_MANIFEST.md        ← این سند (entry point)
│   ├── BLUEPRINT.md               ← معماری و تصمیم‌های قفل
│   ├── ROADMAP_v3.md              ← فازها + DoD + سگمنت‌ها
│   ├── CLAUDE_PROJECT_SETUP.md    ← instructions پروژه
│   ├── GLOSSARY.md                ← کانونِ اصطلاحات
│   └── CONFIG_parameters.md       ← تک‌منبعِ پارامترها
├── 10_knowledge_base/
│   ├── KB-00_master_synthesis.md
│   ├── KB-01_architecture.md
│   ├── KB-02_financial_model.md
│   ├── KB-03_publishing.md
│   ├── KB-04_memory.md
│   ├── KB-05_human_approval_queue.md
│   ├── KB-06_audit_log.md
│   ├── KB-07_constitution_gate.md
│   ├── KB-08_eval.md
│   ├── KB-09_leads_consent_crm.md
│   ├── KB-10_prompts.md
│   ├── KB-11_engineering.md
│   ├── KB-12_australia.md
│   ├── KB-13_market_research.md
│   └── KB-14_ecosystem.md
├── 20_specs/
│   ├── MVP_system_requirements.md
│   └── THREAT_MODEL.md
├── 30_process/
│   ├── BRUSHLINE_theory_completion_prompt.md
│   └── CONSISTENCY_REPORT.md
└── 90_reference/
    ├── LANGAR_kit_1.pdf           ← مرجعِ ماژولِ خواهر
    ├── LANGAR_kit_2.pdf
    └── fusion_multiagent_checklist.pdf  ← ۷ اصلِ حاکمیتی
```

---

## ۱. Governance / Entry (همیشه در پروژه)

| فایل | نقش | وضعیت |
|---|---|---|
| PROJECT_MANIFEST | فهرست/index/readiness | ✅ این سند |
| PROJECT_FULL_CONTEXT | context-loader کامل (ساختار + خلاصهٔ هر فایل) برای chat/agentِ جدید | ✅ ساخته‌شد |
| BLUEPRINT | معماری + تصمیم‌های قفل | ✅ موجود |
| ROADMAP_v3 | فازها + DoD + سگمنت | ✅ به‌روز شد |
| CLAUDE_PROJECT_SETUP | instructions | ✅ موجود |
| GLOSSARY | کانونِ اصطلاحات | ✅ ساخته‌شد |
| CONFIG_parameters | تک‌منبعِ پارامتر | ✅ ساخته‌شد |

## ۲. Knowledge Base — KB-00..KB-14 (همیشه در پروژه)

| KB | عنوان | وضعیت | وابسته به |
|---|---|---|---|
| KB-00 | Master Synthesis | ✅ | همه |
| KB-01 | Architecture + Tools + Integration | ✅ | KB-13 |
| KB-02 | Financial Model (AUD) | ✅ | KB-01/11/13 |
| KB-03 | Publishing + AU | ✅ | KB-07/12 |
| KB-04 | Agent Memory | ✅ | KB-01/06 |
| KB-05 | Human Approval Queue | ✅ | KB-01/07 |
| KB-06 | Audit Log | ✅ | KB-05/07 |
| KB-07 | Constitution Gate | ✅ | KB-12/01 |
| KB-08 | Eval | ✅ | KB-02 |
| KB-09 | Leads + Consent + CRM | ✅ | KB-01/07 |
| KB-10 | Prompt Library | ✅ | KB-07 |
| KB-11 | Engineering | ✅ | KB-13 |
| KB-12 | Australia Compliance | ✅ | — |
| KB-13 | Market Research | ✅ | — |
| KB-14 | Ecosystem + Signals + Capital Works | ✅ | KB-13 |

## ۳. Specs / Security (همیشه در پروژه)

| فایل | نقش | وضعیت |
|---|---|---|
| MVP_system_requirements | functional spec + data model + API/UI + user stories | ✅ |
| THREAT_MODEL | امنیت + STRIDE + multi-tenant | ✅ (multi-tenant اضافه شد) |

## ۴. Process / Reference (در پروژه، ولی working/مرجع)

| فایل | نقش | وضعیت |
|---|---|---|
| BRUSHLINE_theory_completion_prompt | پرامپتِ تکمیل | ✅ |
| CONSISTENCY_REPORT | ممیزی + operating picture | ✅ |
| LANGAR kit (×2) | مرجعِ خواهر | ✅ موجود |
| fusion_multiagent_checklist | ۷ اصلِ حاکمیتی | ✅ موجود |

---

## ۵. گیتِ آمادگیِ پیش‌از‌کدنویسی (Definition of Ready — فاز ۰)

عینِ چک‌لیستِ مهندس قبل از زدنِ اولین خط کد:

| # | شرط | وضعیت |
|---|---|---|
| R1 | معماری مشخص (الگو + tool registry + integration) | ✅ KB-01 |
| R2 | مدلِ داده مفهومی (ER) | ✅ KB-00 §۴ + MVP |
| R3 | سطحِ API/UI مفهومی | ✅ MVP §۵/۶ |
| R4 | پارامترها تک‌منبع (نه hard-code) | ✅ CONFIG |
| R5 | قوانینِ انطباق اجرایی (Gate) | ✅ KB-07/03/12 |
| R6 | HITL + audit طراحی‌شده | ✅ KB-05/06 |
| R7 | threat model + governance ۷ اصل | ✅ THREAT_MODEL |
| R8 | eval/metric تعریف‌شده | ✅ KB-08 |
| R9 | naming/terms قفل (no drift) | ✅ GLOSSARY |
| R10 | DoD هر فاز روشن | ✅ ROADMAP_v3 |
| **R11** | سه قلمِ «verify» در CONFIG بسته شود | ✅ `fx_aud_usd=1.45`، Google Places $32/1K، `spam_penalty_units=330` (Jun 2026) |
| **R12** | سه عددِ اقتصادِ واقعی (KB-02) | ✅ `avg_margin=AUD 1000`، `enquiry→quote=60%`، `quote→job=33%` |

> **گیتِ فاز ۰ سبز است.** همهٔ ۱۲ شرط ✅. → شروعِ scaffold/reuse مجاز است.

---

## ۶. تصمیم‌های قفل (Decision Record — مرجع)
۱. خواهرِ LANGAR (reuse)، نه از صفر. ۲. `draft → human approval → publish/send/sync`. ۳. owned-first؛ rented فقط پل. ۴. integrate, don't duplicate (ServiceM8/Tradify). ۵. AU compliance (Spam/APP7/ACL). ۶. سه Invariant غیرقابل‌حذف. ۷. Capital Works = سگمنتِ strata، نه brand جدا.

## ۷. کنوانسیونِ نسخه/نام
- فایلِ نهایی در پروژه: نامِ بدونِ `_vN` (آخرین نسخه canonical). نسخه‌های کاری `_vN` فقط در outputs.
- اصطلاحات/نام‌ها فقط از GLOSSARY. پارامترها فقط از CONFIG.
- هر سند: Markdown + Mermaid، بدونِ کد (تا فاز ۰).

## ۸. خلاصه
**۲۹ فایلِ مرجع** (۶ governance + ۱۵ KB + ۲ specs + ۴ process/ref + ۲ این‌جا ساخته‌شده). لایهٔ تئوری کامل و سازگار. تنها بازماندهٔ پیش‌از‌کد = R11/R12 (ورودیِ Operator). با بسته‌شدنشان → **شروعِ فاز ۰**.

## مرتبط

<!-- Tier A · CONNECTIONS-MAP (_memory) · اعمال 2026-07-04 -->
- [[06 - Architecture Maps/ECOSYSTEM|ECOSYSTEM]]
