---
type: dashboard
project: "[[PROJECT]]"
aliases: ["Project-F HOME", "خانه پروژه", "داشبورد اونلی فنز", "Project-F Dashboard"]
tags: [project-f, dashboard, moc, home]
cssclasses: [dashboard, wide-page]
up: "[[PROJECT]]"
status: active
updated: 2026-07-10
---

# 🎛 Project-F — HOME (داشبورد زنده)

> نقطهٔ ورودِ vault. برای نقشهٔ curated: [[INDEX]] · منشور: [[CLAUDE]] · وضعیت: [[PROJECT]] · کنترلِ ایجنتِ مادر: [[AGENT-CONTROL-INTERFACE]] + `PROJECT-F-CONTROL-MANIFEST.json`.
> بلاک‌های `dataview` نیازِ افزونهٔ **Dataview** دارند؛ اگر نصب نیست، لینک‌های استاتیکِ زیرِ هر بخش کار می‌کنند.

> [!warning] بلاکرِ فعال — GATE 0
> محل اقامتِ Creator ثبت نشده → Branch A/B نامشخص. **هیچ اکشنِ بیرونی تا حل نشدنش اجرا نمی‌شود.** فاز: **validation** · اجرا: **صفر**. صفِ تصمیم: [[THREAD-CLOSURE-D-2026-07-10#§۹ — منتظر verdict تو|۱۱ verdict منتظر]].

---

## 🧭 مسیرِ لودِ اجباری (طبق [[CLAUDE|منشور]])
۱) [[onlyfans-project-memory-2026-07-05|حافظهٔ فشرده]] → ۲) [[STATE-REPORT-2026-07-05|گزارش وضعیت]] → ۳) [[CLAUDE|منشور]] → ۴) [[PROJECT|Active Context]] → مرجعِ جذب: [[ACQUISITION-ENGINE-2026-07-05]].

---

## 🔴 تصمیم‌های باز (Open Questions)
```dataview
TABLE WITHOUT ID file.link AS "سند", status
FROM "03 - Projects/اونلی فنز"
WHERE type = "knowledge" OR file.name = "OpenQuestions"
```
استاتیک: [[OpenQuestions]] · [[THREAD-CLOSURE-D-2026-07-10]] (§۹ verdictها).

---

## 🆕 آخرین به‌روزرسانی‌ها
```dataview
TABLE WITHOUT ID file.link AS "سند", type AS "نوع", updated AS "تاریخ"
FROM "03 - Projects/اونلی فنز"
WHERE updated
SORT updated DESC
LIMIT 12
```

---

## 🏗 معماریِ سیستم (سه لایه + کنترل)
```
                    ┌─────────── ایجنتِ مادر (Architect) ───────────┐
                    │  رصد + صف‌بندیِ verdict + قطعِ اضطراری          │
                    │  قرارداد: PROJECT-F-CONTROL-MANIFEST.json      │
                    └───────────────────┬───────────────────────────┘
   🎬 Creator (استودیو)  ──►  🧠 مغز (brain/)  ──►  ⚓ Operator (لنگر)
   saba_studio.py            control-plane+۷عامل      langar_bot.py
   درفت/تقویم/ظرفیت          +دو Guard+یادگیرنده       status/verdict/kill
        └──── drafts.json · to_ari.json · for_saba.json · HALT ────┘
```
اسناد: [[SABA-STUDIO-SPEC]] · [[PROJECT-F-BRAIN-SPEC]] · [[BRAIN-BENCHMARK-2026-07-10]] · [[LANGAR-SPEC]] · [[AGENT-CONTROL-INTERFACE]].

---

## 📄 اسناد بر اساس نوع

### استراتژی و ساخت
```dataview
LIST
FROM "03 - Projects/اونلی فنز"
WHERE type = "operating-system" OR type = "playbook" OR contains(file.name, "MASTER-BUILD") OR contains(file.name, "architecture-blueprint") OR contains(file.name, "MONETIZATION")
```
استاتیک: [[MASTER-BUILD-2026-07-04]] · [[Feet-Content-Business-Master-Playbook]] · [[architecture-blueprint-2026-07-04]] · [[MONETIZATION-EXPANSION-2026-07-04]] · [[ACQUISITION-ENGINE-2026-07-05]].

### تصمیم و پلن (۱۰ جولای)
```dataview
LIST
FROM "03 - Projects/اونلی فنز"
WHERE type = "decision-matrix" OR type = "playbook" OR type = "decision-entries" OR type = "thread-closure"
```
استاتیک: [[DECISION-MATRIX-M2-2026-07-10]] · [[COMPLIANT-PLAYBOOK-M3-2026-07-10]] · [[DECISIONLOG-ENTRIES-M4-2026-07-10]] · [[THREAD-CLOSURE-D-2026-07-10]].

### تحقیق (corpus)
```dataview
TABLE WITHOUT ID file.link AS "گزارش"
FROM "03 - Projects/اونلی فنز/research-results" OR "03 - Projects/اونلی فنز/external-research-2026-07-05"
SORT file.name ASC
```
استاتیک (round): [[RESEARCH-INTEGRATION-round1]] · [[RESEARCH-INTEGRATION-round2-2026-07-10]].

### کد و اسپک (مغز/بات‌ها)
```dataview
LIST
FROM "03 - Projects/اونلی فنز"
WHERE type = "spec" OR type = "benchmark" OR contains(file.name, "BRAIN") OR contains(file.name, "LANGAR") OR contains(file.name, "SABA")
```
استاتیک: [[PROJECT-F-BRAIN-SPEC]] · [[BRAIN-BENCHMARK-2026-07-10]] · [[LANGAR-SPEC]] · [[SABA-STUDIO-SPEC]] · [[README-RUNBOOK|Langar Runbook]] · [[README-SABA-RUNBOOK|Saba Runbook]].

### محتوا و ops
استاتیک: [[30-Faceless-Clips-ReadyToFilm]] · [[Content-Topics-Trends-2027]] · [[Fable5-Build-Spec]] · [[DecisionLog]] · [[OpenQuestions]] · [[پرسشنامه پارتنر - پاسخ‌های صبا]].

---

## 🎛 کنترلِ عملیاتی (kill-switch و بودجه)
| کنترل | ماشه | اثر |
|---|---|---|
| کاکپیت | `/kill` یا فایلِ `langar/KILL` | جز /status,/revive رد |
| مرزِ Creator (مقدم) | `/halt` یا `studio/HALT` | استودیو halt + اعلانِ Operator |
| بودجه | ابزار A$100 · LLM A$15 · مغز ۲٪ | fail-closed |
| اخطارِ پلتفرم | هر اخطار | توقفِ فوری + ثبت در [[DecisionLog]] |

اجرا/تست: `python3 -m unittest` در `brain/` (۱۱) · `langar/` (۸) · `studio/` (۱۰).

---

## 🔗 گرافِ گیت‌ها
`G0 (باز، بلاکر) → G1 (هفتهٔ۶: ۲۰۰کلیک/۱۰٪/۸۰٪) → G2 (هفتهٔ۱۲: ۳۰sub/۵٪/A$100) → G3 (A$2k×۳→ABN) → G4 (۱۲ماه سود→Tools)`

---
> این داشبورد صفر-PII است (کدِ A/C). خارج از پوشه فقط «Project-F».
