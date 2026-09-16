---
type: control
project: "[[03 - Projects/اونلی فنز/PROJECT]]"
status: active
created: 2026-07-12
updated: 2026-07-12
created_by: agent
sources:
  - "[[CLAUDE]]"
  - "[[RESEARCH-INTEGRATION-round2-2026-07-10]]"
tags: [project-f, risk, control]
aliases: ["Project-F Risk Ladder"]
---

# RISK-LADDER — Project-F

> فایل غایبی که `RUNBOOK.md` به آن ارجاع می‌داد؛ سنتز از منشور (CLAUDE.md §۱–۲) + MANIFEST + Round2 §۷. **قواعد قفل‌شده بر همهٔ سطوح حاکم‌اند.**

## 🟢 GREEN — خودمختار (برگشت‌پذیر، درون‌پوشه)
read · classify · analyse · research (وب فقط‌خواندنی) · draft · offline test · memory-candidate · propose · گزارش status محتوا-آزاد

## 🟡 YELLOW — propose + log (مالک مرور می‌کند)
پیشنهاد سند governance-برخورد · prompt candidate · schema candidate · درفت آزمایش · درفت داشبورد · پیشنهاد registry

## 🟠 ORANGE — verdict انسانی لازم
**جابه‌جایی/مهاجرت فایل** (PF-STRUCT) · reset هر state ران‌تایم (drafts.json) · آماده‌سازی فعال‌سازی تلگرام · تعویض provider/مدل · فعال‌سازی prompt · پیشنهاد قیمت · live-prep

## 🔴 RED — فقط انسان (master نمی‌تواند self-approve کند؛ تا GATE 0 + Security Gate قفل)
ساخت اکانت · publish/پست · ارسال DM · پرداخت/برداشت · login پلتفرم · echo هویت/محتوا بیرون پوشه · تغییر قاعدهٔ قفل‌شده · **اجرای کد** (حتی تست تا اجازهٔ sandbox) · فعال‌سازی بات (BotFather)

## Kill-switchها (پیاده‌شده در کد — تأیید 2026-07-12)
`langar/KILL` (/kill) · `studio/HALT` (/halt، مرز C حاکم) · CostMeter fail-closed (سقف AUD 15/ماه LLM) · platform-warning → توقف اتوماسیون + ثبت DecisionLog

## قاعدهٔ تشدید
تضاد با قاعدهٔ قفل‌شده → اجرا نکن، با تگ «⚑ برای معمار» flag کن + جایگزین امن پیشنهاد بده.
