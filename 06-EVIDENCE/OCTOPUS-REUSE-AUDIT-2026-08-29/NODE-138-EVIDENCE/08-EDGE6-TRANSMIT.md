---
type: report
project: "[[04 - Architect System/architect/PROJECT]]"
status: ready
tags: [octopus, node-138, edge-6, transmit]
created: 2026-08-29
updated: 2026-08-29
created_by: agent
language: en
sources:
  - "[[06-EVIDENCE/OCTOPUS-REUSE-AUDIT-2026-08-29/P2-DISCOVERY/04-TRANSMIT-PATH-A]]"
  - "[[06-EVIDENCE/OCTOPUS-REUSE-AUDIT-2026-08-29/P2-DISCOVERY/05-TRANSMIT-PATH-B]]"
  - "[[06-EVIDENCE/OCTOPUS-REUSE-AUDIT-2026-08-29/P2-DISCOVERY/08-EDGE6-CAUSAL-TRACE]]"
  - "[[06-EVIDENCE/OCTOPUS-L191-FINDINGS-2026-08-28]]"
---

# 08 — EDGE-6 and transmit

```text
observed_at=2026-08-29T05:32:32Z
method=prior_packs_plus_138_identity_only
this_session_180_bytes=NO
EDGE6_PATCH_AUTHORIZED=NO
EDGE6_FIXED=NO
scope=this_host_only
```

EDGE-6 **definition**: 180 proposal outbox send/drain **to 138**. 138 is the receive/mint/ledger side, not the dual-transmit host.

This session did **not** re-read 180 worker bytes. Transmit graph is `DOCUMENTED` from P2-DISCOVERY 04/05/08 + L191 + Phase 0.

## PATH_A — canonical egress (180)

`handle_task` → freeze → `persist_pending` → `transmit_pending` → `octomesh_send` → ACK `ack|duplicate`.

Idempotency: `reply:{inbound_mid}:{response_sha256}`. run_id from inbound.

## PATH_B — second transmit (180)

`materialize_spine_proposal` → registry → persist/transmit with **synthetic** `spine-proposal-*` mid; result discarded; then PATH_A may still fire.

Added ~2026-08-28T13:15Z. Morning L191 “return after registry” is **true for 07:21 materialize**, **stale as live-code diagnosis**.

## Stage table (run-spine-138-snap-20260828T005835Z)

Unchanged from P2 08: last same-run verified = **registry projection**; first missing = **proposal enqueue**. OwnerDecision / OFN owner item / transmit / effect / matching ACK **MISSING**. 182 `wr_950f8d0e` is source-hash STRUCTURAL before proposal mtime.

## Answers

```text
CANONICAL_TRANSMIT_PATH=PATH_A
SECOND_PATH_PURPOSE=inline_spine_materialize_second_transmit_NOT_fallback
BOTH_CAN_FIRE_FOR_ONE_ACTION=YES_FUTURE_UNFROZEN_SPINE
DUPLICATE_EFFECT_POSSIBLE=YES
ACK_SEMANTICS=transport_or_inbox_store_not_effect
RECEIPT_SEMANTICS=schema_local_not_same_run_effect
FIRST_MISSING_EDGE=proposal_enqueue
EDGE6_FIRST_MISSING_STAGE=proposal_enqueue
TRANSMIT_PATHS=PATH_A,PATH_B
```

138 this session: mesh/OFN outbox **not listed** (no queue consume). Prior E0: 25 outbox rows all `manual_completed` (`DOCUMENTED` / `STALE` as now).

Do not apply the “three persist lines” — that **is** PATH_B.
