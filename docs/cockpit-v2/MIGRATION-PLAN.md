# MIGRATION-PLAN (M0)
M0 done: snapshot, branch ofn/cockpit-v2-20260827, panel untouched
M1: read-only V2 BESIDE panel on same owner port (e.g. /cockpit-v2/), views status/nodes/legs/queue/audit; compare vs old panel
M2: owner command fixtures via Owner Control API, no real effects
M3: limited control (pause/resume test leg; restart/replay/expiry tests)
M4: production exceptions only after fresh E2E GREEN + Telegram canary
M5: retire old panel after parity+acceptance+rollback+7d observation (archive, not delete)
Rollback each step: remove V2 static path/disable flag; old panel untouched
