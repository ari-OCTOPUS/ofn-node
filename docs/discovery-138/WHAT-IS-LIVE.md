# LIVE @ 2026-08-28T00:30Z
1. ofn.service pid1351408 — 4 shells + v1 API + live /cockpit-v2/ (restart 2026-08-27T01:33Z, provenance F-1 unverified)
2. mesh daemons active: supervisor, router, control-router, cycle-settler, verify-dispatcher + timers scheduler(15m)/budget(5m)/heartbeat(60s)
3. octopus-bridge pid589802 (:8796)
4. hypno.run pid672 (:8895, separate product)
5. cloudflared pid669 (:20241)
6. growing DBs: ledger 175 events, outbox 25, mesh processed 6489 / receipts 1992
7. ofn-backup.timer daily (last ok 2026-08-27T17:18Z); ofn-sync-watchdog(5m) + ofn-bridge-watchdog(2m)
Proof: systemctl show + ss owners + pid cmdlines + row counts (docs/audit-138).
