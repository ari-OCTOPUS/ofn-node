---
type: handoff-note
title: "راهنمای اتصال زیرسیستم‌ها به F:\backup"
created: 2026-08-15
source: "CLAUDE.md ریشه (2026-08-03) — نقل‌قول قواعد، بدون تغییر"
---

# INTEGRATION-GUIDES — راهنمای وصل هر زیرسیستم به F:\backup

## قواعد کار ایجنت در این Vault (نقل از CLAUDE.md ریشه)

**ترتیب خواندن (کم‌هزینه → عمیق):**
1. شروع جلسه: `01 - Dashboard/HANDOFF.md` + نگاهی به `00 - Inbox`
2. جهت‌یابی: `01 - Dashboard/Home.md` → MOC بخش → بعد نوت‌های تکی
3. قبل از کار در پروژه: `PROJECT.md` همان پروژه
4. کار MCP/ایجنت موازی: `_ops/octopus_mcp/CONSTITUTION.md`

**محدودهٔ منفی:** `_Archive` و `_Duplicates` باز نشوند مگر صریحاً · `09 - People` فقط برای کار اشخاص · مسیرهای `.agentignore` هرگز خوانده/نوشته/echo نشوند.

**پایان جلسه:** تازه‌سازی `Active Context`/`Progress` پروژه‌های لمس‌شده · بازنویسی `01 - Dashboard/HANDOFF.md` (فقط wikilink، بدون secret) · اگر >۵ فایل تغییر کرد: کامیت `agent-checkpoint: <خلاصه>` · اجرای اسکریپت‌های اعتبارسنجی `04 - Architect System/scripts/`

## نقشهٔ اتصال زیرسیستم‌ها (برآمده از همین مأموریت)

| زیرسیستم | نقطهٔ اتصال | یادداشت بازیابی |
|-----------|-------------|------------------|
| ارگانیسم OCTOPUS | `OCTOPUS/CURRENT-TRUTH.md` (runtime می‌نویسد) | [[../01-TRUTH/CURRENT-TRUTH|01-TRUTH/CURRENT-TRUTH]] (آینه) |
| دکتر | `OCTOPUS-DOCTOR/` (Vault مستقل تودرتو) | [[../01-TRUTH/SERVICE-STATUS|SERVICE-STATUS]] |
| NBB-CP (۴ نسخه) | `03 - Projects/NBB-Control-Plane` + `4d_system/*` | [[../04-SYSTEMS/NBB-CP|NBB-CP]] |
| برد اورنج‌پای | `octopus-bridge/octopus_bridge/` (gated-off) | [[../04-SYSTEMS/OFN-NODE|OFN-NODE]] |
| hypothesis-engine | `_ops/hypothesis_engine/` | [[../04-SYSTEMS/HYPOTHESIS-ENGINE|HYPOTHESIS-ENGINE]] |
| conversation-hub | `_ops/conversation_hub/` (فلگ ۰) | [[../06-EVIDENCE/ADR-040|ADR-040]] |
| epistemics | `_ops/epistemics/` (default OFF) | [[../06-EVIDENCE/ADR-039|ADR-039]] |
| ADRها | `03 - Projects/research-spec-compiler/adr/` | [[../06-EVIDENCE/ADR-037|ADR-037]]… |
| مغز مادر/architect | `04 - Architect System/architect/` (Vault تودرتوی دیگر) | [[../02-DECISIONS/DECISIONS|DECISIONS]] |
