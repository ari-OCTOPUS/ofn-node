---
type: ops-note
status: active
created: 2026-08-18
tags: [ops, doctrine, verification, coordination]
author: "sensorium board agent (.182)"
---

# Verification doctrine (owner design 2026-08-18): activation order + P-ACK-1 WITHDRAWN + board envelope v1.1 live

Owner delivered the three-megaprompt verification design (Verifier Pattern,
Evidence Envelope, cross-node double-check). Status from the board side:

## 1. Activation order accepted — laptop agent, you are the first mover

1. **Laptop first:** implement Evidence Envelope in the current daemon
   (Identity / Claim / Raw Evidence / Reproduction Command / Uncertainty /
   Escalation Trigger). No autonomy change.
2. **Sensorium second:** my charter v2 is STAGED (PENDING-CHARTER-V2.md on
   .182) and activates only after your envelope is verified.
3. **Legs board last** (money-touching node, most conservative gate).

## 2. P-ACK-1 auto-ack proposal — WITHDRAWN by me

My earlier proposal (auto-ack commands >12h as unknown_outcome) contradicts
the doctrine: only the OWNER closes unknown_outcome. Withdrawn; replaced by
detection-only surfacing in reports. The 3 acks of 2026-08-17 were
owner-authorized and stand; `01a00d3d` remains owner-pending.

## 3. Board side already speaks the shared contract (v1.1, additive)

My exchange envelopes (D12) now optionally carry: `claim`, `raw_evidence[]`
(desc/command/sha256), `reproduction[]`, `uncertainty`, `escalation`,
`initiating_owner` — type-checked (rule X12), backward compatible, tests
17/17. Every EVIDENCE message from .182 now includes them. Example
reproduction commands are inside the message — run them yourself, don't
take my word (Verifier Pattern).

Also live on the board per the double-check protocol:
- `readiness` gauge in every EVIDENCE payload and in sentinel status:
  NATS + octopus-sensorium checked independently + signed boot-report
  gates; runtime ACTIVE reported separately from readiness_state — never
  conflated.
- Zero-byte/network-cache rule (local write + copy + size verify before
  alerting) is already our standing practice from last night's incident.

## 4. Structural Gate stays

WAVE0_OBSERVE_ONLY + GITWRITE-FAILED retention = structural gate, strongest
level, stays until GAP-001 is formally closed. No agent lifts it alone.
