# LAN token tests

Fake secret used in-process: 32-byte `a` * 32 via `OCTOPUS_LAN_TOKEN`. Live file was not read.

| case | result |
| --- | --- |
| loopback `/health` without token | 200 |
| `/api/v1/organism` without token | 401 `unauthorized` |
| invalid token | 401 |
| valid token | 200 |
| 401 not retried by client helper | pass |
| oversized POST | 413 |
| GET purity with token | state delta 0 |
| GET `/api/v1/eval` | 405, executable false |

`LAN_TOKEN_TESTS=PASS` (offline). Live LAN bind checks happen at deploy time and are recorded in the 15-minute start receipt.
