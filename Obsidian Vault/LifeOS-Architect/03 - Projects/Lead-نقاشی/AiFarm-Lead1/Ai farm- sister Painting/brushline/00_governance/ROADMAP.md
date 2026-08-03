# ROADMAP v3 — Brushline (Lead Gen نقاشیِ ساختمان، سیدنی)

> به‌روزرسانیِ v2 پس از تکمیلِ لایهٔ تئوری. تصمیمِ معماری قفل: خواهرِ LANGAR (reuse). وضعیت: **لایهٔ تئوری کامل → آمادهٔ فاز ۰**.

---

## ۰. North Star
دستیارِ owned-channelِ ارزانِ چندایجنتی که برای کسب‌وکارِ نقاشیِ سیدنی کانالِ مالکیتی می‌سازد، پاسخ/محتوا/follow-up را **draft** می‌کند، به ServiceM8/Tradify وصل می‌شود؛ اول برای خودت (survival)، بعد محصول.

سه Invariant: **INV-1** (no publish/spend/پیام بدونِ approval) · **INV-2** (PII/مالی هرگز در LANGAR/memory؛ ذخیره AU) · **INV-3** (auto-execution = kill switch + spend cap + hash-chained audit).

---

## ۱. لایهٔ پیش‌نیازِ تئوری (Phase −1) — وضعیت

| # | پیش‌نیاز | وضعیت | خروجی |
|---|---|---|---|
| P1 | بازار + lead-gen (owned vs rented) | ✅ | KB-13 |
| P2 | الگوهای multi-agent (Anthropic) | ✅ | KB-01 |
| P3 | Cheap-first router + هزینهٔ AUD↔credit | ✅ | KB-02 |
| P4 | Governance + قانونِ AU + LSA-نبودن | ✅ | KB-03 + KB-12 |
| P5 | Agent memory | ✅ | KB-04 |
| P6 | HITL approval queue | ✅ | KB-05 |
| P7 | Hash-chained audit log | ✅ | KB-06 |
| P8 | Constitution-gate (no false claims/ACL) | ✅ | KB-07 |
| P9 | Eval (Wilson + cost-per-booked-job) | ✅ | KB-08 |
| P10 | Lead/CRM + privacy + consent (Spam Act) | ✅ | KB-09 |
| P11 | Tool design + tool registry | ✅ | KB-01 |
| P12 | Integration با job-management (ServiceM8/Tradify) | ✅ | KB-01/KB-09 |
| P13 | Synthesis + MVP spec | ✅ | KB-00 + MVP spec |
| P14 | CONFIG + GLOSSARY + THREAT MODEL | ✅ | اسنادِ cross-cutting |
| P15 | Ecosystem + Lead Signals + Capital Works | ✅ | KB-14 |

> **همهٔ پیش‌نیازهای تئوری ✅** — هیچ ⏳ باقی نمانده.

---

## ۲. فازهای ساخت (با گیتِ ایمنی)

| فاز | کار | گیت / DoD |
|---|---|---|
| ۰ | scaffold + reuse interfaceهای LANGAR + جدا DB/process | تستِ «هیچ LANGAR» با JOIN جدولِ شخصی |
| ۱ | Researcher + Audience (read-only) | خروجیِ سورس‌دار از Gate رد شود |
| ۲ | Content/Copy + Asset (draft) | همه در صف؛ هیچ انتشار/ارسال |
| ۳ | Approve queue + audit log (hash-chain) | tamper-evidence تست‌شده |
| ۴ | Publish/Send + kill switch + spend cap (AU) | recheck دومرحله‌ای؛ no auto-post |
| ۵ | Lead-Capture + sync + speed-to-lead + متریک | cost-per-booked-job محاسبه‌پذیر؛ پیامِ اول human-approved؛ consent |
| ۶ | محصول‌سازی (multi-tenant) | تستِ «هیچ cross-tenant read»؛ key/cap/kill per-tenant (THREAT_MODEL §۵.۵) |

---

## ۳. سگمنت‌ها (به‌روز)
`residential` · `strata` · `property-manager` · `builder` · `commercial`.
**Capital Works = زیرمجموعهٔ `strata`** (محصول: `draft_capital_works_assessment`؛ از ۱ آوریل ۲۰۲۶ standard form اجباری). اولویتِ پیشنهادی: residential + strata/property-manager برای lead-gen محلی؛ Capital Works به‌عنوان wedgeِ فاز ۵+.

---

## ۴. Milestones
M0: Project ساخته‌شده + KB + instructions → **اکنون اینجا**.
M1..M5: فاز ۱..۵. M6 = cost-per-booked-job روی دادهٔ واقعی → تصمیمِ محصول.

## ۵. Cost Checkpoints
Brushline core ~AUD ۱۵–۶۵/ماه (جدا از trade subscription $۲۹–۷۹ و Ads). spend cap از روز اول در CONFIG. (جزئیات: KB-02.)

## ۶. خارج از scope (فعلاً)
ویدیوی فوتورئال؛ multi-tenant (فاز ۶)؛ بازسازیِ job-management (integrate به‌جایش)؛ بات‌های activity-based/password-sharing (ban-risk)؛ LSA (در AU وجود ندارد).

## ۷. قدم بعدی
شروعِ **فاز ۰** (scaffold/reuse). پیش‌نیاز: PROJECT_MANIFEST کامل + سه قلمِ «verify» در CONFIG بسته شود.
