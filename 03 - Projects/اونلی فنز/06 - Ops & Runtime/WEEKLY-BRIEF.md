---
type: log
project: "[[03 - Projects/اونلی فنز/PROJECT]]"
status: active
tags: [project-f, brief]
created: 2026-07-14
updated: 2026-07-14
created_by: agent
---

# 📣 بریفِ هفتگی — Project-F

> پرشونده توسط تسکِ `pf-monday-brief` (دوشنبه‌ها ~۰۸:۳۰).

## 2026-07-14 — بریفِ نخست (seed، دستی)

**🚦 گیت‌ها:** GATE 0 **باز** (خط اقامت پارتنر خالی) · Security Gate: تناقضِ سندی → verdict ‏PF-SECGATE-V1 · ⚠️ merge شاخهٔ stage-5 پشتِ `index.lock` قدیمی (07-12) در `.git` — پاک‌کردن دستِ مالک.

**🗳 verdictهای باز:** بستهٔ ۱۹تاییِ تصمیم ([[03 - Projects/اونلی فنز/00 - Control/MASTER-SCHEDULE-2026-07-14|MASTER-SCHEDULE §۱]] — روی شاخه تا merge) — شامل G0، ‏۱۱ ردیفِ THREAD-CLOSURE، ‏PF-STRUCT-V2، ‏PF-STATE-RESET-V1، ‏PF-CODE-REFACTOR-V1، ‏PF-LEARN-WIRE-V1، ‏PF-SECGATE-V1، ‏D1، ‏merge. یادآورِ یک‌بارهٔ فردا صبح (07-15 ‏۰۹:۰۰) چک‌لیست را می‌آورد.

**📋 این هفته:** تو = بستهٔ تصمیم (~۹۰ دقیقه) + پاکِ `index.lock` · C = (پس از G0) پاسخ اقامت + توافق §۴.۱ · ایجنت = روتین‌های زمان‌بندی‌شده (سایهٔ لنگر روزانه، چهارشنبه chores، جمعه KPI).

**🔄 امروز انجام شد (run صفرِ دستیِ همهٔ روتین‌ها):** سوییت زندهٔ pre-merge ‏۵۲/۵۲ سبز · لنگر روزِ ۱ PASS ‏([[03 - Projects/اونلی فنز/06 - Ops & Runtime/LANGAR-SHADOW-LOG|لاگ]]) · داشبورد KPI هفتهٔ صفر ساخته شد · درفتِ گزارشِ یکشنبه آماده (ارسال دستِ تو) · تحلیلِ ۵۰ خطای frontmatter ‏([[03 - Projects/اونلی فنز/06 - Ops & Runtime/AGENT-CHORES-LOG|صف]]).

**⚠️ فوری:** (۱) `index.lock` — تا پاک نشود هیچ commit/merge روی درخت زنده ممکن نیست؛ (۲) فلگ‌ها (PF_LEARNING_WIRED/PF_LIVE_*) عمداً خاموش‌اند تا رأی.
