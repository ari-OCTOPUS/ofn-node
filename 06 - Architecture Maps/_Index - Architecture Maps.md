---
type: moc
status: active
tags: [architecture, diagrams]
updated: 2026-07-09
---

# ایندکس Architecture Maps

> نقشه‌های معماری کل اکوسیستم — دیاگرام‌ها و سندهای «تصویر بزرگ» که چند پروژه را به هم وصل می‌کنند. نوت‌های موجود پایین فهرست شده‌اند.

## قالب پیشنهادی

- هر نقشه یک نوت: عنوان + تاریخ + دیاگرام (Mermaid یا عکس در `08 - Assets`) + لینک به پروژه‌های درگیر.
- نسخه جدید = نوت جدید با suffix تاریخ؛ قدیمی‌ها می‌مانند (تاریخچه تصمیم‌ها).

## نوت‌های این بخش

- [[06 - Architecture Maps/ECOSYSTEM|ECOSYSTEM]] — نقشه کل اکوسیستم (از Inbox منتقل شد)
- [[06 - Architecture Maps/Property Schema|Property Schema]] — زبان داده vault (تک‌منبع حقیقت فرانت‌متر)
- [[06 - Architecture Maps/SYSTEM_MAP|SYSTEM_MAP]] — نقشهٔ اجزا و مالکیت
- [[06 - Architecture Maps/SYSTEM-OVERVIEW|SYSTEM-OVERVIEW]] — تصویرِ کلانِ سیستم
- [[06 - Architecture Maps/LANGAR-ALIAS-REGISTRY|LANGAR-ALIAS-REGISTRY]] — رجیستریِ هم‌نامیِ «لنگر/LANGAR/Anchor» (≥۶ referent)

## وضعیتِ صادقانهٔ «اسنادِ زنده» (D6، بازبینی 2026-07-09)

> ادعای «۱۲ سندِ زنده» (از octopus-atlas، بیرونی) عمدتاً aspirational بود. وضعیتِ واقعیِ گراند‌شده روی repo (recon 2026-07-09): ✅ live · 🟡 draft/جزئی · ❌ غایب.

| سندِ ادعایی | وضعیت واقعی | محل |
|---|---|---|
| SYSTEM_MAP | ✅ live | `06 - Architecture Maps/SYSTEM_MAP.md` |
| AGENT_REGISTRY | ✅ live | `05 - Agents/AGENT_REGISTRY.md` |
| ARCHITECTURE_DECISIONS | ✅ live (D-01..D-37) | `04 …/architect/01-Project/DECISIONS.md` |
| ORGANISM-SPEC | ✅ live | `_ops/ORGANISM-SPEC.md` |
| ECOSYSTEM / Property Schema / SYSTEM-OVERVIEW | ✅ live | همین پوشه |
| CHANGELOG | 🟡 جزئی (فقط genome) | `07 …/genome-system/CHANGELOG` |
| MASTER_ARCHITECTURE | 🟡 فقط draftِ Inbox | `00 - Inbox` (نسخِ v1.x) |
| KNOWLEDGE_GRAPH | ❌ غایب — نزدیک‌ترینِ واقعی = [[04 - Architect System/BIO-SYNTHESIS-MAP\|BIO-SYNTHESIS-MAP]] | — |
| DEPENDENCY_MAP | ❌ غایب — گرافِ وابستگی در recon/GROUNDING-PLAN | — |
| TECHNICAL_DEBT / RISK_REGISTER / ROADMAP / MISSING_EVIDENCE_REGISTER | ❌ به‌صورتِ سندِ اختصاصی غایب — محتوا پراکنده در AGENT_QUESTIONS/GROUNDING-PLAN | — |

**نتیجه:** «۱۲ سند» را به همین فهرستِ واقعی تقلیل بده؛ اگر سندی از ستونِ ❌ واقعاً لازم شد، هنگام نیاز ساخته شود (نه اسکلتِ خالی). مبنا: [[04 - Architect System/2026-07-09 CHRONO-GROUNDING-PLAN — design↔reality + roadmap + decision-gates]].

## سندهای معماری موجود در پروژه‌ها (کاندید نقشه کلان)

- [[03 - Projects/Lead-نقاشی/AiFarm-Lead/SERVER_ARCHITECTURE|SERVER_ARCHITECTURE — VPS چندپروژه‌ای]]
- [[03 - Projects/Lead-نقاشی/AiFarm-Lead/ARCHITECTURE_MASTER|ARCHITECTURE_MASTER — brushline]]
- بلوپرینت‌های architect در `04 - Architect System/architect/01-Project`

## نوت‌های مرتبط

- [[01 - Dashboard/Home|Home]]
