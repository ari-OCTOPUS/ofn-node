---
type: control
project: "[[03 - Projects/اونلی فنز/PROJECT]]"
status: active
created: 2026-07-12
updated: 2026-07-12
created_by: agent
sources:
  - "[[00 - Control/CARTOGRAPHY-2026-07-12|CARTOGRAPHY-2026-07-12]]"
  - "[[BASE-DATA-REPORT-2026-07-12]]"
tags: [project-f, source-of-truth, control]
aliases: ["Project-F SoT Matrix"]
---

# SOURCE-OF-TRUTH MATRIX — Project-F

> **حکم (تأیید مالک 2026-07-12): ریشهٔ پروژه canonical است؛ `docs/` و `research/` آینه‌های stale هستند.**
> مبنا: md5 دقیق + شواهد encoding + annotation خود INDEX («UTF-8 سالم»).

## ۱. فایل‌های تک‌نسخه (canonical بی‌رقیب)

| موضوع | فایل canonical |
|---|---|
| وضعیت زنده | `PROJECT.md` (Active Context) |
| قرارداد کنترل ماشین‌خوان | `PROJECT-F-CONTROL-MANIFEST.json` 🏆 |
| منشور کاری | `CLAUDE.md` |
| تصمیم‌ها | `DecisionLog.md` |
| سؤال‌های باز | `OpenQuestions.md` |
| صف verdict | `VERDICT_QUEUE.md` + `THREAD-CLOSURE-D-2026-07-10.md §۹` |
| ناوبری | `INDEX.md` (curated) · `HOME.md` (dashboard — ⚠ Dataview نصب نیست) |
| حافظه | `_memory/onlyfans-project-memory-2026-07-05.md` |
| جذب (کانونی) | `ACQUISITION-ENGINE-2026-07-05.md` (نسخهٔ root) |

## ۲. دوبله‌ها — کدام برنده است

| فایل | canonical | نسخهٔ retire‌شدنی | نوع تفاوت |
|---|---|---|---|
| PROJECT-F-BRAIN-SPEC.md | root | docs/ | byte-identical → `_Duplicates` |
| PROJECT-F-FULL-REPORT-2026-07-09.md | root | docs/ | byte-identical → `_Duplicates` |
| TELEGRAM-CONTENT-STUDIO-v1.md | root (تاریخی؛ v2 حاکم) | docs/ | byte-identical → `_Duplicates` |
| TELEGRAM-CONTENT-STUDIO-v2.md | root | docs/ | byte-identical → `_Duplicates` |
| ACQUISITION-ENGINE-2026-07-05.md | root | research/ | byte-identical → `_Duplicates` |
| COMPLIANT-PLAYBOOK-M3-2026-07-10.md | root | research/ | byte-identical → `_Duplicates` |
| DECISION-MATRIX-M2-2026-07-10.md | root | research/ | byte-identical → `_Duplicates` |
| DECISIONLOG-ENTRIES-M4-2026-07-10.md | root | research/ | byte-identical → `_Duplicates` |
| PROMPTS-2026-07-05.md | root | research/ | byte-identical → `_Duplicates` |
| RESEARCH-INTEGRATION-round1.md | root | research/ | byte-identical → `_Duplicates` |
| RESEARCH-INTEGRATION-round2-2026-07-10.md | root | research/ | byte-identical → `_Duplicates` |
| STATE-REPORT-2026-07-05.md | root | research/ | byte-identical → `_Duplicates` |
| THREAD-CLOSURE-D-2026-07-10.md | root | research/ | byte-identical → `_Duplicates` |
| MASTER-BUILD-2026-07-04.md | **root** | docs/ | متفاوت (docs کهنه/mojibake) → `09 - Archive` |
| Feet-Content-Business-Master-Playbook.md | **root** | docs/ | متفاوت → `09 - Archive` |
| MONETIZATION-EXPANSION-2026-07-04.md | **root** | docs/ | متفاوت → `09 - Archive` |
| architecture-blueprint-2026-07-04.md | **root** («UTF-8 سالم») | docs/ | متفاوت → `09 - Archive` |
| Fable5-Build-Spec.md | **root** | docs/ | متفاوت → `09 - Archive` |
| Content-Topics-Trends-2027.md | **root** | docs/ | متفاوت → `09 - Archive` |
| 30-Faceless-Clips-ReadyToFilm.md | **root** | docs/ | متفاوت → `09 - Archive` |
| research-prompts-lead-generation.md | **root** | research/ | فقط encoding → `09 - Archive` |
| research-track-BC-2026-07-04.md | **root** | research/ | فقط encoding → `09 - Archive` |

## ۳. کد — نسخهٔ جاری در برابر منسوخ

| جاری (canonical) | منسوخ/مرده | شاهد |
|---|---|---|
| `brain/dual_brain_v3.py` | `brain/dual_brain.py` | orchestrator/langar فقط v3 را import می‌کنند |
| `studio/saba_studio.py` | `studio/studio_telegram.py`، `studio_telegram_v3.py` | فقط saba_studio ‏`__main__` دارد؛ spec §۶ |
| — | `brain/project_f_brain.py` (**spec-canonical ولی runtime-dead**) | هیچ‌جا instantiate نمی‌شود |
| `studio/drafts.json` (پس از reset) | `studio/drafts.json.bak` (۶۰۸ ردیف تست) | آلودگی fixture |

## ۴. تعارض‌های استراتژیک هنوز-باز (تصمیم مالک، نه فایل)

MASTER-BUILD ↔ Playbook (سند master) · نردبان قیمت (۳ نسخه؛ EXT-04 مرجح) · برند (Anar Soles پیشنهادی) · Fansly (mirror مرجح) · «Persian/Sydney» در کپی (#۹). تا verdict، **هیچ سندی سند دیگر را overwrite نکند** — فقط reconcile-note.
