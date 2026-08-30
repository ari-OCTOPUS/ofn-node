---
type: report
project: "[[04 - Architect System/architect/PROJECT]]"
status: ready
tags: [octopus, edge-6, causal]
created: 2026-08-29
updated: 2026-08-29
created_by: agent
language: fa
sources:
  - "[[06-EVIDENCE/OCTOPUS-L191-FINDINGS-2026-08-28]]"
  - "[[06-EVIDENCE/OCTOPUS-TELEGRAM-WEBAPP-PHASE0-2026-08-29]]"
  - "[[06-EVIDENCE/OCTOPUS-REUSE-AUDIT-2026-08-29/MISSING-EDGES]]"
---

# 08 — EDGE-6 causal trace

```text
EDGE6_DEFINITION=180_proposal_outbox_send_or_drain_to_138
EDGE6_LAST_VERIFIED_STAGE=registry_projection
EDGE6_FIRST_MISSING_STAGE=proposal_enqueue
EDGE6_PATCH_AUTHORIZED=NO
EDGE6_FIXED=NO
RUN=run-spine-138-snap-20260828T005835Z
PROPOSAL=proposal-950f8d0e
observed_at=2026-08-28
method=prior_ssh_artifacts_plus_docs
this_session_ssh=0
truth_status=DOCUMENTED
```

## Canonical definition

`06-EVIDENCE/OCTOPUS-L191-FINDINGS-2026-08-28.md` §5 table:

> **EDGE-6** = **ارسال outbox ۱۸۰→۱۳۸** (180 proposal outbox send/drain to 138).  
> Status for this run: **PROVEN_BROKEN**.

EDGE-7 mint, EDGE-8 witness-for-run, EDGE-9 owner-receipt consume are **downstream**.

Registry / `live_spine_run.json` is **not** effect and **not** receipt.

## Mechanism (refined)

Morning L191: spine handler returned after registry; `persist_pending` / `transmit_pending` not called; 25 outbox files; none `proposal-950f8d0e`; journal since 27 Aug: zero send/drain.

Phase 0 + later disk: persist/transmit **exist** on the wake/snapshot PATH_A tail, and a **second** inline PATH_B was added 13:15Z **after** 07:21 materialize. This run was **not** replayed through PATH_B.

```text
EDGE6_ROOT_CAUSE_07_21=proposal_never_enqueued
EDGE6_ROOT_CAUSE_LIVE_CODE=duplicate_future_paths_unreconciled
OLD_THREE_LINE_PATCH=STALE_WOULD_CREATE_PATH_B_AGAIN
```

## Chain for `run-spine-138-snap-20260828T005835Z`

IDs: source hash `950f8d0e02e6dc89…`; proposal file sha `ddd5b11c…`; registry prefix `cff7fc6d`; proposal mtime **07:21:30Z**.

| Stage | Status | Artifact ID | Store | Producer | Consumer | ts | hash | correlation | causation | run ID | business ID |
|---|---|---|---|---|---|---|---|---|---|---|---|
| proposal | PRESENT_VERIFIED | `proposal-950f8d0e.json` | 180 `state/cognition/` | 180 materializer | none for drain | 07:21:30Z | `ddd5b11c…` | snap run | EDGE-5 | `run-spine-138-snap-…` | source `950f8d0e` |
| draft / OwnerDecision | MISSING | — | — | — | — | — | — | — | — | — | — |
| owner item OFN | MISSING | — | 138 outbox | — | decide | — | — | — | — | — | no `950f8d0e` row |
| owner decision | PRESENT_UNVERIFIED as file; NOT_APPLICABLE as decide→effect | `…/AUTH/run-spine-138-snap-….owner-receipt.json` | 191 AUTH | owner | unused | — | `25811b70…` | run name | not POST decide | run-spine-… | — |
| plan/command | MISSING | — | — | — | — | — | — | — | — | — | — |
| enqueue | MISSING | no `replies/pending` / `meta/spine-proposal-*` | 180 reply-outbox | — | — | — | — | — | — | — | lineage UNSCOPED_EVIDENCE_ABSENT |
| transmit attempt | MISSING | — | 180 audit | — | — | — | — | — | — | — | seq 6006–6017 = wake/snapshot |
| effect | MISSING | — | 138 | HOLD_EXTERNAL | — | — | — | — | — | — | — |
| ACK | MISSING for proposal; CONTRADICTED if 6006–6017 labeled EDGE-6 | wake ACKs `8a7ac40f` / `64a6e2f6` | mesh | 138 transport | 180 | 00:59–01:01 | — | inbound mids | — | snap/wake | not proposal |
| receipt | CONTRADICTED as this-run closure | `630c5060…` notify; `wr_950f8d0e_receipt.json` | 138/182 | 182/138 | — | 07:19:39Z **before** proposal | `bce27b8a…` native | `425f4012-…` ≠ snap run | source hash | `witness-receipt-950f8d0e` | source hash not enqueue |
| witness | PRESENT_VERIFIED as source-hash STRUCTURAL_PASS; MISSING as EDGE-8 drain | `wr_950f8d0e` | 182 | 182 | 138 notify | 07:19:39Z | signed | source hash | — | matches source | no proposal/effect IDs |
| registry projection | PRESENT_VERIFIED | `live_spine_run.json` | 180 | materializer | observers | 07:21:30Z | prefix `cff7fc6d` | snap run | — | snap run | **last proven same-run step** |
| frontend | NOT_OBSERVED for this proposal | — | Cockpit/MiniApp | — | — | — | — | — | — | — | 191 cards = ziman-gallery |

**Last verified same-run stage:** registry projection.  
**First missing same-run stage:** proposal enqueue.

Mechanism of 07:21 materialize (why no persist): `UNKNOWN` (no audit line; inbound already `reply_acked`).

## Do not patch from

1. Morning “add 3 persist lines” — those lines **are** PATH_B.
2. Owner “PROVEN_OK” via L977 dry-run + seq 6006–6017 — L977 is `call_model=False`; 6006–6017 are wake/snapshot.
3. `630c5060` as this-run receipt — envelope `run_id` does not match.
