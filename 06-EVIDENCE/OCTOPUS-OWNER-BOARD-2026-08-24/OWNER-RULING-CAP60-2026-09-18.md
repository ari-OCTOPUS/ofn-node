# OWNER-RULING-CAP60-2026-09-18 — daily send cap = 60

- stamp: 2026-09-18T08:10Z (18:10 AEST)
- channel: owner chat, clickable 4-option question (AskUserQuestion), owner selected
  **«۶۰ در روز (پیشنهادی)»**.
- effect: the first outbound wave (ruling WAVE1, full 68) proceeds at ≤60 sends/day.

## Execution verification (NO mutation required)
The OPERATIVE cap file — `state/revenue-drive/standing-authorization.json` (the one
`money_tools._standing_authorization()` and `send_queue.py` actually read) — **already carries
`scope.daily_cap = 60`**, set earlier today by the runtime lane citing the owner's own words
("no artificial limit, as much as it can"), with a per-run batch of 25 as bug-blast protection.
Its expiry: 2026-10-02T02:58:30Z. No file was edited for this ruling.

- `i7-runtime.json` still mirrors a stale `standing_authorization.daily_cap: 10`, but code
  inspection shows send_queue.py reads i7-runtime.json ONLY for the hold-gate fields
  (`no_auto_customer_send`, `customer_send`, `mode`) — all currently open
  (customer_send=true, no_auto_customer_send=false, mode=standing_authorized). The 10 is
  dead weight; left for the runtime lane to tidy (cosmetic, no consumer).
- locks re-checked this session: SEND-PAUSED / AUTH-REVOKED / CHANNEL-REVOKED /
  STOP-AUTONOMY / ops-halt all absent.

## Expected wave cadence (measured from the code + timer)
next tick 12:00:36Z → 25 (batch limit) → +6h 25 (50) → +6h 10 (60/day cap) → next day 8.
Full 68 contacted within ~24–30h of the first tick. DoE reply rides the same path
(guard: one reply per inbound).

rollback: none needed (no state mutated). Revoke path unchanged: AUTH-REVOKED file.
