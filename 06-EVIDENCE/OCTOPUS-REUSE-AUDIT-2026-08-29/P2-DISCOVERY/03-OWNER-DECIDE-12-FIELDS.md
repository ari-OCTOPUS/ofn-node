---
type: report
project: "[[04 - Architect System/architect/PROJECT]]"
status: ready
tags: [octopus, owner-decide, provenance]
created: 2026-08-29
updated: 2026-08-29
created_by: agent
language: fa
sources:
  - "[[06-EVIDENCE/OCTOPUS-REUSE-AUDIT-2026-08-29/P2-DISCOVERY]]"
  - "[[06-EVIDENCE/OCTOPUS-REUSE-AUDIT-2026-08-29/runtime-provenance-20260828T230743Z/owner_decision.p2]]"
---

# 03 — owner_decide twelve fields

```text
TWELVE_FIELDS_TOTAL=12
TWELVE_FIELDS_CANONICAL=0
TWELVE_FIELDS_AVAILABLE_UNVERIFIED=2
TWELVE_FIELDS_DERIVABLE_LOSSY=1
TWELVE_FIELDS_MISSING=9
LOCAL_MINTING_REJECTED=true
observed_at=2026-08-29T04:50:00Z
method=read_vault_ofn_plus_p2_snapshot
scope=this_host_only
```

## Two contracts

**Live command (this vault tree):**  
`POST /api/v1/decide` `{id, approve, confirmed_twice}` → `ApiApp._owner_decide` → `Node.owner_decide` → `outbox.approve_manual` + ledger `VERDICT`.  
`03 - Projects/OFN-Board/ofn/adapters/http_api.py:1284-1295`  
`03 - Projects/OFN-Board/ofn/node.py:3081-3137`

It does not import `OwnerDecision`, does not call `validate()`, does not mint hashes, does not call `witness_mint`.

**Card schema (138 spine snapshot only):**  
`DECISION_FIELDS` in `owner_decision.p2.py:59-62`. File **absent** from vault `ofn/adapters/`. Body on 138 at `6881337` per REUSE-MAP; this host: `body_not_on_this_host`.

`validate` is a module function, not `OwnerDecision.validate()`. It checks presence, SHA hex shape, expiry shape. It does **not** check `sha256(exact_payload)==payload_sha`.

## Field table

| Field | Type | Required | Canonical producer | Canonical store | Existing at decide | Provenance | May default | Missing behavior | Status |
|---|---|---|---|---|---|---|---|---|---|
| decision_id | str | yes | UNKNOWN | UNKNOWN | UNKNOWN | none | no | validate `decision_id: missing`; live path ignores | MISSING |
| run_id | str | yes | UNKNOWN | UNKNOWN (mesh run_id is another object) | UNKNOWN | none | no | `run_id: missing` | MISSING |
| lane | str | yes | UNKNOWN (doc: painting/ziman) | none; neighbor `tenant` | tenant present, lane UNKNOWN | CLAIM if mapped from tenant | no | `lane: missing` | MISSING |
| action | str | yes | enqueue `kind` / `Action.name` | `OutboxItem.kind` | `item.kind` | CLAIM that kind≡action | no | `action: missing` | AVAILABLE_UNVERIFIED |
| recipient_masked | str | yes | UNKNOWN; no masker | none | raw `to`/`target` sometimes | CLAIM if minted from raw | no | `recipient_masked: missing` | MISSING |
| exact_payload | str | yes | UNKNOWN at decide; later first of text\|caption\|message | payload dict ≠ this string | payload dict exists | first-wins is CLAIM | no | packet API refuses until approved | DERIVABLE_LOSSY |
| payload_sha | str 64hex | yes | intended sha256(exact_payload) | none at decide; `packet_sha256` after complete | UNKNOWN | three hash contracts CONTRADICTED | no | `payload_sha: missing` | MISSING |
| artifact_sha | str 64hex | yes | UNKNOWN | none | UNKNOWN | witness_mint uses `artifact_sha256` different name | no | `artifact_sha: missing` | MISSING |
| verdict_sha | str 64hex | yes | UNKNOWN | none; ledger VERDICT is another object | UNKNOWN | ledger event.hash ≠ this | no | `verdict_sha: missing` | MISSING |
| idempotency_key | str | yes | enqueue caller | `outbox.idem_key` scoped `{tenant}:{key}` | scoped key present | CLAIM scoped vs unscoped | no | enqueue fail-closed | AVAILABLE_UNVERIFIED |
| expires_at | str Z | yes | UNKNOWN | none on OutboxItem | UNKNOWN | other expires_at schemas CONTRADICTED | no | format error / missing | MISSING |
| rollback | str | yes | UNKNOWN | none | UNKNOWN | fixture invents a sentence | no | `rollback: missing` | MISSING |

## Per-field trust tags

| Field | CLAIM_OR_PROVENANCE | MINTED_OR_OBSERVED | TRUST_BOUNDARY | SIGNATURE_REQUIRED | FRESHNESS_REQUIRED | IDEMPOTENCY_ROLE | PII_CLASS |
|---|---|---|---|---|---|---|---|
| decision_id | CLAIM if minted at card time | would be MINTED | card assembler | no | no | none | UNKNOWN |
| run_id | would be PROVENANCE if bound | UNKNOWN | UNKNOWN | no | no | input to witness request_id | UNKNOWN |
| lane | CLAIM if tenant mapped | tenant OBSERVED | registry vs leg name | no | no | none | UNKNOWN |
| action | PROVENANCE of kind; CLAIM of name | OBSERVED | enqueue → owner | no | no | none | UNKNOWN |
| recipient_masked | CLAIM if from raw to | mask MINTED | contract forbids raw; packet returns raw → CONTRADICTED | no | no | none | masked vs raw PII |
| exact_payload | CLAIM of which bytes | dict OBSERVED | owner approves exact bytes | no | no | none | often PII |
| payload_sha | PROVENANCE after bytes fixed | MINTED | executor at send | no (hash) | no | approval also carries it in fake | hash of PII |
| artifact_sha | would be PROVENANCE | MINTED | witness/card | no | no | witness request_id | UNKNOWN |
| verdict_sha | CLAIM if ledger reused | UNKNOWN | policy → card | no | no | none | UNKNOWN |
| idempotency_key | PROVENANCE of outbox id | OBSERVED | item_id tenant prefix | no | no | UNIQUE enqueue | UNKNOWN |
| expires_at | CLAIM if reused | UNKNOWN | fake executor clock | no | YES in fake execute; NO in validate; NO in live decide | none | UNKNOWN |
| rollback | CLAIM if invented at approve | UNKNOWN | owner card | no | no | none | UNKNOWN |

## Hash contradiction

Three SHA objects exist and are not proven equal:

1. `OwnerDecision.payload_sha` = SHA-256 of `exact_payload` UTF-8 (`fake_executor.p2.py:171-172`).
2. `ManualPacket.sha256` = SHA-256 of JSON `{text,target,channels,meta}` (`manual_dispatch.py`).
3. `witness_mint` `payload_sha256` of caller `payload_bytes`.

## Binding rule

No local UUID, empty string, zero, or wall-clock stamp may stand in for a missing producer/witness value. Missing stays `UNKNOWN`. Schema expansion is a blocker, not a patch, in this phase.

`OWNER_DECISION_DATA_AVAILABLE_AT_APPROVAL=false` (`P2-DISCOVERY.md:20`).
