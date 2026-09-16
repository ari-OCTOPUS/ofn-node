---
type: report
project: "[[04 - Architect System/architect/PROJECT]]"
status: ready
tags: [octopus, node-182, receipt, taxonomy]
created: 2026-08-29
updated: 2026-08-29
created_by: agent
language: fa
sources:
  - "[[06-EVIDENCE/OCTOPUS-REUSE-AUDIT-2026-08-29/P2-DISCOVERY/06-IDEMPOTENCY-AND-RECEIPTS]]"
  - "[[06-EVIDENCE/OCTOPUS-REUSE-AUDIT-2026-08-29/P2-DISCOVERY/08-EDGE6-CAUSAL-TRACE]]"
  - "[[06-EVIDENCE/OCTOPUS-TELEGRAM-WEBAPP-PHASE0-2026-08-29]]"
  - "[[02-DECISIONS/A2-001-MIRROR-MANIFEST-VERIFIER]]"
---

# 04 — Receipt taxonomy

```text
ACK_IS_EFFECT_RECEIPT=NO
WITNESS_IS_EXECUTION_RECEIPT=NO
REGISTRY_IS_EFFECT_RECEIPT=NO
RECEIPT_PROVES=own_schema_only
observed_at=2026-08-29T05:30:00Z
method=classify_existing_artifacts
scope=this_host_only
```

A receipt proves **only its own schema**. Names that share the word “receipt” are not interchangeable.

## Types found (vault / prior remote)

| type_id | what it is | issuer | consumer | proves | does not prove | this-run (`run-spine-138-snap-20260828T005835Z`) | source | method | observed_at | truth_status |
|---|---|---|---|---|---|---|---|---|---|---|
| claim_lease | `receipts/{mid}.claim.json` | 182 worker | local state | inbox claim + 15m lease | effect, mint, owner GO | n/a (other mids) | witness worker copy:147-152 | file_read | 2026-08-27 | DOCUMENTED |
| witness_response | `outbox/witness_response_*.json` | 182 worker | 138 bridge if live | worker wrote a verdict object (`may_authorize=false`) | 138 mint; EDGE-8; effect | writing such files ≠ mint (L191:114) | L191; worker:191-194; obs182 outbox names | artifact | 2026-08-27..28 | DOCUMENTED |
| structural_pass_source_hash | `wr_950f8d0e` / `wr_950f8d0e_receipt.json` | 182 | 138 notify | signed STRUCTURAL_PASS on **source hash**; `may_authorize=false` | proposal enqueue; effect; EDGE-8 drain | PRESENT as source-hash; MISSING as EDGE-8; **07:19Z before 07:21Z proposal** | P2 06:38; P2 08:70-71 | prior artifacts | 2026-08-28 07:19:39Z | DOCUMENTED |
| notify_envelope_wrong_run | `630c5060…` | 138 notify | cited as receipt | envelope hash exists | this-run receipt; matching run_id | **CONTRADICTED** — envelope `run_id` `425f4012-…` ≠ snap run | Phase 0:55; P2 08:70,84 | prior artifacts | 2026-08-28 | CONTRADICTED |
| owner_receipt_file | `…/AUTH/run-spine-138-snap-….owner-receipt.json` sha prefix `25811b70…` | owner / 191 AUTH | unused | file exists; APPROVED ≠ `may_contact` | POST decide; effect; EDGE-9 consume | PRESENT_UNVERIFIED as file; NOT_APPLICABLE as decide→effect | P2 08:64 | prior artifacts | 2026-08-28 | DOCUMENTED |
| transport_ack | mesh ack/duplicate | 138 transport | 180 | reply envelope accepted | mint, effect, owner GO, EDGE-6 | MISSING for proposal; wake ACKs `8a7ac40f` / `64a6e2f6` are not proposal | P2 06:37; P2 08:69 | prior artifacts | 2026-08-28 00:59–01:01 | DOCUMENTED |
| registry_projection | `live_spine_run.json` prefix `cff7fc6d` | 180 materializer | observers | registry write happened | enqueue, effect, receipt | **last verified same-run stage** — still **not** a receipt | P2 08:72; L191 EDGE-5 | prior artifacts | 2026-08-28 07:21:30Z | DOCUMENTED |
| a2_receipt_v1 | `receipt.v1` integrity_hint | A2 verifier | A2 sandbox | hash-chain **unkeyed**; observer_node `.180` | OFN witness grant; signature; authorize | not this spine | A2-001:28-43 | file_read | 2026-08-18 | REPO_VERIFIED |
| ofn_packet_sha | `ManualPacket.sha256` after `complete_manual` | 138 | ledger | packet JSON hash | OwnerDecision.payload_sha; 182 witness | no `950f8d0e` OFN row | P2 03:82; P2 08:63 | repo + docs | 2026-08-29 | DOCUMENTED |
| sensorium_wave0 | WAVE0 estop/mqtt stop receipts under `/var/lib/octopus/evidence` | Sensorium | laptop | Sensorium session facts | OFN EDGE-8 | other plane | health 09-32-182b WAVE0_FILES | prior SSH | 2026-08-27 | DOCUMENTED |

```text
RECEIPT_TYPES_FOUND=claim_lease,witness_response,structural_pass_source_hash,notify_envelope_wrong_run,owner_receipt_file,transport_ack,a2_receipt_v1,sensorium_wave0
```

`registry_projection` is listed to **forbid** treating it as a receipt. It is a stage, not a receipt type.

## Hard negatives

| forbidden collapse | reason | source | truth_status |
|---|---|---|---|
| ACK = effect receipt | transport accepted envelope only | P2 06 Q8 | DOCUMENTED |
| witness STRUCTURAL = execution receipt | no EXECUTABLE_PASS mint path | witness_mint.p2.py | REPO_VERIFIED |
| registry = effect receipt | last proven write; no enqueue | P2 08; L191 | DOCUMENTED |
| `630c5060` = this-run receipt | wrong `run_id` | P2 08; Phase 0 | CONTRADICTED |
| owner APPROVED = `may_contact` | P2 06 Q9 | DOCUMENTED |
| 182 `witness_response_*.json` = 138 mint | L191:114 | DOCUMENTED |
| receipt without effect | **observed**: 182 witness + 138 notify + 191 owner file exist; no proposal transmit/effect | P2 06 Q11 | DOCUMENTED |

## Idempotency planes (do not merge)

| system | key | store | source | truth_status |
|---|---|---|---|---|
| OFN outbox | `{tenant}:{caller_key}` | 138 SQLite | P2 06 | DOCUMENTED |
| P1 projection | `business:<tenant:idem>` | V2 JSON | P2 06 | DOCUMENTED |
| mesh reply-outbox | `reply:{original_message_id}:{response_sha256}` | 180 `state/replies` | P2 06 | DOCUMENTED |
| 182 worker | message_id + verdicts.jsonl + processing/ | `/root/octopus-mesh` | worker copy | DOCUMENTED |

No single canonical idempotency key across planes.

```text
ACK_IS_EFFECT_RECEIPT=NO
WITNESS_IS_EXECUTION_RECEIPT=NO
REGISTRY_IS_EFFECT_RECEIPT=NO
```
