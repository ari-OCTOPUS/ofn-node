# OWNER-RULING-GOB3-2026-09-18 — approve all three pending go_b3 cards

- stamp: 2026-09-18T07:35Z (17:35 AEST)
- channel: owner chat with ZCode session (lane S2-OPEN-20260918), explicit 4-option question, owner selected:
  **«تأیید هر سه»** (option "تأیید هر سه (پیشنهادی)" of question «با این سه کارت چه کنم؟»)
- scope: the three pending entries of go_b3_pending_registry.json (sha256 857cd98d…, live-verified 06:43Z):
  1. `gob3-smarter-communities` / card SMARTER-COMMUNITIES → option **ACK_SEEN**
  2. `gob3-bcs-pica` / card BCS-PICA → option **ACK_SEEN**
  3. `gob3-INDEX-BATCH` / card INDEX → option **ACK_BATCH**
- effect unblocked: customer_contact for those targets (the send path's own gates —
  customer_send policy, channel-authorization, packet idempotency — still apply unchanged).
- authority chain: S2-OPENING-PROMPT-20260918.md (owner-authored) → this ruling →
  consumption records on 138 citing ruling sha.
- red lines untouched: no TCB change, no secret, no bypass of the send path's own
  authorization; customer_send policy itself is NOT modified by this ruling.

execution receipt (filled 2026-09-18T07:20:28Z remote):
- method: the binder's own functions (`mark_used` + `emit_decision` from go_b3_owner_bind.py),
  no forged TG spool message; authority fields recorded inside each decision row.
- pre-image registry sha256 `857cd98d60edb9ee…` → post-image `d34b6aeac9bebcc8…`
- decisions ledger pre `f37395950cc4e885…` → post `c00aae35fcfc2726…`
- 3 new owner_decision.v1 rows (verdicts ACK_SEEN / ACK_SEEN / ACK_BATCH), each carrying
  `authority: owner-chat-ruling-OWNER-RULING-GOB3-2026-09-18 sha256:13e87cdf055ea94a`,
  `consumed_by: zcode lane S2-OPEN-20260918`, `owner_words: «تأیید هر سه»`.
- registry now 6/6 consumed; external_effects=0, hold_external=true, customer_send=false
  unchanged in every row (the send path's own gates apply as before).
- rollback: restore registry from pre-image (statuses pending) + truncate the 3 decision rows;
  pre-image content preserved in this chain and in the session transcript.
