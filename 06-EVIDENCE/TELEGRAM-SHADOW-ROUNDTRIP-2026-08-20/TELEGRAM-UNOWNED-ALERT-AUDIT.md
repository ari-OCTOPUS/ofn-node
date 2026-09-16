---
type: evidence
status: active
tags: [incident, telegram, unowned-alert, 2026-08-20]
created: 2026-08-20
updated: 2026-08-20
created_by: agent
project: "[[04 - Architect System/architect/PROJECT]]"
---

# LOOP-TELEGRAM-UNOWNED-INSTANT-ALERT

```text
LOOP-TELEGRAM-UNOWNED-INSTANT-ALERT
type: ORPHAN + LOST_ACK
severity: HIGH
status: OPEN
```

## Pre-fix (debug session 71ffce, runId=fear-pre)

`instant_alert_bridge.check` called `channel.send_text` with no task/event/receipt.

| field | pre-fix |
|---|---|
| producer | `_sig_fear` ← cortisol/stress 🔴 |
| trigger | `level` contains 🔴 |
| event_id | null |
| task_id / run_id | null |
| correlation_id | null |
| outbox | none |
| delivery receipt | none |
| readback | none |
| sender | direct `send_text` |

Log messages: `fear-unowned-payload`, `direct-send-text` (`bypasses_outbox: true`).

## Containment (do not treat as VERIFIED live loop)

- `_sig_fear` still builds the card (path not deleted).
- `check()` routes to `TelegramOrgan.enqueue_unowned_alert` (outbox-only, `sent=false`, `terminal=BLOCKED`).
- Direct Telegram send prohibited.
- No fabricated task_id.
- Dedupe: `message_key` in telegram-cursor `alert_keys`; organ `rate_s`.
- Wave 1 remains locked. No live canary.

outboxed=True
