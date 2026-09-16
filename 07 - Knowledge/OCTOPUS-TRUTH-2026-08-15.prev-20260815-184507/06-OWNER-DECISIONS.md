---
title: تصمیمات قفل‌شدهٔ مالک
type: decision-log
tags: [octopus, decisions, governance]
up: "[[00-INDEX]]"
signed_at: 2026-08-15
recorded_in: PHASE-1-DECISIONS.md
commit: dc5839d
---

# تصمیمات مالک — ۱۵ اوت ۲۰۲۶

## NBB-V1 — نقش NBB-CP نسبت به Architect و `_ops`

**حکم: A**

NBB-CP **حاکم** است، بالای شش پا.

| حق | دارد؟ |
|---|---|
| متوقف کردن یک پا (`stop`) | ✅ |
| رد کردن proposal | ✅ |
| **پیشنهاد** بودجه | ✅ |
| **اجرای** بودجه | ❌ |

حل تناقض با Architect:

- تناقض **عملیاتی** → NBB-CP تصمیم می‌گیرد
- تناقض **معماری** → Architect تصمیم می‌گیرد

## ADR-037 — موتور فرضیه

**حکم: A** — پذیرفته با قید:

- adapter خاموش
- `CORTEX_HYPOTHESIS=0`
- `evidence_level: C`

دلیل قید: نتیجهٔ ارزیابی «not superior to novelty» بود. پذیرش سند، نه فعال‌سازی
قابلیت.

## USGS

**پذیرش موقت** با `needs_formal_allowlist: true`. باید در allowlist v2 با شاهد
robots رسمی شود.

## `deceptive_grid.py`

ویرایش commit‌نشده‌ای که ۳۶۴ خط و از جمله `falsified_assists_at` را حذف کرده
بود → **بازگردانی** با `git checkout --`.

این ویرایش ریشهٔ تناقض C-003 بود. به [[07-CONTRADICTIONS]] برو.

## ADR-041 / ADR-037

از پروژهٔ پرپلکسیتی به `F:\backup\03 - Projects\research-spec-compiler\adr\`
کپی شود.
