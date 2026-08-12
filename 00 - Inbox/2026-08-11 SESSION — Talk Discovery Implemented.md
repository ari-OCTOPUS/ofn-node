---
type: session-notes
status: active
created: 2026-08-11
updated: 2026-08-11
tags: [octopus, talk-discovery, collaborator, ai-core, propose-only]
aliases: [Talk Discovery, جلسه Talk Discovery]
---

# SESSION — Talk Discovery A–D (ادغام Obsidian)

> پیاده‌سازی روی worktree `octopus-integration-collaborator`؛ اسناد vault هم‌تراز شدند.
> کد runtime هنوز merge/arm نشده مگر رأی جدا.

## حکم یک‌خطی

همکار می‌تواند واقعی حرف بزند (adapter → `model_router`، task=`collab_chat`)؛ MiniApp و DM یک مغز دارند؛ کشف پنهان propose-only است — بدون auto-arm و بدون vision/money.

## اسناد Obsidian (canonical)

| موضوع | نوت |
|---|---|
| قرارداد تعامل | [[06 - Architecture Maps/OCTOPUS-COLLABORATOR-INTERACTION-CONTRACT\|OCTOPUS-COLLABORATOR-INTERACTION-CONTRACT]] |
| pointer runtime | [[_ops/INTERACTION-CONTRACT\|INTERACTION-CONTRACT]] |
| پروتکل کشف | [[_ops/DISCOVERY-PROTOCOL\|DISCOVERY-PROTOCOL]] |
| دفترچه قابلیت | [[_ops/CAPABILITY-JOURNAL\|CAPABILITY-JOURNAL]] |
| نردبان شاهد | [[_ops/EVIDENCE-LADDER\|EVIDENCE-LADDER]] |
| مسیر مدل | [[_ops/ROUTE-POLICY\|ROUTE-POLICY]] |
| ADR همکار | [[03 - Projects/research-spec-compiler/adr/ADR-023-octopus-collaborator\|ADR-023]] |
| رأی تمرکز AI | [[00 - Inbox/2026-08-11 OWNER — Focus AI Core Hidden Capabilities\|OWNER AI focus]] |
| HANDOFF | [[01 - Dashboard/HANDOFF\|HANDOFF]] |

## فازها

| فاز | وضعیت |
|---|---|
| A — adapter مدل + intro | ✅ |
| B — یک مغز MiniApp+DM + عکس صادقانه | ✅ |
| C — journal / dark pulse / digest build-only | ✅ |
| D — پروتکل مالک↔اختاپوس + سقف روزانه | ✅ |
| ادغام قرارداد + `collab_chat` در TASK_TIERS | ✅ |

## Arm زنده (هنوز رأی مالک)

```text
OCTOPUS_WIRE_COLLAB=1
OCTOPUS_COLLAB_USE_MODEL=1
OCTOPUS_COLLAB_MODEL_DAILY_CAP=20
```

سپس restart + boot snapshot. پول/لید/outbound خارج از این رأی.

## حقیقت

```text
shared-collab-brain + honest-photo + discovery-journal + capped-collab-chat
!= vision != money-live != unbounded-model != auto-arm
```

## بعدی

1. رأی arm روی live (یا رد)
2. ۷ روز حلقهٔ DISCOVERY-PROTOCOL
3. merge worktree فقط با verdict جدا
