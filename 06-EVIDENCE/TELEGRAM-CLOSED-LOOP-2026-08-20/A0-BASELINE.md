---
type: evidence
status: active
tags: [telegram, a0, baseline, 2026-08-20]
created: 2026-08-20
updated: 2026-08-20
created_by: agent
project: "[[04 - Architect System/architect/PROJECT]]"
---

# A0 — قفل، baseline، حفاظت lane

## PASS

```text
lease valid
canonical bot ID pinned
one canonical inbound process identified
no dirty shared-file ambiguity in this lane
```

## Freeze

| نقش | ID | handle |
|---|---|---|
| canonical owner | 7992324219 | @intergrade2725_Bot |
| approval | 8187434784 | @Robo2725_bot |
| Ziman | 8861821707 | (نه مسیر canary مالک) |

## PID (snapshot همین جلسه)

| پروسه | PID | یادداشت |
|---|---|---|
| center.py | 26388 | تنها poller کانونیکال |
| organism.py | 9904 | دست‌نخورده |
| brain.daemon | 25680 | دست‌نخورده |
| miniapp_gateway | 9120 | HMAC؛ getUpdates نمی‌زند |
| approval_channel | — | در این snapshot پیدا نشد |

Lease: `62440c28…` · agent A · scope `telegram, owner_console, spine_emitter, router_attribution, evidence, git` · هنوز hold.

Paid cognition و Full Loop تا گیت A4/A7 خاموش ماندند (این سشن صفر فراخوانی پولی از طرف ایجنت).

Manifest هش: [[A0-BASELINE.json]]
