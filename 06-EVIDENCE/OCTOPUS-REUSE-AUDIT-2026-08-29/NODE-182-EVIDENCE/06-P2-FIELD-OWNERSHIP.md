---
type: report
project: "[[04 - Architect System/architect/PROJECT]]"
status: ready
tags: [octopus, node-182, p2, fields]
created: 2026-08-29
updated: 2026-08-29
created_by: agent
language: fa
sources:
  - "[[06-EVIDENCE/OCTOPUS-REUSE-AUDIT-2026-08-29/runtime-provenance-20260828T230743Z/owner_decision.p2]]"
  - "[[06-EVIDENCE/OCTOPUS-REUSE-AUDIT-2026-08-29/P2-DISCOVERY/03-OWNER-DECIDE-12-FIELDS]]"
  - "[[06-EVIDENCE/OCTOPUS-REUSE-AUDIT-2026-08-29/P2-DISCOVERY/field-provenance]]"
---

# 06 — P2 field ownership (182)

```text
P2_FIELDS_TOTAL=12
P2_FIELDS_OWNED_BY_182=NONE
P2_FIELDS_MISSING=decision_id,run_id,lane,action,recipient_masked,exact_payload,payload_sha,artifact_sha,verdict_sha,idempotency_key,expires_at,rollback
LOCAL_MINTING=FORBIDDEN
observed_at=2026-08-29T05:30:00Z
method=read_owner_decision_p2_plus_p2_discovery_03
scope=this_host_only
```

Canonical names from `owner_decision.p2.py:59-62` (`DECISION_FIELDS`):

`decision_id` `run_id` `lane` `action` `recipient_masked` `exact_payload` `payload_sha` `artifact_sha` `verdict_sha` `idempotency_key` `expires_at` `rollback`

182 **must not** mint fields owned by the 180 producer or by 138. No signed grant gives 182 any of the twelve. Witness-adjacent hashes use **different names** (`artifact_sha256`, `payload_sha256`) and are not substitutes.

## Per-field (182 vantage)

| field | 182 may mint | 180 producer | 138 | 182 role if any | status | source | method | observed_at | truth_status |
|---|---|---|---|---|---|---|---|---|---|
| decision_id | NO | no signed owner | card assembler CLAIM | none | MISSING | P2 03:47 | file_read | 2026-08-29 | DOCUMENTED |
| run_id | NO | spine run string on EDGE-5 | local mint would be REJECT as 182 truth | input to witness request_id (not 182-owned) | MISSING | P2 03:48; witness_mint | merge | 2026-08-29 | DOCUMENTED |
| lane | NO | CLAIM if mapped from tenant | neighbor `tenant` | none | MISSING | P2 03:49 | file_read | 2026-08-29 | DOCUMENTED |
| action | NO | enqueue `kind` CLAIM | `OutboxItem.kind` | none | AVAILABLE_UNVERIFIED on 138 only | P2 03:50 | file_read | 2026-08-29 | DOCUMENTED |
| recipient_masked | NO | UNKNOWN; no masker | raw `to` sometimes CONTRADICTED | none | MISSING | P2 03:51 | file_read | 2026-08-29 | DOCUMENTED |
| exact_payload | NO | proposal bytes CLAIM | later first-wins CLAIM | none | DERIVABLE_LOSSY elsewhere | P2 03:52 | file_read | 2026-08-29 | DOCUMENTED |
| payload_sha | NO | intended sha256(exact_payload) | ManualPacket.sha256 ≠ this | 138 witness `payload_sha256` ≠ this | MISSING | P2 03:53,78-83 | file_read | 2026-08-29 | CONTRADICTED (three hashes) |
| artifact_sha | NO | UNKNOWN | witness_mint `artifact_sha256` different name | trust_boundary “witness/card” is CLAIM not ownership | MISSING | P2 03:54; field-provenance.csv | file_read | 2026-08-29 | DOCUMENTED |
| verdict_sha | NO | UNKNOWN | ledger VERDICT ≠ this | none | MISSING | P2 03:55 | file_read | 2026-08-29 | DOCUMENTED |
| idempotency_key | NO | mesh reply key other plane | OFN `{tenant}:{key}` | 182 worker has its own mid key — **not** this field | AVAILABLE_UNVERIFIED on 138 only | P2 03:56; P2 06 | merge | 2026-08-29 | DOCUMENTED |
| expires_at | NO | UNKNOWN | none on OutboxItem | envelope `expires_at` on mesh msgs is another object | MISSING | P2 03:57; obs182 hit | merge | 2026-08-29 | DOCUMENTED |
| rollback | NO | UNKNOWN | fixture invents a sentence | none | MISSING | P2 03:58 | file_read | 2026-08-29 | DOCUMENTED |

```text
P2_FIELDS_OWNED_BY_182=NONE
P2_FIELDS_MISSING=decision_id,run_id,lane,action,recipient_masked,exact_payload,payload_sha,artifact_sha,verdict_sha,idempotency_key,expires_at,rollback
```

`action` and `idempotency_key` are AVAILABLE_UNVERIFIED **on 138 enqueue**, not owned or minted by 182.

## What 182 may emit (not P2 fields)

| object | names | source | truth_status |
|---|---|---|---|
| STRUCTURAL witness record | request_id, artifact_sha256, payload_sha256, pass_type | witness_mint.p2.py | REPO_VERIFIED (138 module; 182 live emit UNKNOWN this session) |
| mesh witness_response | verdict, may_authorize, falsification_attempts | worker copy | DOCUMENTED |
| claim lease | claimed_by_node=182, lease_expires_at | worker copy | DOCUMENTED |

Embedding those as OwnerDecision values is REJECT.

## Binding rule

No local UUID, empty string, zero, or wall-clock stamp on 182 may stand in for a missing 180/138 producer value. Missing stays `UNKNOWN`. Schema expansion is a blocker, not a 182 patch.

Open producer question (P2 00 / P2-DISCOVERY.md) remains for: `run_id`, `artifact_sha`, `verdict_sha`, `recipient_masked`, `expires_at`, `rollback`. **182 is not the answer** until a signed registry says otherwise.
