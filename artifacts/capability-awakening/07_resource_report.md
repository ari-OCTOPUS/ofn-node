# Controlled growth resource report

Canary window: `2026-08-25T13:18:07Z` to `2026-08-25T13:33:08Z`

- Minimum RAM available: `2171404 KiB`
- Required RAM minimum: `358400 KiB`
- Minimum root-disk available: `7015362560 bytes` (`6.53 GiB`)
- Required disk minimum: `5368709120 bytes` (`5 GiB`)
- Maximum root use: `88.56%`
- Required root maximum: `<92%`
- Maximum SoC temperature: `29615 mC`
- Thermal trip threshold: `105000 mC`
- Resource violations: `0`
- Dependency installs: `0`
- New models: `0`
- Unbounded new processes: `0`
- Heartbeat interval changes: `0`
- Large artifacts: `0`

The checkpoint watcher ran as PID `41212` beneath `timeout --signal=TERM 3600s`; both process presence and heartbeat freshness were checked throughout the canary. The watcher quarantines/reports invalid receipts and does not terminate monitoring for receipt-shape errors.

The local-hypothesis inference load was not exercised live in this two-experiment canary. Offline tests bound that path to exactly five loopback calls, four output tokens per call, and eight seconds per call.

RESOURCE_STATUS: `PASS`
