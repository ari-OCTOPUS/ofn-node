---
type: report
project: "[[04 - Architect System/architect/PROJECT]]"
status: ready
tags: [octopus, idempotency, ack, receipt]
created: 2026-08-29
updated: 2026-08-29
created_by: agent
language: fa
sources:
  - "[[06-EVIDENCE/BOARD-180-REPLY-REPAIR-2026-08-27/WAVE0/octopus_reply_outbox.py]]"
  - "[[06-EVIDENCE/OCTOPUS-TELEGRAM-WEBAPP-PHASE0-2026-08-29]]"
---

# 06 — Idempotency, ACK, receipt

```text
IDEMPOTENCY_KEY_CANONICAL=CONTRADICTED_TWO_SYSTEMS
ACK_SEMANTICS=transport_or_inbox_store_not_effect
RECEIPT_SEMANTICS=schema_local_not_same_run_effect
DUPLICATE_EFFECT_POSSIBLE=YES
EDGE6_PATCH_AUTHORIZED=NO
observed_at=2026-08-29T04:50:00Z
```

## Twelve answers

| # | Question | Answer | Truth |
|---|---|---|---|
| 1 | Canonical transmit path? | **PATH_A** (`handle_task` common persist/transmit). PATH_B is a 13:15Z add-on. | DOCUMENTED |
| 2 | Can both run for one owner action? | **This historical run: no.** Future **unfrozen** spine task: **yes** (B then A fall-through). | DOCUMENTED / inference |
| 3 | Internal path fallback or second transmit? | **Second transmit.** Result discarded; different IDs; no ACK-state guard. | DOCUMENTED |
| 4 | Is `run_id` attempt or business? | **Overloaded.** Business: `run-spine-138-snap-20260828T005835Z`. PATH_A: inbound run or mid. PATH_B: `spine-proposal-950f8d0e`. 138 notify UUID `425f4012-…`. ACK audit sometimes uses mid. | DOCUMENTED |
| 5 | Dedupe before or after effect? | **Before send** (same mid+sha). **After handoff** (`transmit_handed`). **Not** after 138 business effect. Different mids = no dedupe. | REPO_VERIFIED (WAVE0 copy) + DOCUMENTED |
| 6 | Namespaced business ID stable on both? | **No.** P1 `business:<tenant:idem>` is OFN, not mesh. PATH_B drops the spine run on the wire. | DOCUMENTED |
| 7 | Crash after remote accept, before receipt? | `transmit_handed=true`, pending on disk, retry will not re-call `fn(wire)`. Remote may have accepted. No effect receipt. | DOCUMENTED (contract) |
| 8 | What ACK proves? | Transport accepted the **reply envelope** (`ack` or `duplicate`). 180 receive ACK = valid inbox store. Not mint, not effect, not owner GO. | DOCUMENTED |
| 9 | What receipt proves? | Only its own schema. 182 `wr_950f8d0e` = signed `STRUCTURAL_PASS` on **source hash**, `may_authorize=false`, issued **07:19** (before 07:21 proposal). `630c5060` = 138 notify envelope, **wrong** `run_id`. Owner receipt `APPROVED` ≠ `may_contact`. Registry write is **not** a receipt. | DOCUMENTED |
| 10 | Effect without receipt? | Architecturally possible. **Not observed** for this proposal (no enqueue). | HYPOTHESIS |
| 11 | Receipt without effect? | **Yes, observed:** 182 witness + 138 notify + 191 owner receipt exist; no proposal transmit/effect. | DOCUMENTED |
| 12 | Duplicate future testable? | In principle yes (fake `OCTOMESH_REPLY_TRANSMIT`, two originals). No `test_cognitive_worker.py` on vault. WAVE0 tests same-mid retry, not dual-path. Phase 0: some materializer tests can hit real transport — do not run them. | DOCUMENTED |

Until 1 and 2 are re-verified on **current** 180 bytes in an isolated worktree:

```text
EDGE6_PATCH_AUTHORIZED=NO
```

## Two idempotency systems (do not merge)

| System | Key | Store | Meaning |
|---|---|---|---|
| OFN outbox | `{tenant}:{caller_key}` | SQLite on 138 | business enqueue uniqueness |
| P1 projection | `business:<tenant:idem>` | V2 JSON only | display namespace |
| Mesh reply-outbox | `reply:{original_message_id}:{response_sha256}` | 180 `state/replies` | transport attempt uniqueness |

There is no single canonical idempotency key across planes.

## Crash / race

```text
handed_awaiting_ack:
  remote may have accepted
  local pending still present
  retry must not fn(wire) again
  no OFN receipt
  no EDGE-6 closure
```

180 pack: worker 45s timer is the retry driver (`OnUnitActiveSec=45s`). `DOCUMENTED`.
