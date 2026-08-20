# Closed Loops

Generated: 2026-08-20

## SHADOW_CLOSED

- Authorized Telegram update → durable intent → same task/run IDs → dispatch marker → result → deterministic outbox → fake transport → delivery receipt → disk readback → CLOSED.
- Duplicate update suppression: 5/5 shadow duplicates, zero duplicate effects.
- Crash after intent: resumes same task/run.
- Crash after dispatch: fails closed to NEEDS_RECONCILIATION.
- Crash/uncertainty at send boundary: one transport attempt, no automatic resend.
- Confirmed receipt restart: prior message ID returned, transport not called.
- Explicit failed send receipt: no longer counted as ANSWERED.
- Multi-message task: each reply has an independent deterministic receipt.

## PRODUCTION_CLOSED

None in this session. The live flag is off, no process restart occurred, and no owner Telegram canary events were sent.
