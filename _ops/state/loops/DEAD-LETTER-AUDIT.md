# Dead Letter Audit

Generated: 2026-08-20

## Durable loop behavior

- Unknown send outcome is stored as `NEEDS_RECONCILIATION`; automatic resend count is zero.
- Replay after `DISPATCHED` without a result is stored as `NEEDS_RECONCILIATION`.
- Poison/update handler exceptions continue to use the existing center dead-letter path; `test_no_silent_message_drop.py` passes 8/8.
- Duplicate updates are disposition-logged and suppressed before business logic.

## Remaining debt

- Existing legacy dead letters are not migrated into the new per-event state machine.
- No production reconciliation worker was activated.
- `event_bridge.py` failed sends are still suppressed by pre-send content dedupe rather than entering a delivery DLQ.

No dead-letter record was deleted or replayed in this session.
