---
type: log
project: "[[03 - Projects/اونلی فنز/PROJECT]]"
status: active
tags: [project-f, kpi, ops]
created: 2026-07-14
updated: 2026-07-14
created_by: agent
---

# 🔁 لاگِ حلقهٔ جمعه (KPI + بهداشت فنی)

> پرشونده توسط تسکِ `pf-friday-kpi-loop` (جمعه‌ها ~۱۷:۰۰). هر بخش: نتیجهٔ validatorها + سوییت تست (سندباکسِ tmp) + وضعیت داشبورد + درفتِ یکشنبه.

## 2026-07-14 — run صفر (دستی، seed — دوشنبه)
- **سوییت تستِ درختِ زنده (pre-merge):** ‏`test_learning` ‏۱۱/۱۱ + ‏pytest (pipeline/langar/pf_admin/affirm/saba_studio) ‏**۴۱/۴۱** = ۵۲ سبز. state فقط در tmp ‏(PF_BRAIN_DIR/PF_STUDIO_DIR).
- **نکته:** سوییتِ کاملِ ۷۲تایی (شامل copy_bank/test_acquisition/test_pipeline_bank) بعد از merge شاخهٔ `claude/project-analysis-planning-4b34df` روی درخت زنده قابل‌اجراست — merge فعلاً پشتِ `index.lock` قدیمی (07-12) در `.git` است؛ پاک‌کردنش دستِ مالک.
- **validator ‏frontmatter:** ‏۵۰ خطای pre-existing در پوشهٔ Project-F (baseline — تفکیک در [[03 - Projects/اونلی فنز/06 - Ops & Runtime/AGENT-CHORES-LOG|AGENT-CHORES-LOG]]).
- **داشبورد KPI:** ساخته شد (هفتهٔ صفر) → [[03 - Projects/اونلی فنز/06 - Ops & Runtime/KPI-DASHBOARD|KPI-DASHBOARD]].
- **درفتِ یکشنبه:** آماده → [[03 - Projects/اونلی فنز/06 - Ops & Runtime/SUNDAY-REPORT-DRAFTS|SUNDAY-REPORT-DRAFTS]] (ارسال دستِ انسان).
