# VERIFIED ECONOMIC STATES — contract design (owner ruling 1, 2026-09-02: APPROVED DESIGN)

Status: design approved by owner 2026-09-02 (رأی ۱، ECONOMIC-LEARNING-RULINGS-2026-09-02).
Implementation: separate PR, human review. **No spine-event change. Sealed names stay sealed.**

## 1. Problem

`ofn/kernel/events.py` deliberately seals `send_authorized`, `quote_sent`,
`campaign_envelope_ready` as FORBIDDEN_EFFECT_KINDS — revenue words are STATES,
not spine events. There is no typed contract for *receipt-verified economic
outcomes*, so verified payments can only live in a lane-local ledger.

## 2. Proposal — adapter-level state vocabulary (not events)

A frozen, versioned set of **effect-observation states**, recorded by
adapters (never by the spine), mirroring the kernel's style:

```python
# ofn/learning/states.py (proposed, this design only)
ECONOMIC_STATES = frozenset({
    "payment_received_verified",    # independent receipt hash matched
    "payment_claim_unverified",     # claim exists, no independent receipt
    "payment_receipt_tampered",     # receipt diverges from claim
    "payment_disconnected",         # receipt real, lead-link unproven
    "response_received",            # inbound observed (receipted imap row)
    "quote_card_sent",              # quote row status=sent (painting_quotes)
})
```

Rules encoded in code, mirroring the kernel's refusal patterns:
1. none of these may EVER appear as a spine `kind` (validated against
   EVENT_KINDS — the states are a different namespace by construction);
2. `payment_received_verified` requires: independent source ≠ claimant +
   sha256(receipt fields) match + provable lead link (ReceiptVerifier);
3. states are observations, never authorizations — any code path combining a
   state with a send decision raises (same shape as OutcomeScorer.authorize);
4. receipts source (owner ruling 6, combined): now = owner-provided receipt
   file + SHA256 in a receipt folder; later = payment-provider API. Until an
   independent receipt exists, every payment stays `payment_claim_unverified`.

## 3. What explicitly does NOT change

- `FORBIDDEN_EFFECT_KINDS` untouched (quote_sent stays sealed);
- `ofn/kernel/events.py` untouched on the implementing branch (asserted by test);
- no new send capability: the states observe, they never authorize.

## 4. Acceptance tests (for the implementing PR)

- vocabulary frozen: adding a state without version bump fails;
- each state only constructible with its required evidence fields;
- reflection test: `ECONOMIC_STATES ∩ EVENT_KINDS = ∅` forever;
- independent-source rule unit-tested (claimant-attested receipt rejected);
- states.py cannot be imported by kernel (dependency direction enforced).
