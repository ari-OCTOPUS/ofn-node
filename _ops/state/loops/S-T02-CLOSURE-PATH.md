# S-T02 Event Bridge Production Closure Path

Generated: 2026-08-21
Status: IN_PROGRESS (zero event_bridge invocations in the audited canary window)

## Current production path

`Center.beat()` → `event_bridge.beat(center)` → read new governor alert / incident event / protective edge / C6 transition → `event-bridge-outbox.jsonl` QUEUED → `Center.push_alert()` → Telegram durable sender → delivery → CONFIRMED or DELIVERY_FAILED → bounded pending retry (max 3) → DLQ.

The code is loaded in PID 23568 and `OCTOPUS_WIRE_EVENT_BRIDGE=1`; however the audited canary window had no qualifying alert, so production evidence is zero — absence is not closure.

## Closure test (production, bounded, no paid call)

1. Inject one **TEST_ONLY** synthetic critical event into an isolated fixture source (not the live governor ledger) and call `event_bridge.beat(fake center)` — already covered by `test_event_bridge_outbox.py` 3/3 (shadow).
2. Production canary (requires no owner message): create one reversible canary alert line tagged `CANARY-EVENT-BRIDGE-{nonce}` in the designated canary source, record source hash, run one beat, then restore the source to its prior bytes.
3. Verify exactly one outbox QUEUED and one CONFIRMED for deterministic key; exactly one Telegram delivery; one readback; zero direct-send; restart-no-resend.
4. Repeat with fake delivery failure in shadow only to prove pending retry/DLQ; do not force Telegram failure in production.
5. Independent verifier reconciles source event → event_bridge outbox → durable Telegram event/task/run → delivery receipt/readback.

## Alternative retirement proof

If policy decides event_bridge alerts are redundant with the durable center/cockpit, prove no production caller reaches it for 72 hours with flag ON, archive the bridge explicitly, remove its caller and flag, and keep regression tests proving zero direct sends. Do not call the path CLOSED merely because invocation count is zero.
