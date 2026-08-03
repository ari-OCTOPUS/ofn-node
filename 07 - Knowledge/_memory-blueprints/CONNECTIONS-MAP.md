---
type: report
subject: "نقشهٔ ارتباطات جدید — مقایسهٔ تمام دایرکتوری‌ها (propose-only)"
date: 2026-07-04
method: "اسکن ۳۸۵ نوت · گراف wikilink · unlinked-mention با word-boundary + نرمال‌سازی NFC/RTL · فیلتر عنوان‌های generic"
status: draft
related: "[[REVIEW]] · [[LINK-DISCOVERY-PROMPT]] · [[LIVING-BRAIN-BLUEPRINT]]"
---

# CONNECTIONS-MAP — ارتباطات کشف‌شده بین دایرکتوری‌ها

**هیچ نوتی ویرایش نشده.** این نقشه پیشنهاد است؛ اعمال فقط بعد از verdict آری (پروتکل اعمال در [[LINK-DISCOVERY-PROMPT]]).

## آمار پایه (اسکن زندهٔ امروز)

| متریک | مقدار |
|---|---|
| نوت اسکن‌شده (خارج از محدودهٔ منفی) | ۳۸۵ |
| میانگین out-degree | ۲.۳۶ |
| orphan (درجهٔ صفر) | ۱۴۱ — بخش بزرگی «خوشهٔ جزیره‌ای» عمدی (brushline، فیوژن KB)، نه orphan واقعی |
| کاندیدای خام mention | ۲۳۶۳ → پس از فیلتر boundary/generic: ۵۳۷ → بین‌دایرکتوری: ۲۲۸ → curated: ~۱۷۴ |

## Tier A — اطمینان بالا، آمادهٔ اعمال (~۴۰ لینک)

منبع صریحاً به مقصد اشاره می‌کند ولی wikilink ندارد. جهت پیشنهادی: بخش `## مرتبط` در انتهای نوت منبع.

**Crypto ↔ معماری/ایجنت‌ها** (شکاف اصلی: اسناد معماری Crypto از charter الگو گرفته‌اند ولی لینک ندارند)
- `CRYPTO_ARCHITECTURE_v1` → [[04 - Architect System/architect/ARCHITECT_CHARTER|ARCHITECT_CHARTER]] · [[05 - Agents/AGENT_REGISTRY|AGENT_REGISTRY]] · [[06 - Architecture Maps/SYSTEM_MAP|SYSTEM_MAP]]
- `L7_FLEET_DESIGN` → ARCHITECT_CHARTER
- `MASTER_ARCHITECTURE_PROMPT` → [[04 - Architect System/architect/01-Project/SYSTEM-BLUEPRINT-v2|SYSTEM-BLUEPRINT-v2]] · ARCHITECT_CHARTER · AGENT_REGISTRY · [[03 - Projects/Accounting/Accounting|Accounting]]

**Accounting ↔ اکوسیستم** (پل بین‌پروژه‌ای واقعی)
- `Ecosystem-Rollout-Plan` → [[06 - Architecture Maps/ECOSYSTEM|ECOSYSTEM]] · [[06 - Architecture Maps/Property Schema|Property Schema]] · [[03 - Projects/Crypto - etoro/Crypto - etoro|Crypto]] · [[03 - Projects/Lead-نقاشی/Lead-نقاشی|Lead-نقاشی]]
- `Accounting/PROJECT` → Lead-نقاشی

**brushline ↔ ECOSYSTEM** (۷+ نوت governance/KB به اکوسیستم اشاره دارند — رفع جزیره‌ایِ بخشی از خوشه با «یک» لینک hub در هر نوت)
- `00_governance/PROJECT_FULL_CONTEXT` · `PROJECT_MANIFEST` · `ROADMAP` · `10_knowledge_base/KB-00_master_synthesis` · `KB-14_ecosystem` · `30_process/BRUSHLINE_theory_completion_prompt` · `CONSISTENCY_REPORT` → همگی → ECOSYSTEM

**ایجنت‌ها ↔ پروژه‌ها** (ناوگان به پروژه‌ها می‌خورد ولی رجیستری لینک ندارد)
- `AGENT_REGISTRY` → Accounting · Lead-نقاشی · [[03 - Projects/Ziman Galerry/Capacity & Channels|Ziman Capacity & Channels]] · [[03 - Projects/Crypto - etoro/Portfolio Registry|Portfolio Registry]]
- `Research Scout Fleet` → Accounting · Ziman Capacity & Channels · [[04 - Architect System/architect/04-Docs/fusion-audit/REFACTOR_PLAN|REFACTOR_PLAN]]

**پروژه ↔ اهداف (Life OS)** — تنها پل موجود به لایهٔ اهداف؛ ارزشمندترین کلاس
- `Lead-نقاشی` (شناسنامه) و `Report - Sydney Lead Channels` → [[02 - Life OS/Weekly Review|Weekly Review]]

**architect ↔ پروژه‌ها** (بلوپرینت‌ها دربارهٔ پروژه‌ها حرف می‌زنند، بی‌لینک)
- `architect/PROJECT` · `00-Home` · `SYSTEM-BLUEPRINT-v1/v2/v3-proposal` · `BACKLOG` · `DECISIONS` · `GAPS` → هرکدام → پروژه‌های نام‌برده (Accounting / Lead-نقاشی / اونلی فنز)
- `اونلی فنز/PROJECT` → ARCHITECT_CHARTER
- `Mining` (شناسنامه) → ECOSYSTEM

## Tier B — نیازمند بازبینی انسانی قبل از اعمال

- `_Index - Projects` → شناسنامه‌های پروژه: ایندکس الان به `PROJECT.md`ها لینک دارد؛ افزودن لینک شناسنامه شاید عمدی حذف شده. verdict آری.
- `Report - Vault Relationship Map v3` → ~۱۲ مقصد: نوت گزارشی است؛ لینک‌دهی مفید ولی کم‌اولویت.
- خوشهٔ «فیوژن KB → SERVER_ARCHITECTURE» (۱۹ مورد) و «Mining → قالب‌های KB فیوژن»: به‌احتمال قوی artifact فهرست‌درختی/قالب مشترک است نه ارجاع معنایی — قبل از هر اعمالی یک‌به‌یک چک شود.

## Tier C — اعمال نشود

- منابع `_superseded/` (آرشیوند)، `HANDOFF`/`Brain` (overwrite-شونده)، پرامپت‌های Inbox (گذرا)، هر فایل کلاس قرنطینه ([[REVIEW]] یافتهٔ ۲).

## یافتهٔ ساختاری

الگوی تکرارشونده: **لایهٔ معماری (۰۴/۰۵/۰۶) پروژه‌ها را «می‌بیند» ولی به آن‌ها لینک نمی‌دهد، و برعکس.** hub-and-spoke روی کاغذ هست، در گراف نیست. Tier A دقیقاً همین شکاف hub↔spoke را می‌بندد — پیش‌نیاز «مغز زنده» ([[LIVING-BRAIN-BLUEPRINT]]).
