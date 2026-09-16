---
schema: octopus.owner-authorization.note.v1
token: OCTOPUS-HANDOFF-MERGE-2026-08-22
date: 2026-08-22
timezone: Australia/Sydney (UTC+10)
tags: [octopus, orangepi, handoff, owner-review, merge, equal-value]
---

# OWNER-AUTHORIZATION — Handoff ∪ OWNER_REVIEW merge (equal value)

**Owner decision (2026-08-22):** MERGE `LAPTOP-AGENT-HANDOFF` and `OWNER_REVIEW` narratives because **both have equal value**. Integrate into coherent current truth — **do not delete one**.

## Allowed
- Archive copies (copy, do not destroy) into `06-EVIDENCE/OCTOPUS-HANDOFF-MERGE-2026-08-22/archive/`
- Write merged docs dated 2026-08-22 preserving valuable content from BOTH
- Mark Aug17 FAIL gaps as **superseded** where live ABD+C receipts show PASS
- Optional Obsidian pointer

## Forbidden / still locked
- Unlock WAVE0 / actuators
- Open MQTT 1883
- `git add -A`
- Key export / rewrite
- Mutate Pi authority without a separate execute grant

## Live posture (must remain in merged truth)
- WAVE0: **KEEP_LOCKED**
- MQTT 1883: **CLOSED**
- `actuator_authority`: **NONE**
