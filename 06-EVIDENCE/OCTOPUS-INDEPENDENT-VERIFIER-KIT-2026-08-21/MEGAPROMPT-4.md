---
type: architecture-debug-plan
scope: wave1-megaprompt-4-post-canary
owner: Ari
date: 2026-08-21
execution_authorized: false
live_send_authorized: false
---

# MEGAPROMPT 4 — post-canary expansion (plan only)

Not executed. Owner order: expansion after a live n=1 canary.

## Suggested waves (do not start without a new owner order)

1. G-CANARY-OUT: one `sendMessage` via Center-owned env, OWNER_CHAT_ONLY, text `WAVE1-CANARY-N1`, ceiling 1.
2. Hold `tg:223883344` / `tg:223883346` forever (no auto-resend).
3. T5: watchdog consumes `watchdog_truth()` (TCB-adjacent — separate gate).
4. T7: cockpit fields from measured APIs only.
5. Close remaining INCONCLUSIVE lab cards only with named fixtures (hub/doctor/C21/C23).
6. 60-minute no-send soak before `TELEGRAM_LOOP_BASELINE`.

Forbidden without extra gates: webhook, paid calls, second recipient, force-push.
