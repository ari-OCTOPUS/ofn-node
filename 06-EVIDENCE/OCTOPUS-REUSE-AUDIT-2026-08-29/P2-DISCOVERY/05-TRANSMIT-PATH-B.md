---
type: report
project: "[[04 - Architect System/architect/PROJECT]]"
status: ready
tags: [octopus, transmit, path-b]
created: 2026-08-29
updated: 2026-08-29
created_by: agent
language: fa
sources:
  - "[[06-EVIDENCE/OCTOPUS-TELEGRAM-WEBAPP-PHASE0-2026-08-29]]"
  - "[[06-EVIDENCE/OCTOPUS-REUSE-AUDIT-2026-08-29/MISSING-EDGES]]"
---

# 05 — Transmit PATH_B (inline second transmit)

```text
PATH=B
NAME=materialize_spine_proposal_inline
CANONICAL=NO
FALLBACK=NO
SECOND_TRANSMIT=YES
observed_at=2026-08-29T04:50:00Z
current_180_bytes_reread=NO
truth_status=DOCUMENTED
```

## Graph

```text
PATH_B:
materialize_spine_proposal
→ _build_proposal_v1
→ atomic_json proposal file
→ _register_live_spine_run   # registry; NOT receipt
→ persist_pending(synthetic original, proposal)
→ transmit_pending(...)      # result DISCARDED
→ return ready
→ (caller handle_task may then run PATH_A on a different original)
```

Documented lines on 180 worker sha `c43afff0…` (28 Aug / 180 pack 29 Aug): `_build_proposal_v1` ~572; registry ~583; persist+transmit ~586–589. Added mtime **2026-08-28T13:15:15Z**. Pre-patch `.bak` `d2f3e571…` returned after registry (morning L191 FACT).

## IDs (why dedupe cannot collapse A and B)

| Field | PATH_A | PATH_B |
|---|---|---|
| run_id on wire | inbound `run-spine-138-snap-…` or mid | synthetic `spine-proposal-950f8d0e` |
| original message_id | inbound wake/snapshot id | constructed, not inbound |
| idempotency | `reply:{inbound_mid}:{sha}` | `reply:{synthetic_mid}:{sha}` |
| business run preserved | yes when inbound has it | **no** |

`persist_pending` dedupes on **original.message_id + response_sha256** (`octopus_reply_outbox.py` WAVE0 ~215–221). Different mids → two pending files → two wires.

## Stage notes

| Stage | side effect | durable write | caller ownership |
|---|---|---|---|
| registry | `live_spine_run.json` | yes | materializer |
| persist/transmit | same primitives as A | second pending/meta | materializer; transmit result unused |
| ACK/effect/receipt | not observed for proposal-950f8d0e | MISSING | n/a |

## Relation to morning L191

“Return after registry, persist never called” is **true for 07:21 materialize** of this run and **stale as a live-code diagnosis**. `MISSING-EDGES` E4 still quotes the morning FACT. Adding the “three persist lines” again would **duplicate PATH_B**.

180 pack 2026-08-29: live worker sha still `c43afff0…`; header still claims stale `72e3b3a3` / “NOT live” (`CON-WORKER-HASH`). `DOCUMENTED`.
