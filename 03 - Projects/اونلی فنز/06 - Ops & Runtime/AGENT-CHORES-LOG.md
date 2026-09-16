---
type: log
project: "[[03 - Projects/اونلی فنز/PROJECT]]"
status: active
tags: [project-f, chores, ops]
created: 2026-07-14
updated: 2026-07-14
created_by: agent
---

# 🧹 لاگِ کارهای چهارشنبه (صفِ بی‌گیتِ ایجنت)

> پرشونده توسط تسکِ `pf-agent-chores` (چهارشنبه‌ها ~۱۰:۰۰). هر اجرا دقیقاً یک آیتم.

## صف
1. ⏳ پاکسازیِ مکانیکیِ frontmatter نوت‌های پروژه (تحلیل انجام شد — اجرای ویرایش بعد از رفعِ index.lock، چون batch >۵ فایل نیازمند agent-checkpoint است)
2. ⬜ تعریفِ تستِ قراردادِ پروژه (`brain/test_contract.py`)
3. ⬜ راستی‌آزمایی Q12 (وزن‌های ادعایی الگوریتم X)
4. ⬜ حالتِ پایدار: بهداشتِ هفتگی (validatorها + سازگاری VERDICT_QUEUE↔PROJECT.md)

## 2026-07-14 — آیتم ۱، فازِ تحلیل (دستی، seed)
**۵۰ خطای frontmatter در پوشهٔ Project-F** (validator زنده). تفکیک و برنامه:

**الف) فیکسِ مکانیکیِ بی‌ابهام (~۱۴ فایل — آمادهٔ اجرا بعد از بازشدنِ git):**
- ۷× `updated:` غایب → از `created:`/mtime پر می‌شود.
- ۳× `status: draft-for-build` → `draft` · ۲× `complete` → `done` · ۲× `proposal (awaiting human verdict)` → `idea`.

**ب) نیازمند تصمیم مالک (فقط پیشنهاد — اعمال نمی‌شود):**
- ۴ فایل کلاً بدون فرانت‌متر (از جمله VERDICT_QUEUE.md — عمداً جدول خام است؟).
- ۱× `status` غایب · کلیدهای خارج از schema (حذف نمی‌کنیم): `relates_to`×۵، `input`×۲، `up`، `scope`، `round`×۲، `reader`، `public_alias`، `parent_report`، `audience`، `machine_contract`.
- typeهای محلیِ بستهٔ سند (تغییر نمی‌دهیم مگر با رأی): `research-integration`×۲، `thread-closure`، `state-report`، `prompts`، و مشابه‌ها. پیشنهادِ نگاشت: همه → `report` یا افزودنِ این واژگان به Property Schema به‌عنوان typeهای مجازِ بستهٔ Project-F (تصمیمِ schema = فقط مالک، طبق قانون §۶).
