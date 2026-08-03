# Brushline — Theory Project (README)

> سیستمِ چندایجنتیِ marketing/lead-gen برای نقاشیِ ساختمانِ سیدنی. این bundle = **کلِ لایهٔ تئوری** (بدونِ کد). نقطهٔ شروع برای کدنویسی (فاز ۰).

## از کجا شروع کنم؟
۱. **`00_governance/PROJECT_MANIFEST.md`** — فهرستِ کامل + گیتِ آمادگیِ پیش‌از‌کد. اول این.
۲. **`00_governance/BLUEPRINT.md`** — معماری و تصمیم‌های قفل.
۳. **`00_governance/ROADMAP.md`** — فازها + DoD.
۴. **`10_knowledge_base/KB-00_master_synthesis.md`** — نقشهٔ متصلِ همهٔ ماژول‌ها.

## ساختار (به‌روز — لایهٔ عملیاتی + رابطِ تلگرام اضافه شد)
```
00_governance/   PROJECT_OVERVIEW, MASTER_INSTRUCTIONS, PROJECT_MANIFEST, BLUEPRINT, ROADMAP, CLAUDE_PROJECT_SETUP, GLOSSARY, CONFIG_parameters
10_knowledge_base/ KB-00 … KB-14   (سیستمِ AI + بازار + انطباقِ داده/پیام)
20_specs/        MVP_system_requirements, THREAT_MODEL
30_process/      BRUSHLINE_theory_completion_prompt, CONSISTENCY_REPORT, DEEP_RESEARCH_PROMPT
40_operations/   OPS-00 … OPS-09   ← جدید: عملیاتِ واقعیِ نقاشی (quote/SOP/sales/marketing/CRM/compliance)
50_interface/    TG-01             ← جدید: ربات تلگرام = تنها درگاهِ Operator (تئوری، بدون کد)
90_reference/    fusion checklist (+ LANGAR refs وقتی آپلود شد)
99_archive/      نسخه‌های PDF + zip + DEDUP_NOTE (تکراری‌ها حل شد)
```

> **تغییرِ این نسخه:** ساختار مرتب و یکدست شد؛ تکراری‌ها (ROADMAP v2، KB-12 قدیمی) بایگانی شدند؛ آن ۲۰٪ گم‌شده (لایهٔ عملیاتیِ نقاشی) در `40_operations/` اضافه شد؛ تلگرام به‌عنوان تنها درگاه در `50_interface/`. هیچ کدی نوشته نشد.

## سه Invariant (روحِ پروژه)
- **INV-1** هیچ publish/spend/پیام بدونِ human approval.
- **INV-2** PII/مالی هرگز در LANGAR/memory؛ داده در AU.
- **INV-3** auto-execution = kill switch + spend cap + hash-chained audit.

## وضعیت
لایهٔ تئوری **کامل و سازگار** (۲۱ سندِ markdown). تنها بازماندهٔ پیش‌از‌کد = ورودیِ Operator:
- CONFIG: `fx_aud_usd`، Google Places per-request، `spam_penalty_units` (verify).
- KB-02: `avg_margin_per_job`، `enquiry→quote`، `quote→job`.

با بسته‌شدنِ این‌ها → شروعِ **فاز ۰ (scaffold/reuse)**.

## مباحثی که تحقیقِ عمیق‌تر می‌خواهند
به `30_process/DEEP_RESEARCH_PROMPT.md` مراجعه کن (حقوقِ AU، APIهای واقعی، دادهٔ بازارِ محلی، LANGAR، go-to-market).

## قاعده‌ها
نام‌ها فقط از GLOSSARY؛ پارامترها فقط از CONFIG؛ همه‌چیز Markdown + Mermaid، بدونِ کد تا فاز ۰.
