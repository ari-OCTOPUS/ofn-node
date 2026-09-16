# BLOCKERS — Board2 Windows wire (reconciled)
captured_at_local: 2026-08-22T17:19:30+10:00 (Australia/Sydney)

## Closed on laptop this turn
1. F:\octopus-wire ABSENT → CREATED
2. MESSAGES-WINDOWS.md missing id:wNNN → id:w001 APPENDED (ca038d4)
3. Laptop GitHub HTTPS push → WORKS via GCM (after initial fail) — origin/ofn/wire == ca038d4
4. Germline ofn/wire → UPDATED @ 175e9565 with MESSAGES-WINDOWS.md (+ PROTOCOL/BOARD/ONBOARDING/BACKLOG) for SMB fetch

## Still open
1. **Board GitHub fetch** of origin ofn/wire — DietPi lacks HTTPS creds (live probe tip still fec6c2f). Optional owner: read-only GitHub creds on board.
2. **Phase-3** CONTROL_URL / OUTBOUND / BOARD_CP_PULL intentionally unarmed until owner G7.
3. **Playbook step 4 cron** — 2-hourly Windows wire automation not installed.
4. **gh CLI** — not on PATH (git+GCM used).

## Secrets policy
No secrets written to wire, evidence, or chat. PAT only in OS credential manager / board secret store.
