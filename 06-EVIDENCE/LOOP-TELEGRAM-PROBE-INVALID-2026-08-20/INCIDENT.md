---
type: evidence
status: active
tags: [incident, telegram, probe, 2026-08-20]
created: 2026-08-20
updated: 2026-08-20
created_by: agent
project: "[[04 - Architect System/architect/PROJECT]]"
---

# LOOP-TELEGRAM-PROBE-INVALID

```text
LOOP-TELEGRAM-PROBE-INVALID
type: BROKEN_FEEDBACK + SILENT_SPAM
symptom: PROBE_RESPONSE_INVALID repeated
evidence: telegram_events remains 11 across beats 43303–43337
likely break: probe response parser | event consumer | acknowledgment/readback
severity: HIGH
status: OPEN (spam suppressed; closure unproven)
```

Wave 1 remains locked. Memory-read OK is not Telegram closure.

## Trace

```text
EVENT-TIME-PROBE-2026-08-20.json (frozen 08:06Z)
  producer: research/event_time_probe/run_probe_v2.py::execute_probe
  validation: response.content == request.nonce (exact)
  fail: nonce_match=false · finish_reason=length (truncated, max_tokens=32)
  spine_event_written=false · executable=false
  retries_allowed=0  → probe itself is already terminal INVALID
        ↓ (no consumer)
_ops/scripts/tg_bridge_once.py::snapshot  reads the frozen JSON every tick
        ↓ identity hash INCLUDED beat  (FIRST_BROKEN_EDGE)
tg_bridge_loop.sh  sleep 300
        ↓ changed=true every organism beat
_http_send → owner chat   (no outbox, no terminal, no coalesce)
telegram_events COUNT in spine.db stays 11
        ↓ never treated as a new ingest, never ACK/readback
```

## Condition (A–F)

**B + F**, with a frozen **C** on the original probe:

| id | true? | note |
|---|---|---|
| A | no | not reprocessing a Telegram update_id; no inbound event |
| B | **yes** | owner messages generated with no new telegram event (count stuck at 11) |
| C | **yes (original probe)** | parser required exact nonce; model returned truncated `length` |
| D | no | no valid Telegram response was produced |
| E | no | delivery of the *heartbeat* succeeded; there was no probe-response receipt path |
| F | **yes** | 5-min loop had no terminal/dedup; beat in hash → infinite user-facing retry |

## Safe mode

- `_ops/STOP-TG-HEARTBEAT` present
- `tg_bridge_once.main` live-sends only if `LIVE-TG-BRIDGE.flag` exists **and** STOP is absent
- Heartbeat goes to `_ops/state/loops/tg-bridge-heartbeat.jsonl` (internal)
- Same INVALID payload: incident once, digest once after 6h, then `DEAD_LETTERED`

## Fear message

`instant_alert_bridge._sig_fear` can send «ترس — همین حالا» with **no** task_id / event_id / receipt. Separate from this probe spam. Not closed here.

## Do not

- Re-run the DeepSeek event-time probe (paid)
- Mark Telegram loop VERIFIED
- Treat memread OK or telegram_events=11 as closure
