# OWNER DECISIONS — current state (2026-08-28)
- Producer today: owner (human) via legacy panel; recorded in outbox with manual_completed.
- New contract (this spine): ofn/adapters/owner_decision.py — 12-field decision, one decision per message, fake renderer only in this mission.
- Gate to executability: exact payload_sha + artifact_sha + verdict_sha binding, expiry, idempotency; fake_executor enforces (see tests).
- No real approval/send occurs in this mission (HOLD_EXTERNAL preserved).
