# TELEGRAM CANONICAL FINDING (2026-08-28)
States (evidence: config + journal + unit files):
- 5 bot tokens CONFIGURED (ziman, lead, studio, studio_partner, __owner__) — mini-app shells served over them.
- PRODUCER: none automated. Owner decisions historically produced by OWNER via legacy panel → outbox (25 manual_completed rows: lead:quote 1, lead:reply 1, studio:publish 23).
- POLLER: zero active (no unit; octopus-telegram-bridge fragment absent).
- SENDER: alert.py implements sendMessage but 0 sends in ofn journal since 2026-08-20 → SHADOW.
- DEAD: octopus-telegram-bridge unit (inactive, blocked-config by design).
CANONICAL PROPOSAL (no new bot): ONE owner channel = __owner__ bot via Owner Control API long-poller (M2), reusing existing token; alert.py becomes the only sender implementation behind that API; all other paths archived (units removed only under owner GO). ACK≠SENT≠CUSTOMER_REPLY≠SETTLED_CASH enforced at ledger.
