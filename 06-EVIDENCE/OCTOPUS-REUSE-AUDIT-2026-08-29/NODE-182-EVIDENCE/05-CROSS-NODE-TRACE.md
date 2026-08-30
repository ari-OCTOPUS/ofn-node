---
type: report
project: "[[04 - Architect System/architect/PROJECT]]"
status: ready
tags: [octopus, node-182, trace, edge-6, edge-8]
created: 2026-08-29
updated: 2026-08-29
created_by: agent
language: fa
sources:
  - "[[06-EVIDENCE/OCTOPUS-L191-FINDINGS-2026-08-28]]"
  - "[[06-EVIDENCE/OCTOPUS-REUSE-AUDIT-2026-08-29/P2-DISCOVERY/08-EDGE6-CAUSAL-TRACE]]"
  - "[[06-EVIDENCE/OCTOPUS-TELEGRAM-WEBAPP-PHASE0-2026-08-29]]"
  - "[[06-EVIDENCE/OCTOPUS-REUSE-AUDIT-2026-08-29/MISSING-EDGES]]"
---

# 05 — Cross-node trace

```text
RUN=run-spine-138-snap-20260828T005835Z
PROPOSAL=proposal-950f8d0e
SOURCE_HASH_PREFIX=950f8d0e
EDGE6_LAST_VERIFIED_STAGE=registry_projection
EDGE6_FIRST_MISSING_STAGE=proposal_enqueue
EDGE8_FOR_RUN=MISSING_FOR_RUN
this_session_ssh=0
observed_at=2026-08-29T05:30:00Z
method=prior_ssh_artifacts_plus_docs
scope=this_host_only
truth_status=DOCUMENTED
```

IDs: source hash `950f8d0e02e6dc89…`; proposal file sha `ddd5b11c…`; registry prefix `cff7fc6d`; proposal mtime **07:21:30Z**.

## EDGE table (L191 §5) vs this-run

| edge | name | L191 status | 182 involvement | source | observed_at | truth_status |
|---|---|---|---|---|---|---|
| EDGE-1 | 138 snapshot → 180 inbox | PROVEN | none | L191:166 | 2026-08-28 | DOCUMENTED |
| EDGE-2 | wake binding | PROVEN (ACK) | none | L191:167 | 2026-08-28 | DOCUMENTED |
| EDGE-3 | inbox claim on 180 | PROVEN | none | L191:168 | 2026-08-28 | DOCUMENTED |
| EDGE-4 | cognition predict | PROVEN | none | L191:169 | 2026-08-28 | DOCUMENTED |
| EDGE-5 | build `proposal.v1` | PROVEN | none (180 producer) | L191:170 | 2026-08-28 07:21:30Z | DOCUMENTED |
| EDGE-6 | 180 outbox send/drain → 138 | **PROVEN_BROKEN** | none (never reached) | L191:171; P2 08 | 2026-08-28 | DOCUMENTED |
| EDGE-7 | mint on 138 | MISSING_FOR_RUN | downstream | L191:172 | 2026-08-28 | DOCUMENTED |
| EDGE-8 | witness 182 for this run | **MISSING_FOR_RUN** | would be 182 | L191:173; P2 08:71 | 2026-08-28 | DOCUMENTED |
| EDGE-9 | owner receipt consume | ARMED on PC, unused | not 182 | L191:174 | 2026-08-28 | DOCUMENTED |
| EDGE-10..14 | executor / customer / settle | GATED HOLD_EXTERNAL | no | L191:175 | 2026-08-28 | DOCUMENTED |

## Same-run stage table (P2 08)

| Stage | Status | Artifact | Producer | Consumer | ts | run correlation | source | truth_status |
|---|---|---|---|---|---|---|---|---|
| proposal | PRESENT_VERIFIED | `proposal-950f8d0e.json` | 180 | none for drain | 07:21:30Z | snap run | P2 08:61 | DOCUMENTED |
| OwnerDecision | MISSING | — | — | — | — | — | P2 08:62 | DOCUMENTED |
| OFN owner item | MISSING | no `950f8d0e` row | — | decide | — | — | P2 08:63 | DOCUMENTED |
| owner receipt file | PRESENT_UNVERIFIED; N/A as effect | 191 AUTH | owner | unused | — | run name | P2 08:64 | DOCUMENTED |
| enqueue | MISSING | no `replies/pending` / `meta/spine-proposal-*` | — | — | — | — | P2 08:66 | DOCUMENTED |
| transmit attempt | MISSING | seq 6006–6017 = wake/snapshot | — | — | — | not proposal | P2 08:67 | DOCUMENTED |
| effect | MISSING | HOLD_EXTERNAL | — | — | — | — | P2 08:68 | DOCUMENTED |
| ACK | MISSING for proposal | wake ACKs only | 138 transport | 180 | 00:59–01:01 | not proposal | P2 08:69 | DOCUMENTED |
| 630c5060 | CONTRADICTED as this-run | notify envelope | 138 | — | 07:19:39Z | `425f4012-…` | P2 08:70 | CONTRADICTED |
| wr_950f8d0e | STRUCTURAL source-hash; not EDGE-8 | 182 file | 182 | 138 notify | 07:19:39Z **before** proposal | source hash, no proposal/effect IDs | P2 08:71 | DOCUMENTED |
| registry | PRESENT_VERIFIED | `live_spine_run.json` | 180 | observers | 07:21:30Z | snap run | P2 08:72 | DOCUMENTED |
| frontend | NOT_OBSERVED for this proposal | — | — | — | — | 191 cards = ziman-gallery | P2 08:73 | DOCUMENTED |

```text
TRACE_LAST_VERIFIED_STAGE=registry_projection
TRACE_FIRST_MISSING_STAGE=proposal_enqueue
```

Mechanism of 07:21 no-persist: `UNKNOWN` (no audit line; inbound already `reply_acked`) — P2 08:78.

## 182-specific trace facts

| claim | value | source | method | observed_at | scope | truth_status |
|---|---|---|---|---|---|---|
| 182 saw this proposal on the wire | NOT_OBSERVED / MISSING | EDGE-6 broken before 182 | inference from L191+P2 08 | 2026-08-28 | documented_remote | DOCUMENTED |
| 182 issued wr_950f8d0e | YES, source-hash STRUCTURAL | P2 08:71 | prior artifacts | 2026-08-28 07:19:39Z | documented_remote | DOCUMENTED |
| that file closes EDGE-8 | NO | missing proposal/effect IDs; earlier than proposal | P2 08 | 2026-08-28 | documented_remote | DOCUMENTED |
| TCP 138↔182 at L191 probe | NONE_TO_180_OR_182 | L191:81 | prior SSH | 2026-08-28T11:48-11:59Z | documented_remote | DOCUMENTED |
| MISSING-EDGES E4 | 180 proposal → 182 witness → OwnerDecision still open | MISSING-EDGES.md:56-64 | doc | 2026-08-29 | this_host_only | DOCUMENTED |
| MISSING-EDGES E3 | dispatcher IDs → empty/unresolved witness (`04af67d5`, `e19fe76b`) | MISSING-EDGES.md:45-54 | doc | 2026-08-29 | this_host_only | DOCUMENTED |

## Do not close this run with

1. Registry / `live_spine_run.json`.
2. Transport ACK (wake/snapshot or otherwise).
3. `630c5060` (wrong `run_id`).
4. `wr_950f8d0e` (source-hash STRUCTURAL before proposal).
5. 191 owner-receipt file (not POST decide; unused).
6. L977 dry-run or seq 6006–6017 as EDGE-6.

```text
REGISTRY_IS_EFFECT_RECEIPT=NO
ACK_IS_EFFECT_RECEIPT=NO
```
