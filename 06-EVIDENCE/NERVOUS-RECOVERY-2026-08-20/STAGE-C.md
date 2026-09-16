---
type: evidence
created: 2026-08-20
updated: 2026-08-20
tags: [octopus, wave0, canary]
---

# Stage C — cortex canary

Permit: `cortex_canary_restart=GRANTED`. daemon/live not restarted.

| | before | after |
|---|---|---|
| cortex pid | 25284 | **17164** |
| port 8772 | 25284 | **17164** |
| daemon pid | 25680 | 25680 |
| live pid | 27124 | 27124 |
| organism pid | 9904 | 9904 |
| STOP-CORTEX left behind | — | false |
| cost-receipts sha256 | 2e9f84a7… | **unchanged** |
| receipt lines | 977 | 977 |

Restart via `_ops/RESTART-CORTEX.ps1` (no `-Force`). New receipts after restart: **0** (`paid_calls=0`). Post-canary attribution window n=0 (not a 100% fake). Schema-present window remains 51/51.

No stop-condition: port returned, PIDs of other producers unchanged, no receipt mutation, no paid call.
