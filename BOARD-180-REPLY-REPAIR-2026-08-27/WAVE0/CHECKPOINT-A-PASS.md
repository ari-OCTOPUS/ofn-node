# Checkpoint A PASS
**closed:** 2026-08-27 11:48 AEST
**by:** PC (Lead Architect)
**scope:** durable reply repair cycle only
**not included:** systemd live-enable, Fresh E2E, PERSISTENT_GREEN, Telegram, cash

## Evidence
- Official v2 task: 5834522f-a8c2-43b5-91e2-42c93ba89d16 claimed once by 180 at 01:45:11Z, completed 01:45:55Z
- Durable reply: 11bd33fb-9f54-562f-80dc-a25b1919ed7f
- response_sha256: 7322ddbc47b8792f2c62f1cc53592d1f84b9d5872151838b22c5d9110d237e0f
- TRANSMIT_HANDED, transmit_calls=1, state=INPUT_PROCESSED
- 138 ACK: 7dc09d56-a524-497c-b9ba-ffe99a1db625 (in_reply_to=11bd33fb) ingested by 180
- 182 VERDICT=confirmed (independent hash of 4 WAVE0 files + settle-5834522f 11:47)
- WAVE0 JSON sha: 512030a08e3a633bb9aaafad2b32a64ecba27e79f2d552debfb739dd161c3bcd
- outbox sha: bac40b1e7923cb67656ecc8c0163f9f3df1e2b4479293e3f5ab55285e1cd6a73
- PC_worker reference 8fe57d68 25/25 (not deployed)

## Superseded
- 30f60773 verify-only / completed / no re-claim
- b4893759 OLD_LOST_REPLY; ACK 8fb28ba3 was of that old reply only

## Next
Checkpoint B / Wave 1: Fresh E2E, zero manual sessions, HOLD stays until that PASS, then PERSISTENT_GREEN.
