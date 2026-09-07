---
type: dashboard
status: active
tags: [dashboard]
updated: 2026-09-07
---

# خانه — داشبورد اصلی

> 🎯 **سیزن ۱ بسته شد → [[ACTIVE-SEASON-REVENUE-ON-LIVE-LOOP-20260907|سیزن درآمد روی حلقهٔ زنده]] (2026-09-07):** اولین حکم قابلیتی با ۲۰۴ رسید گیت‌پذیر صادر شد (`09-LANES/ACD-PREREG-20260907/FAMILY-VERDICT-ACD-01`)، حسگرها صادق (`09-LANES/MP-V41-U1-20260907/U1-RECEIPT`)، بکاپ سبز (`09-LANES/R1-GITWRITE-20260907/LANE-REPORT`)، رمزها تجمیع (`09-LANES/R2-SECRETS-20260907/ROTATION-RUNBOOK`، چرخش waive شد)، دکمهٔ `09-LANES/OPS-RESTARTALL-CAPABILITY-20260907/CAPABILITY-MAP-AND-TEST-PROMPTS` آماده. مرور کامل: [[07 - Knowledge/octopus/95-SEASON-REVENUE-CLOSEOUT-2026-09-07|نوت ۹۵]] · وضعیت جلسه قبل: [[01 - Dashboard/HANDOFF|HANDOFF]] · تاریخچهٔ بلوک‌های قبلی: `_Archive/Logs/HANDOFF-archive-2026-09-07.md`

> نقطه ورود به کل vault. قواعد: [[_PROJECT_INSTRUCTIONS|اینستراکشن پروژه v2.0]]
>
> 🧠 **مغز:** [[01 - Dashboard/Brain|Brain]] (snapshot ۲۰۲۶-۰۷-۰۶، زنده نیست) · زیرساخت زنده: `_ops` + [[07 - Knowledge/genome-system/INDEX|genome-system]]

## پروژه‌ها (خودکار — Bases)

![[Projects.base]]

## Inbox و پردازش‌نشده‌ها (خودکار — Bases)

![[Inbox.base]]

## نقشه اکوسیستم

- [[04 - Architect System/architect/00-Home|architect]] — لایه مادر: کنترل، تحقیق و بازرسی همه پروژه‌ها از تلگرام — نقشه کامل: [[06 - Architecture Maps/ECOSYSTEM|ECOSYSTEM]]
- درآمد و کسب‌وکار: [[03 - Projects/Lead-نقاشی/PROJECT|Lead-نقاشی]] (درآمد اصلی)، [[03 - Projects/Ziman Galerry/PROJECT|Ziman Gallery]]، [[03 - Projects/اونلی فنز/PROJECT|اونلی فنز]]
- سرمایه‌گذاری و سخت‌افزار: [[03 - Projects/Mining/PROJECT|Mining]]، [[03 - Projects/Crypto - etoro/PROJECT|Crypto - etoro]]
- زیرساخت مالی: [[03 - Projects/Accounting/PROJECT|Accounting]]
- دانش شخصی: [[07 - Knowledge/هیپنوتیزم  و خودآگاهی/PROJECT|هیپنوتیزم و خودآگاهی]]، [[07 - Knowledge/Time-Architecture/PROJECT|Time-Architecture (معماری زمان)]]
- سلامت شخصی: [[03 - Projects/WLOS - Weight Loss OS/PROJECT|WLOS — Weight Loss OS]] (کوچ تلگرامی کاهش وزن، v0.1.1 هنوز live نشده)
- تحقیق خودترمیم/شناختی (shadow، propose-only): [[03 - Projects/Chord/PROJECT|Chord]] (فیلتر وترِ ریاضی برای دکتر تکاملی) · [[03 - Projects/research-spec-compiler/PROJECT|research-spec-compiler]] (اندام شناختیِ Ring-2)
- زیرساخت زنده (`_ops` + ژنوم): [[_ops/ORGANISM-SPEC|ORGANISM-SPEC]] (ارگانیسم متابولیسم-مناظره-تکثیر، سایه $0) · پنل مالک `_ops/panel/` (`http://127.0.0.1:8790` — پروفایل/پروژه‌ها/ارگانیسم) · [[07 - Knowledge/genome-system/INDEX|genome-system]] (v0.4.3) · همکار/کشف: [[06 - Architecture Maps/OCTOPUS-COLLABORATOR-INTERACTION-CONTRACT|Interaction Contract]] · [[_ops/DISCOVERY-PROTOCOL|DISCOVERY-PROTOCOL]]
- لایهٔ تئوری/معماری CHRONOS-FABLE OS (سنتزِ ۱۶‌پوشه‌ایِ کورپوسِ OCTOPUS/CHRONOS، تئوریِ همین ارگانیسم زنده) — **بایگانی شد**، اینجا زنده نیست: `_Archive/CHRONOS-FABLE-OS/` (PROJECT، HANDOFF، `13_MasterPrompts/MasterSystemPrompt.v2`)

## بخش‌ها

- `00 - Inbox` — ورودی‌های دسته‌بندی‌نشده + [[00 - Inbox/AGENT_QUESTIONS|سوالات ایجنت‌ها]]
- `02 - Life OS` → [[02 - Life OS/_Index - Life OS|ایندکس]] · [[02 - Life OS/Weekly Review|مرور هفتگی]]
- `03 - Projects` → [[03 - Projects/_Index - Projects|ایندکس پروژه‌ها]]
- `04 - Architect System` → [[04 - Architect System/architect/00-Home|Home معماری]]
- `05 - Agents` → [[05 - Agents/_Index - Agents|ایندکس Agents]]
- `06 - Architecture Maps` → [[06 - Architecture Maps/_Index - Architecture Maps|ایندکس]] · [[06 - Architecture Maps/Property Schema|Property Schema]]
- `07 - Knowledge` → [[07 - Knowledge/_Index - Knowledge|ایندکس دانش]]
- `08 - Assets` — عکس‌ها و پیوست‌ها (Telegram-2023 · WhatsApp-2026)
- `09 - People` → [[09 - People/_Index - People|ایندکس People]]
- `10 - Telegram processing` → [[10 - Telegram processing/_Index - Telegram processing|ایندکس]] · [[10 - Telegram processing/SOP|SOP]] · [[10 - Telegram processing/ROUTING|ROUTING]]
- `_Templates` — قالب نوت‌های جدید (project / knowledge / log / person / agent / handoff)

## پوشه‌های سیستمی (خارج از دانش)

- آرشیو باینری‌ها — از 2026-07-04 **خارج از vault**: `Desktop\backup-Archive` (باینری‌ها، بازنشسته‌ها ~۳٫۲ گیگ + `Logs/Cleanup 2026.md`) — انتقال به آن فقط توسط مالک؛ داخل vault دیگر `_Archive` وجود ندارد
- `_Duplicates` — قرنطینه تکراری‌ها + گزارش «_گزارش تکراری‌ها.txt» — فقط مقصد انتقال
