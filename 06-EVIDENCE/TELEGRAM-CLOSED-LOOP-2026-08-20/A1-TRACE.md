---
type: evidence
status: active
tags: [telegram, a1, canary, 2026-08-20]
created: 2026-08-20
updated: 2026-08-20
created_by: agent
project: "[[04 - Architect System/architect/PROJECT]]"
---

# A1 — Canary دور دوم (زنده روی کد قدیم)

مالک `/status` زد قبل از reload مرکز. علت تعیین شد؛ ریاستارت این سشن انجام نشد.

```yaml
update_id: 223883326
bot_id: 7992324219
message_id: (not in inbound-log)
message_date: 2026-08-20T09:38:01Z
spine_event_id: evt_f726433abb33404b
telegram_event_delta: +1
model_intents_delta: +1 synthesize (deepseek-v4-flash)
cost_receipts_delta: +1 (task_id=synthesize, run_id empty)
outbound_message_ids: 1 logical DM (stream=center, chars=211, bot_role=outer)
handler_count: 1 (center.py PID 26388)
owner_auth: true
```

## PASS/FAIL

| سنجه | هدف | زنده ۱۹:۳۸ |
|---|---|---|
| telegram_events +1 | exact | PASS |
| bot_id = 7992324219 | pin | PASS |
| owner auth | true | PASS |
| spine rows +1 | exact | PASS |
| model intents +0 | exact | **FAIL** |
| cost receipts +0 | exact | **FAIL** |
| outbound replies | 1 | PASS |
| handlers for bot | 1 | PASS |

## علت (یک همبستگی)

`handle_local` رشته برمی‌گرداند → `center.py` روی `_rep.get("kind")` می‌ترکد → `except: pass` → fall-through به `ask_brain` → یک synthesize پولی (~AU$0.000711) و همان یک reply از مغز، نه از renderer محلی.

پچ (روی دیسک، نه در PID 26388):

1. `local_commands.handle_local` → `(bool, dict)` با `kind`+`text`
2. `telegram_adapter._as_reply_dict`
3. coerce رشته در `center.py` قبل از `.get`

دور بعدی canary فقط بعد از C-047 reload **فقط center**، سپس یک `/status` به بات کانونیکال.
