---
type: moc
project: "[[03 - Projects/اونلی فنز/PROJECT]]"
status: active
tags: [creator-business, faceless, moc, project-f]
aliases: ["MOC", "نقشه پروژه", "Project-F Index"]
created: 2026-07-04
updated: 2026-07-24
---

# INDEX — MOC پروژه اونلی فنز (Project-F)

> کیت مغز پروژه ([[_memory/LIVING-BRAIN-BLUEPRINT|بلوپرینت]]) — 2026-07-04. خارج از این پوشه فقط کد «Project-F».
> 🏠 **داشبورد زندهٔ Obsidian:** [[HOME]] (Dataview + kill-switch + معماری). این INDEX نقشهٔ curated است؛ HOME نمای زنده.
> 📐 **بازآرایی ۲۰۲۶-۰۷-۲۴:** اسناد پراکندهٔ ریشه به پوشه‌های شماره‌دار (۰۱–۰۹) منتقل شدند؛ آینه‌های کهنهٔ  و  حذف؛ کدِ منسوخ / (v1) به  رفت. فایل‌های code-coupled (PROJECT/OpenQuestions/DecisionLog/THREAD-CLOSURE/CLAUDE/ACQUISITION/STATE-REPORT/MANIFEST/orchestrator) **در ریشه ماندند** چون کد پایتون با مسیر نسبی آن‌ها را می‌خواند. مسیرها در  مانیفست به‌روز شدند. جزئیات: [[00 - Control/REORG-LOG-2026-07-24|REORG-LOG]]. از آنجا که Obsidian بر اساس *نام فایل* لینک‌ها را حل می‌کند، wikilinkها بدون تغییر کار می‌کنند.

> 🆕 **۲۰۲۴-۰۷-۲۴:** ساختار Obsidian بازآرایی شد + pf_os کامل شد (۲۵ فایل، ۱۱۹ تست). اول [[00 - Control/HANDOFF-NEXT-AGENT-2026-07-24-REORG|HANDOFF ایجنت بعدی]] را بخوان. ردِّ تغییرات: [[00 - Control/REORG-LOG-2026-07-24|REORG-LOG]].

## 🎛 کنترلِ ایجنتِ مادر (اول این را بخوان — cross-domain)
- **`PROJECT-F-CONTROL-MANIFEST.json`** — 🆕 **07-10:** قراردادِ ماشین‌خوانِ کنترل (صفر-PII، کدِ A/C): identity، status، gates، قواعد قفل‌شده، capabilities، سطحِ کنترل (دستورها/فایل‌ها/handoffها)، kill-switchها، entrypointها، صفِ verdict. **single-source برای ایجنتِ مدیریتِ همهٔ پروژه‌ها.**
- [[AGENT-CONTROL-INTERFACE]] — روایتِ همان: چه ساخته شده، ایجنتِ مادر چه می‌تواند/نمی‌تواند (رصد+صف+قطع؛ اجرا هرگز)، پروتکلِ تشدید.

## وضعیت و حافظه (جدید)
- [[HOME]] — 🆕 **07-10:** داشبورد زندهٔ Obsidian (Dataview + معماری + kill-switch + گیت‌ها).
- [[brain/BRAIN-BENCHMARK-2026-07-10|BRAIN-BENCHMARK]] — 🆕 **07-10:** راستی‌آزماییِ مغزِ یادگیرنده + بنچمارک با معماریِ مولتی‌ایجنتِ رقبا ۲۰۲۶ + تقویت: ضعفِ greedy رفع → `brain/learning.py` (ThompsonBandit + UCB1 + recency + eval، ۴۹٪/۳۳٪ بهتر، ۱۰/۱۰ تست).
- [[studio/SABA-STUDIO-SPEC|SABA-STUDIO-SPEC]] — 🆕 **07-10:** رابط تلگرامیِ جدای صبا (`studio/saba_studio.py`) روی موتور ContentStudio؛ boundary-first، propose-only، صفر رسانه؛ سیم‌کشیِ دوطرفه با لنگر؛ ۱۰/۱۰ تست. Runbook: [[studio/README-SABA-RUNBOOK|Saba Runbook]].
- [[THREAD-CLOSURE-D-2026-07-10|THREAD-CLOSURE-D]] + [[langar/LANGAR-SPEC|LANGAR-SPEC]] — 🆕 **07-10 (PROMPT D + لنگر):** بستن T1–T8 + ۵ درفت در `drafts-awaiting-gate/` + کاکپیت «لنگر» (خودآگاه، propose-only، ۸/۸ تست). ساعت صبا بسته (~۳h).
- [[DECISION-MATRIX-M2-2026-07-10|DECISION-MATRIX-M2]] + [[COMPLIANT-PLAYBOOK-M3-2026-07-10|COMPLIANT-PLAYBOOK-M3]] + [[DECISIONLOG-ENTRIES-M4-2026-07-10|M4-entries]] — 🆕 **07-10:** زنجیرهٔ M2→M3→M4: ماتریس ban-risk-weighted · پلن ۲۴-گامی compliant-only · ۶ ورودی DecisionLog.
- [[RESEARCH-INTEGRATION-round2-2026-07-10|RESEARCH-INTEGRATION-round2]] — 🆕 **07-10:** تحقیق جامع ۷-محوره (WS-1..7): R4 گذار مالکیتی OF · AU under-16 live · کاتالوگ ۵۸-روشی · unit-economics · spec مغز · roadmap ۳۰/۶۰/۹۰ · #۱۷–۲۰.
- [[RESEARCH-INTEGRATION-round1|RESEARCH-INTEGRATION-round1]] — **07-06:** delta-map Round 1؛ REJECT تلگرام/کریپتو؛ ممنوعیت AI-chat در ToS OF.
- [[STATE-REPORT-2026-07-05|STATE-REPORT-2026-07-05]] — گزارش جامع وضعیت (نقشه دانش، تناقض‌ها).
- [[_memory/onlyfans-project-memory-2026-07-05|memory-synthesis]] — سنتز فشرده حافظه بلندمدت (اول این را لود کن).
- [[PROMPTS-2026-07-05|PROMPTS-2026-07-05]] — سه پرامپت ماموریت Cowork.

## هسته
- [[ACQUISITION-ENGINE-2026-07-05|ACQUISITION-ENGINE]] — ⭐ **مرجع کانونی جذب مشتری**: قیف ۵لایه + استک/هزینه + KPI + نقشه ۹۰روزه.
- [[PROJECT|PROJECT]] — شناسنامه + Active Context · [[CLAUDE|منشور کاری]] — operating charter.
- [[DecisionLog|DecisionLog]] · [[OpenQuestions|OpenQuestions]]
- [[project-master-reference|project-master-reference]] · [[اونلی فنز|لاگ تلگرام]]

## کد و اسپکِ سیستم (مغز/بات‌ها)
- [[PROJECT-F-BRAIN-SPEC|PROJECT-F-BRAIN-SPEC]] · [[brain/BRAIN-BENCHMARK-2026-07-10|BRAIN-BENCHMARK]] — `brain/` (project_f_brain، acquisition، learning، ab_tracker، dual_brain_v3، orchestrator)
- [[langar/LANGAR-SPEC|LANGAR-SPEC]] · [[langar/README-RUNBOOK|Langar Runbook]] — کاکپیت Operator
- [[studio/SABA-STUDIO-SPEC|SABA-STUDIO-SPEC]] · [[studio/README-SABA-RUNBOOK|Saba Runbook]] — استودیو Creator
- [[PROJECT-F-FULL-REPORT-2026-07-09|FULL-REPORT (07-09)]]

## تحقیق — corpus کامل (P1–P13)
- [[research-results/00-executive-summary|00 خلاصهٔ اجرایی]]
- [[research-results/P1-channel-map|P1 channel-map]] · [[research-results/P2-x-growth-engine|P2 X-growth]] · [[research-results/P3-reddit-engine|P3 Reddit]] · [[research-results/P4-persona-hooks|P4 persona]] · [[research-results/P5-funnel-geoblock|P5 funnel/geo]]
- [[research-results/P6-owned-audience|P6 owned]] · [[research-results/P7-dm-automation|P7 DM]] · [[research-results/P8-s4s-network|P8 S4S]] · [[research-results/P9-repurposing-pipeline|P9 repurposing]] · [[research-results/P10-analytics-experiment-loop|P10 analytics]]
- [[research-results/11-fresh-scan-2026-07-04|11 fresh-scan]] · [[research-results/12-prelaunch-verification-2026-07-05|12 prelaunch]] · [[research-results/13-external-ai-research-integration-2026-07-05|13 external-integration]]
- external: [[external-research-2026-07-05/01-reddit-growth-plan|01 Reddit]] · [[external-research-2026-07-05/02-x-playbook|02 X]] · [[external-research-2026-07-05/03-content-engine|03 Content]] · [[external-research-2026-07-05/04-onlyfans-funnel|04 OF-funnel]] · [[external-research-2026-07-05/06-opsec-legal|06 OpSec]] · [[external-research-2026-07-05/marketing-automation-100-topics-2026|100-topics]]
- [[research-track-BC-2026-07-04|research-track-BC]] · [[research-prompts-lead-generation|research-prompts]]

## validation، محتوا، consent
- [[پرسشنامه پارتنر - پاسخ‌های صبا|پرسشنامه پارتنر — پاسخ‌ها]]
- [[Content-Topics-Trends-2027|Content-Topics-Trends-2027]] · [[30-Faceless-Clips-ReadyToFilm|30-Faceless-Clips]]

## ساخت و استراتژی
- [[MASTER-BUILD-2026-07-04|MASTER-BUILD]] · [[Feet-Content-Business-Master-Playbook|Feet playbook]] · [[architecture-blueprint-2026-07-04|architecture-blueprint]] (UTF-8 سالم)
- [[MONETIZATION-EXPANSION-2026-07-04|MONETIZATION-EXPANSION]] · [[Fable5-Build-Spec|Fable5-Build-Spec]] · [[Knowledge_Base_Memory_Synthesis|Knowledge_Base]]

## درفت‌های منتظر گیت
- [[drafts-awaiting-gate/link-hub-copy|link-hub]] · [[drafts-awaiting-gate/x-profile|x-profile]] · [[drafts-awaiting-gate/tracking-link-design|tracking-links]] · [[drafts-awaiting-gate/ppv-ladder|ppv-ladder]] · [[drafts-awaiting-gate/kpi-dashboard-spec|kpi-spec]]

## خارج از scope
- `_inbox-other-projects/` — Ziman DM Bot · self-improvement-root-map (شخصی)
