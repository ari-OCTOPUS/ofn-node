---
type: project
kind: project
project: "[[03 - Projects/اونلی فنز/PROJECT]]"
status: active
owner: آری
risk_level: high
autonomy_level: read-only
tags: [creator-business, faceless]
created: 2026-07-03
updated: 2026-07-06
---

# پروژه: اونلی فنز

> 🏗️ **رکنِ ساخت:** [[04 - Architect System/MYCELIAL-MASTER-SPEC|MYCELIAL-MASTER-SPEC]] — این پروژه یک node در §۳ رجیستریِ اتصال است (build/test/delete پشتِ verdict).

**وضعیت:** creator brand با مدل faceless (فقط پا در فاز فعلی) — تیم دونفره ۵۰/۵۰، فاز validation. سند کامل: [[03 - Projects/اونلی فنز/project-master-reference|master-reference]].

**نقش در اکوسیستم:** درآمد آزمایشی؛ زیر نظارت architect (رئیس کل). کد ارجاع در خروجی‌های cross-domain: **«Project-F»**.

## Agent interface (تا پیش از ARCHITECT_CHARTER — نسخه حداقلی)

- **خواندن مجاز:** PROJECT.md، master-reference، نوت‌های validation و لاگ آزمایش‌ها.
- **نوشتن مجاز:** فقط پیشنهاد (proposal)، گزارش و draft داخل همین پوشه؛ هیچ اکشن خارجی (پست، پیام، ساخت اکانت، پرداخت) بدون verdict انسانی.
- **ممنوع مطلق:** echo هویت پارتنر، عکس/محتوا، یا هر جزئیات شناسایی‌پذیر در تلگرام، داشبورد یا هر خروجی خارج از این پوشه — فقط کد «Project-F».
- **Security Gate:** تا وقتی ردیف‌های CRITICAL در [[ROTATION_CHECKLIST]] باز است، همه ایجنت‌ها روی این پروژه read-only هستند.

## KPIs (فاز validation)

delivery-rate پارتنر در trial sprint `[To measure]` · engagement روی teaserها `[To measure]` · نتیجه Track B (payment/banking پایدار: بله/خیر) — متریک درآمد از ابتدا به صبا گزارش شود (شرط تعهد او).

## Open blockers

**GATE 0: محل اقامت پارتنر ثبت و شاخه A/B انتخاب شود** — «محل اقامت پارتنر: ___ · تاریخ: ___ · پیامد: Branch A/B» ([[03 - Projects/اونلی فنز/architecture-blueprint-2026-07-04|بلوپرینت §۱]]) · ریسک #۱ (consistency زیر friction) هنوز تست‌نشده · مرز body در production plan با رضایت فعلی صبا در تضاد `[OPEN]` · سؤال آخر پرسشنامه نامفهوم ماند · Security Gate بسته

## Active Context

- تمرکز فعلی: بلوپرینت معماری 2026-07-04 آماده؛ **منتظر G0**
- تغییرات اخیر: 2026-07-03 — ثبت [[03 - Projects/اونلی فنز/پرسشنامه پارتنر - پاسخ‌های صبا|پاسخ‌های صبا]]؛ مرز محتوا قفل شد: فقط پا، بدون صورت/بدن + geo-block ایران · 2026-07-04 — کیت مغز پروژه ساخته شد · 2026-07-05 — [[03 - Projects/اونلی فنز/STATE-REPORT-2026-07-05|STATE-REPORT]] + verification pass (۸/۹ تناقض تأیید، ۱ اصلاح) + اعمال patch بلوپرینت §۱۱
- ۳ قدم بعدی: (۱) Track B/C — تحقیق desk درباره payment/banking و automation-fit، time-box یک هفته (۲) بازپرسیدن سؤال آخر پرسشنامه به زبان ساده‌تر (۳) طراحی Track A sprint با متریک صریح و گزارش‌دهی زودهنگام نتیجه مالی به صبا
- تصمیم‌های باز: «مسیر safe expansion به body» در production plan — صبا فعلاً بدن را رد کرده؛ منجمد یا حذف؟

## Progress

- چه کار می‌کند: master-reference کامل، production plan، funnel دیاسپورا، رجیستر ۵ ریسک، پرسشنامه پارتنر پاسخ‌داده‌شده
- چه مانده: Track A/B/C validation، زیرساخت legal/banking (مشروط به عبور از گیت‌ها)
- مشکلات شناخته: تعهد پارتنر مشروط به دیدنِ مسیر پول‌دهی است؛ تضاد مرز body با production plan

## Next actions

- [ ] **G0** — ثبت محل اقامت پارتنر + انتخاب Branch A/B (بلوپرینت §۱)
- [ ] ارسال پیام آماده به صبا (بازپرسیدن سؤال آخر + انتظارات — بلوپرینت §۴.۲) و ثبت جواب
- [ ] توافق مکتوب دونفره (بلوپرینت §۴.۱) — فقط بعد از Branch A
- [ ] تصمیم: انجماد/حذف «expansion به body» + تعیین hours واقعی (30h vs 3–5h)
- [ ] روز صفر زیرساخت (بلوپرینت §۵، ~۴–۵ ساعت) → شروع warm-up هفته ۱
- [x] Track B + C (desk research) — انجام شد 2026-07-04: GO conditional / GO limited

## نوت‌های مرتبط

- [[03 - Projects/اونلی فنز/پرسشنامه پارتنر - پاسخ‌های صبا|پرسشنامه پارتنر — پاسخ‌های صبا]]
- [[03 - Projects/اونلی فنز/اونلی فنز|لاگ پیام‌های تلگرام — اونلی فنز]]
- [[03 - Projects/اونلی فنز/Knowledge_Base_Memory_Synthesis|Knowledge_Base_Memory_Synthesis]]
- [[03 - Projects/اونلی فنز/project-master-reference|project-master-reference]]

## مرتبط

<!-- Tier A · CONNECTIONS-MAP (_memory) · اعمال 2026-07-04 -->
- [[04 - Architect System/architect/ARCHITECT_CHARTER|ARCHITECT_CHARTER]]
