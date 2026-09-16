---
type: report
project: "[[04 - Architect System/architect/PROJECT]]"
status: ready
tags: [octopus, node-182, witness, contract]
created: 2026-08-29
updated: 2026-08-29
created_by: agent
language: fa
sources:
  - "[[06-EVIDENCE/OCTOPUS-REUSE-AUDIT-2026-08-29/runtime-provenance-20260828T230743Z/witness_mint.p2]]"
  - "[[06-EVIDENCE/BOARD-180-REPLY-REPAIR-2026-08-27/oracle-182/isolated-once/octopus_witness_worker]]"
  - "[[06-EVIDENCE/OCTOPUS-REUSE-AUDIT-2026-08-29/P2-DISCOVERY]]"
  - "[[06-EVIDENCE/OCTOPUS-L191-FINDINGS-2026-08-28]]"
---

# 03 — Witness contract

```text
WITNESS_REQUEST_PRODUCER=DISPUTED
WITNESS_RESPONSE_CONSUMER=138
WITNESS_IS_EXECUTION_RECEIPT=NO
ACK_IS_EFFECT_RECEIPT=NO
DRAFT11_REQUIRED=UNKNOWN
LOCAL_MINTING=FORBIDDEN
observed_at=2026-08-29T05:30:00Z
method=read_snapshots_plus_prior_docs
scope=this_host_only
```

Two witness machines exist. They are **not** the same contract.

## Machine A — 138 `witness_mint` (STRUCTURAL only)

| item | value | source | method | observed_at | scope | truth_status |
|---|---|---|---|---|---|---|
| schema | `witness_request.v1` | witness_mint.p2.py:40 | file_read | 2026-08-28 snapshot | this_host_only | REPO_VERIFIED |
| store | `witness_requests.jsonl` | same:41 | file_read | same | this_host_only | REPO_VERIFIED |
| pass minted | `STRUCTURAL_PASS` only | same:10-21,121 | file_read | same | this_host_only | REPO_VERIFIED |
| `EXECUTABLE_PASS` | name exists; **no mint path** | same:16-21,45-46 | file_read | same | this_host_only | REPO_VERIFIED |
| id | SHA-256 of `run_id \x1f artifact_sha \x1f payload_sha \x1f policy \x1f schema` | same:60-74 | file_read | same | this_host_only | REPO_VERIFIED |
| fields written | request_id, run_id, artifact_sha256, payload_sha256, policy_version, schema_version, pass_type, created_at | same:113-123 | file_read | same | this_host_only | REPO_VERIFIED |
| sends | nothing | docstring:29 | file_read | same | this_host_only | REPO_VERIFIED |
| as canonical 182 truth | REJECT | P2-DISCOVERY.md:68-70 | doc | 2026-08-29 | this_host_only | DOCUMENTED |

`artifact_sha256` / `payload_sha256` are **not** OwnerDecision `artifact_sha` / `payload_sha`. Three hash objects remain unproven-equal (P2 03).

## Machine B — 182 mesh worker (isolated copy)

| item | value | source | method | observed_at | scope | truth_status |
|---|---|---|---|---|---|---|
| role label | lab-witness / independent_witness; `may_authorize=false` | octopus_witness_worker.py:3-4 | file_read | 2026-08-27 copy | this_host_only | DOCUMENTED |
| accepted types | `verification_task` / `witness_request` / `observation` only | same:5-6 | file_read | same | this_host_only | DOCUMENTED |
| rejects | generic tasks; never claims ack/nack control plane | same:6-7 | file_read | same | this_host_only | DOCUMENTED |
| claim receipt | `receipts/{mid}.claim.json` lease 15 min | same:147-152 | file_read | same | this_host_only | DOCUMENTED |
| response file | `outbox/witness_response_{mid[:8]}.json` | same:191-194 | file_read | same | this_host_only | DOCUMENTED |
| default verdict | `unresolved`; `may_authorize: False` | same:174-189 | file_read | same | this_host_only | DOCUMENTED |
| send | `octomesh_agent_bridge.py complete` → `reply_status==ack` | same:199-211 | file_read | same | this_host_only | DOCUMENTED |
| ACK meaning | transport/bridge accepted reply | same + P2 06 | merge | 2026-08-27..29 | this_host_only | DOCUMENTED |
| commander fail | `COMMANDER_UNAVAILABLE_SAFE_HOLD`; no self-promotion | same:217-222 | file_read | same | this_host_only | DOCUMENTED |
| live bytes == this copy | UNKNOWN | this pack | no hash | 2026-08-29 | this_host_only | UNKNOWN |

Worker ACK is **not** OFN effect, **not** EDGE-8 closure, **not** owner GO.

## Producer / consumer (disputed)

| direction | who | source | method | observed_at | truth_status |
|---|---|---|---|---|---|
| intended request producer (P2 prose) | 180 producer **before** card / enqueue | P2-DISCOVERY.md:73-79 | doc | 2026-08-29 | DOCUMENTED (proposal, unimplemented) |
| module that can mint request locally | 138 `witness_mint` | witness_mint.p2.py | file_read | 2026-08-28 | REPO_VERIFIED |
| documented inbox producer to 182 | 138 `sender_node` on `verification_task` | obs182_extract.json hits | artifact | 2026-08-27T01:52:35Z | DOCUMENTED |
| wr_950f8d0e issuer | 182 (source-hash STRUCTURAL_PASS) | P2 08:71 | prior artifacts | 2026-08-28 07:19:39Z | DOCUMENTED |
| wr_950f8d0e request producer | UNKNOWN (before proposal 07:21) | P2 08 | prior artifacts | 2026-08-28 | UNKNOWN |
| response consumer | 138 notify | P2 08:71 | prior artifacts | 2026-08-28 | DOCUMENTED |

```text
WITNESS_REQUEST_PRODUCER=DISPUTED
WITNESS_RESPONSE_CONSUMER=138
```

Disputed because: P2 wants 180 to register the request; 138 can mint STRUCTURAL locally; live 182 inbox shows 138-origin `verification_task`; the only same-prefix witness for `950f8d0e` predates the proposal and has no signed producer field in vault docs.

## draft-11

| item | value | source | method | observed_at | scope | truth_status |
|---|---|---|---|---|---|---|
| string `draft-11` / `DRAFT-11` / `draft_11` in 07 Knowledge | 0 | rg | 2026-08-29 | this_host_only | NOT_FOUND |
| same in 08-PLANS | 0 | rg | 2026-08-29 | this_host_only | NOT_FOUND |
| same in 02-DECISIONS | 0 | rg | 2026-08-29 | this_host_only | NOT_FOUND |
| same in agent-prompts | 0 | rg | 2026-08-29 | this_host_only | NOT_FOUND |
| reuse-audit mentions | only “string absent / UNKNOWN” | P2 00, 02, contradictions.csv CON-DRAFT11 | file_read | 2026-08-29 | this_host_only | DOCUMENTED |
| prior owner law still binding | UNKNOWN | absence ≠ repeal | merge | 2026-08-29 | this_host_only | UNKNOWN |

```text
DRAFT11_REQUIRED=UNKNOWN
```

If still valid, pre-draft-11 binding is reject. This pack does not invent a draft-11 body.

## Fail-closed rules already stated (not implemented here)

| rule | source | truth_status |
|---|---|---|
| missing 182 → P2 RED fail-closed | P2 02:89 | DOCUMENTED (proposed, not implemented) |
| local `witness_mint` inside `owner_decide` REJECT | P2-DISCOVERY.md:68-70 | DOCUMENTED |
| STRUCTURAL ≠ EXECUTABLE | witness_mint.p2.py | REPO_VERIFIED |
| 182 must not mint 180/138 OwnerDecision fields | this pack + P2 03 | DOCUMENTED |

```text
WITNESS_IS_EXECUTION_RECEIPT=NO
ACK_IS_EFFECT_RECEIPT=NO
```
