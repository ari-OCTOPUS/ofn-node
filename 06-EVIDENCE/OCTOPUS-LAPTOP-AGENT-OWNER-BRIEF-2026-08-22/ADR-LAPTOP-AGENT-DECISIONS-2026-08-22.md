---
type: decision
status: active
tags: [octopus, adr, laptop-agent, three-node, connector-first, 2026-08-22]
created: 2026-08-22
updated: 2026-08-22
owner: ari
source_of_truth: F:\backup
---

# ADR — Laptop Agent Decisions (2026-08-22)

## Decision lock (owner-signable)

| Domain | Decision | Execution condition |
|---|---|---|
| Similarweb Premium Connector | ADOPT | Tag every output as `estimate`, attach `evidence_id`, `captured_at`, `confidence`, and `valid_for` |
| GA4 / GSC / Ads | GAP | Until OAuth + owner signature: register only as `CONNECTOR-GAP`; no metric invention |
| Telegram Mini App | ADOPT (Read-Only First) | Same primary state machine and same run/event chain; parallel execution path forbidden |
| Telegram Payment | TRIAL (limited) | One business only and only with real auditable execution receipt |
| Three-node messaging | TRIAL (JetStream) | Inbox/Outbox + idempotency first; JetStream only when pass criteria are met |
| Sensorium Governance | ADOPT Shared Policy | Shared allowlist/policy with separate namespace boundaries |

## Governance invariants for this package

1. Runtime evidence outranks narrative and old notes.
2. Any datum without valid `evidence_id` or valid `source_type` is `unverified`.
3. Estimated market/traffic signals must include `confidence` and `valid_for`.
4. D1/D7 owner gates remain binding for irreversible actions.
5. SoT remains single-homed on `F:\backup`.
6. Connector-first is mandatory for external research; no invented numbers.
7. No external write/payment/contact/deploy without owner gate.

## JetStream TRIAL pass criteria

JetStream can be promoted from TRIAL only when all criteria pass:

1. At least two real independent consumers require replay.
2. Laptop-offline scenario causes real event-loss risk and Inbox/Outbox is insufficient.
3. Duplicate handling with `idempotency_key` is tested and verified.
4. Rollback is documented and tested (JetStream off without flow break).

Default until then: durable Inbox/Outbox + idempotent consumers.

## NODE-PACK intake and synthesis lock

- Required intake order: `Business Node` -> `Sensorium Node` -> `Laptop Node`.
- Each node pack must carry per-file inventory with SHA-256 digest.
- Final three-node synthesis remains locked until all three packs are received and hashed.
- Unknown data must stay `unknown`/`unverified`; no assumption fill-in.

## Scope note for tonight

- Active businesses: Master Painting, Ziman, Studio.
- Mining exists as the fourth canonical business but remains deferred.
- This ADR does not authorize mining work, WAVE0 hardware unlock, or paid external actions.

## Evidence references

- `F:\backup\06-EVIDENCE\OCTOPUS-LAPTOP-AGENT-OWNER-BRIEF-2026-08-22\OWNER-BRIEF.md`
- `F:\backup\07 - Knowledge\octopus\93-LAPTOP-AGENT-OWNER-BRIEF.md`
- `F:\backup\07 - Knowledge\octopus\01-BUSINESS-MAP-CANONICAL.md`
- `F:\backup\07 - Knowledge\octopus\90-SEASON-ROLLUP-2026-08-22.md`
- `F:\backup\06-EVIDENCE\OCTOPUS-HANDOFF-MERGE-2026-08-22\merged\CURRENT-TRUTH.md`
