# G22 orphan script quarantine note
Stamp: 2026-08-23T09:13:00+10:00
Action: INVENTORY + QUARANTINE NOTE only. Do not delete unless clearly safe and owner-approved.
Suspect orphans under _ops/scripts/:

- _ops\scripts\__pycache__\tg_bridge_once.cpython-313.pyc (18696 B)
- _ops\scripts\tg_bridge_loop.sh (250 B)
- _ops\scripts\tg_bridge_once.py (14360 B)
- _ops\scripts\unlock_self_progress.py (12831 B)

Treat as non-canonical vs telegram_center + live_telegram_gate + durable loop outbox.
Prefer center paths; do not wire orphans without review.
