---
type: report
project: "[[04 - Architect System/architect/PROJECT]]"
status: ready
tags: [octopus, transmit, path-a]
created: 2026-08-29
updated: 2026-08-29
created_by: agent
language: fa
sources:
  - "[[06-EVIDENCE/BOARD-180-REPLY-REPAIR-2026-08-27/WAVE0/octopus_reply_outbox.py]]"
  - "[[06-EVIDENCE/OCTOPUS-TELEGRAM-WEBAPP-PHASE0-2026-08-29]]"
---

# 04 — Transmit PATH_A (canonical egress)

```text
PATH=A
NAME=handle_task_common_egress
CANONICAL=YES_BY_HISTORY
observed_at=2026-08-29T04:50:00Z
current_180_bytes_reread=NO
truth_status=DOCUMENTED
```

Live worker is **not** on `F:\backup`. Contract copy: `06-EVIDENCE/BOARD-180-REPLY-REPAIR-2026-08-27/WAVE0/octopus_reply_outbox.py`. Line numbers for `handle_task` come from prior 180 traces (`03-edge6-control-flow.md`, Phase 0), not from this session’s SSH.

## Graph

```text
PATH_A:
inbound mesh task (wake/snapshot/unfrozen)
→ octopus_cognitive_worker.handle_task
→ optional materialize_spine_proposal (if spine; see PATH_B)
→ if ready: response = dict(spine["proposal"])   # fall-through
→ freeze_prediction
→ persist_pending(original, response)
→ transmit_pending(rec)
→ octomesh_send.transmit(wire)
→ remote {status: ack|duplicate} = parse_verdict ACK
→ pending → acked; processed_ids reply_acked=true
→ INPUT_PROCESSED only after REPLY_ACKED
```

## Stage table

| Stage | file:line | function | input | output | run_id | message_id | business_id | idempotency | side effect | durable write | failure | retry | owner |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| entry | 180 `octopus_cognitive_worker.py` ~952–1054 (DOCUMENTED) | `handle_task` | inbound envelope | response dict | `original.run_id` else `original.message_id` | inbound task id | inbound run_id when present | n/a yet | cognition | prediction freeze | skip if already processed | timer 45s | 180 worker |
| persist | WAVE0 `octopus_reply_outbox.py:211` | `persist_pending` | original+response | pending record | from original | original.message_id | same as inbound when set | `reply:{mid}:{response_sha256}` `:82` | none on wire | `state/replies/pending/<sha>.json` + meta | duplicate same mid+sha collapsed | n/a | reply-outbox |
| transmit | same `:421` | `transmit_pending` | rec + TransmitFn | verdict | audit may use correlation/mid | same | same | same key | `fn(wire)` once | `transmit_handed` latch `:475` | RETRY_WAIT; circuit 3/60s | re-enter transmit; no second `fn` if handed | reply-outbox |
| ACK | `:328` | `parse_verdict` | remote result | ack\|duplicate treated ACK | not business proof | envelope | n/a | n/a | move pending→acked | meta + processed_ids | handed_awaiting_ack | wait | transport |
| effect | 138 (not this path) | UNKNOWN | — | — | — | — | — | — | **not proven by ACK** | OFN/ledger if any | — | — | 138 body |
| receipt | 182 / owner files | schema-local | — | — | often mismatched | — | — | — | **not this path** | — | — | — | DISPUTED |

## Semantics (180 pack, DOCUMENTED)

Mesh receive ACK on 180 means **valid inbox store**, not effect execution. Seven-step receive; no payload code exec; authenticity = SSH boundary, no message HMAC (`DOCUMENTED` from 180 pack; `NOT_RUN` here).

PATH_A is the **pre-existing common tail** for every unfrozen task. Phase 0 allowlist: keep this path; remove the later inline path.
