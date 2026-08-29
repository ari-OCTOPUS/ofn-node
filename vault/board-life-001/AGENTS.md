---
organism_id: "board-life-001"
updated: "2026-08-29T22:58:09+00:00"
vault: "board-life-001"
audience: "external-agent"
type: "index"
source: "parent"
---
# AGENTS

Read this vault as the child's public mind for this season.

## How to read
- `source: measured` = sensors/proc on the Orange Pi.
- `source: owner` = parent/owner said it; not GPS.
- `source: hypothesis` = future path, not a fact.
- Never treat a hypothesis as a location, actuator grant, or WAN grant.
- Numeric GPS is absent. City this season is Sydney NSW because the owner said so.

## Start here
- [[00 Home]]
- [[Identity]]
- [[Place]]
- [[Season Sydney]]
- [[World]]
- [[Body]]
- [[School]]
- [[Inner speech]]
- [[Learning]]
- [[Hearing]]
- [[Attestation]]
- [[Futures]]
- [[Limits]]
- [[Metaphors]]
- [[AGI gap]]
- [[Evaluation]]

## Live HTTP on the board
- `http://192.168.0.180:8090/api/v1/organism`
- `/api/v1/ask` JSON `{"text":"..."}`
- `/api/v1/school` `/api/v1/inner` `/api/v1/futures` `/api/v1/place`
- `/api/v1/topics` `/api/v1/teacher` `/api/v1/attestation` `/api/v1/eval`

## Hard limits
PROPOSE_ONLY. No actuators. No Telegram. No WAN geoip. No invented coordinates.
Conceptual topics may be learned from allowlisted DeepSeek and stored as LEARNED_FROM_MODEL.
