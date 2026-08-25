# GET purity proof (source + offline HTTP)

Invariant: `GET_REQUEST_STATE_DELTA == 0` when `OCTOPUS_GET_PURE=1`.

Cognitive state = events/episodes/outbox/identity counts and heads, memory receipts, decision evidence, and hashes of files the GET handler would write (`ORGANISM-PUBLIC.json`, `ATTESTATION.json`). Operational `/proc` reads and in-memory `STATE` copies are not cognitive writes.

| method | path | loopback | LAN | auth when token on | db read | db write | event write | identity write | file write | network | side_effect_free when GET_PURE=1 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| GET | /health | yes, no token | token required | loopback exempt | no | no | no | no | no | no | yes |
| GET | /api/v1/organism | token | token | yes | yes | no | no | no | no | no | yes |
| GET | /api/v1/episodes | token | token | yes | yes | no | no | no | no | no | yes |
| GET | /api/v1/self | token | token | yes | yes | no | no | no | no | no | yes |
| GET | /api/v1/world | token | token | yes | yes | no | no | no | no | no | yes |
| GET | /api/v1/utterance | token | token | yes | yes | no | no | no | no | no | yes |
| GET | /api/v1/growth | token | token | yes | yes | no | no | no | no | no | yes |
| GET | /api/v1/place | token | token | yes | yes | no | no | no | no | no | yes |
| GET | /api/v1/tools | token | token | yes | yes | no | no | no | no | no | yes |
| GET | /api/v1/development | token | token | yes | yes | no | no | no | no | no | yes |
| GET | /api/v1/lessons | token | token | yes | yes | no | no | no | no | no | yes |
| GET | /api/v1/school | token | token | yes | yes | no | no | no | no | no | yes |
| GET | /api/v1/inner | token | token | yes | yes | no | no | no | no | no | yes |
| GET | /api/v1/futures | token | token | yes | yes | no | no | no | no | no | yes |
| GET | /api/v1/season | token | token | yes | yes | no | no | no | no | no | yes |
| GET | /api/v1/topics | token | token | yes | yes | no | no | no | no | no | yes |
| GET | /api/v1/teacher | token | token | yes | yes | no | no | no | no | no | yes |
| GET | /api/v1/attestation | token | token | yes | yes | no | no | no | no | no | yes (read existing file only) |
| GET | /api/v1/eval | token | token | yes | no | no | no | no | no | no | N/A — 405, moved to POST |
| POST | /api/v1/eval | token | token | yes | yes | receipts if eval runs | no actuator | no | no | local cortex only | not GET; `executable=false`; WAVE0 |
| POST | /api/v1/ask | token | token | yes | yes | event/episode | yes | no | maybe public | local cortex | not GET; `executable=false` |

When `OCTOPUS_GET_PURE=0` (legacy), GET `/api/v1/organism` and nested views still call `enrich_snapshot` / `write_public_status` / health identity transitions. That path is compatibility-only and must stay off for the 15-minute soak.

Offline proof: `ofn.organism.tests.test_get_purity_and_lan.GetPurityAndLanTests.test_get_purity_zero_state_delta`.
