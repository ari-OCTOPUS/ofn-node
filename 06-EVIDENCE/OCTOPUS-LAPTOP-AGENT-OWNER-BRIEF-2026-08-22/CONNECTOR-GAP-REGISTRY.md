---
type: registry
status: active
tags: [octopus, connector-gap, connector-first, owner-gates, 2026-08-22]
created: 2026-08-22
updated: 2026-08-22
owner: ari
---

# CONNECTOR-GAP Registry (owner-gated)

## Standard statuses

| Status | Meaning | Allowed action |
|---|---|---|
| `GAP_OPEN` | Gap identified, not yet owner-triaged | Record evidence only |
| `WAITING_OWNER_OAUTH` | Connector requires owner OAuth/login | No OAuth automation; wait |
| `WAITING_OWNER_SIGNATURE` | Owner sign-off required after credentials exist | No external action |
| `BLOCKED_POLICY_GATE` | Policy gate (D1/D7 or equivalent) blocks use | Keep proposal-only |
| `BLOCKED_TOS_OR_LICENSE` | ToS/license ambiguity or restriction | Stop and request verdict |
| `READY_FOR_RETEST` | Owner action complete; safe to re-probe read-only | Probe via connector only |
| `CLOSED` | Gap resolved and runtime-verified | Keep evidence and receipts |

## Locked GAP entries (mandatory)

| gap_id | connector | status | scope | reason | required owner action | gate |
|---|---|---|---|---|---|---|
| `CG-001` | Google Analytics 4 (GA4) | `WAITING_OWNER_OAUTH` | Master Painting / Ziman / Studio | API access exists but needs owner OAuth + property grants | OAuth consent and project/property mapping | D1/D7 |
| `CG-002` | Google Search Console (GSC) | `WAITING_OWNER_OAUTH` | Master Painting / Ziman / Studio | Search data API requires verified site ownership + owner OAuth | OAuth consent and verified property binding | D1/D7 |
| `CG-003` | Google Ads | `WAITING_OWNER_OAUTH` | Master Painting / Ziman / Studio | Ads API needs owner credentials/token + account linkage | OAuth consent and account approval | D1/D7 |

## Connector-first probe queue (non-gap, no invented figures)

These are not marked as gaps here; they are queued for evidence-first probes.

| connector | status | output policy |
|---|---|---|
| Similarweb Premium | `PENDING_RUNTIME_PROBE` | `estimate` + `evidence_id` + `captured_at` + `confidence` + `valid_for` |
| Statista | `PENDING_RUNTIME_PROBE` | fact/estimate label + evidence metadata |
| CB Insights | `PENDING_RUNTIME_PROBE` | fact/estimate label + evidence metadata |
| Realtime Finance Data | `PENDING_RUNTIME_PROBE` | fact/estimate label + evidence metadata |
| GitHub | `PENDING_RUNTIME_PROBE` | source-linked facts only |
| Hugging Face | `PENDING_RUNTIME_PROBE` | source-linked facts only |

## Hard rules

1. No connector output without `evidence_id`.
2. Any missing/invalid `source_type` => `unverified`.
3. Similarweb and other estimated data cannot be promoted to fact without explicit verification path.
4. No external write/login/payment/contact from this registry without owner gate.

## Evidence references

- `F:\backup\06-EVIDENCE\OCTOPUS-LAPTOP-AGENT-OWNER-BRIEF-2026-08-22\OWNER-BRIEF.md`
- `F:\backup\06-EVIDENCE\OCTOPUS-LAPTOP-AGENT-OWNER-BRIEF-2026-08-22\ADR-LAPTOP-AGENT-DECISIONS-2026-08-22.md`
- `F:\backup\07 - Knowledge\octopus\93-LAPTOP-AGENT-OWNER-BRIEF.md`
