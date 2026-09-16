# LEG P0-2 — `quote_draft` (quote half of P0 ResponseQuoteLeg)
**Version:** 1.1 · **Priority:** P0 · **Pattern source:** Upscale (5 written guarantees, fixed price, transparent pricing) + Premium Trust-and-Response playbook (premium PDF presentation)
**Type:** propose-only Leg

## Mission
Turn the Owner's rough post-inspection notes into a premium, fixed-price, guarantee-stacked quote — drafted in < 10 minutes, sent same day. The quote *is* the marketing: it must look like a $5M/yr company produced it.

## Integration contract *(verify against repo)*
- Trigger: Telegram command `/quote <free text>` from Owner, or event `inspection.completed`.
- Emits `LegProposal(kind="quote_draft")` → approval card → on Approve: EffectorGate releases
  (a) PDF generation and (b) delivery message (SMS/email with link or attachment).
- Outcome via `record_proposal_outcome()`; quote lifecycle events (`quote.sent`, `quote.won`,
  `quote.lost`) feed the Governor and the Follow-Up backlog (P1).

## Input (owner notes, free text)
Example: `/quote 3br house mosman, walls+ceilings+trims, heritage windows front, needs gyprock patch hallway, 4 days, 4800, sarah 0412..., wants it before open home 9 aug`

## Processing steps
1. **Parse** notes → structured `QuoteDraft` (LLM, schema below). Missing critical fields
   (price, scope, client contact) → card asks Owner the gaps instead of guessing.
2. **Licensing check — FAIL-CLOSED (v1.1; the system never auto-decides statutory scope):**
   - The classifier only RAISES FLAGS; it never clears them. Reference facts (Verification
     Report §4.1: >$5k residential = licensed; stand-alone internal exempt since 2015) are
     shown on the card as *context for the Owner*, not applied as automatic rules.
   - Any of: value near/over $5k · scope not purely internal · mixed painting+other work ·
     contract-structure ambiguity → `quote_status = REQUIRES_LICENCE_REVIEW` and
     `external_send_allowed = false` until the Owner explicitly confirms licence applicability
     on the card (one tap: "Licence covered ✅" / "Restructure scope" / "Decline job").
   - Specialist risk flags — each independently forces review, never auto-cleared:
     `lead_paint (pre-1970s)` · `asbestos` · `waterproofing` · `electrical` · `plumbing` ·
     `working_at_heights / rope_access` · `mould_remediation_beyond_surface`. Card links the
     relevant SafeWork/Fair Trading obligation note.
   - Contract requirements reminder (written contract >$5k, deposit caps, home-warranty
     insurance threshold) rendered as an Owner checklist — *verify current thresholds with
     Fair Trading; do not hard-code them.*
3. **Guarantee stack selection** — pick the subset that fits this job:
   G1 fixed-price guarantee (signed, no variations without written approval) ·
   G2 not-a-scratch guarantee (+ pre-start photo protocol) ·
   G3 {{WARRANTY_YEARS}}-year written workmanship warranty ·
   G4 free colour consult ·
   G5 daily clean-site + photo update promise.
4. **Compose** client-facing quote content (LLM prompt below) → HTML → PDF (effector).
5. Card to Owner with full preview.

## Output schema (`QuoteDraft`)
```json
{
  "client": {"name": "", "phone": "", "email": "", "address": "", "suburb": ""},
  "scope_type": "internal_only|external|mixed",
  "line_items": [{"area": "", "work": "", "prep": "", "coats": 2, "product": ""}],
  "exclusions": [],
  "price_fixed_incl_gst": 0,
  "licence_required": true,
  "duration_days": 0,
  "proposed_start": null,
  "deadline_context": "pre_sale|end_of_lease|none",
  "guarantees": ["G1","G2","G3"],
  "validity_days": 14
}
```

## LLM prompt template (system)
```
You are the quote writer for {{BUSINESS_NAME}} (NSW Lic {{NSW_LICENCE_NO}}, fully insured
{{INSURANCE_COVER}}). Expand the owner's rough notes into a premium fixed-price quote.

Structure (in order):
1. One-paragraph personal opener: reference the property, the client's goal (e.g. "ready
   before your open home on {{date}}"), and one specific observation from the inspection.
2. Scope of works: per-area table rows (area / prep / system / coats / product line). Be
   specific about prep — prep detail is what separates premium quotes from texts with a number.
3. What's included: protection of floors & furniture, daily tidy, colour consult if selected,
   photo documentation before/during/after.
4. Exclusions: explicit, short, honest.
5. Fixed price: ONE number incl. GST. No ranges. State "fixed — no variations without your
   written approval."
6. Guarantees: render ONLY the guarantee IDs provided, as short bold promises.
7. Timing: duration + earliest start + validity window.
8. Next step: one line — "Reply YES and we'll lock in {{proposed_start}}."
Tone: confident, concrete, zero fluff, Australian English. Never invent measurements,
products, or prices not present in the notes. If notes conflict, flag in "open_questions"
instead of resolving silently.
Output JSON: {"quote_html_body": str, "sms_cover": str(≤300 chars, ends with STOP line),
"email_cover": str, "open_questions": [str]}
```

## Telegram approval card
```
📄 QUOTE DRAFT — {{client.name}} · {{suburb}} · ${{price_fixed_incl_gst}}
Scope: {{scope_type}} | Licence req: {{licence_required}} | {{duration_days}} days
Guarantees: {{guarantees}} | Deadline: {{deadline_context}}
Open questions: {{open_questions | "none"}}
── PDF preview attached ──
[✅ Send to client] [✏️ Edit] [💲 Change price] [🗑 Discard]
```
`Change price` → inline reply with new number → re-render → new card (versioned `q-v2`).

## PDF generation effector
- MVO: HTML template → headless Chromium print-to-PDF (no external SaaS, zero cost).
- Template requirements: logo, licence + ABN + insurance line in header; Dulux-accredited badge
  if held; before-photos page if supplied; guarantee page; T&Cs page ({{TCS_VERSION}}).
- Later (P2): ServiceM8 quote object sync via its REST API so quotes live in job management.

## Outcome recording
`record_proposal_outcome(proposal_id, outcome ∈ {sent, edited_sent, discarded}, meta:{quote_id, value, scope_type, elapsed_notes_to_sent_s})`
Then lifecycle: `quote.won` / `quote.lost` (owner command `/won q-123` `/lost q-123 reason`) —
**these two commands are mandatory discipline: they are what makes the Governor learn.**

## KPIs
- notes → sent same-day rate ≥ 90% · quote→win % by niche/suburb (Governor input)
- average value of won vs lost quotes (price-position signal)
- % quotes with deadline_context (pre-sale / end-of-lease leads close faster — validate)

## Failure modes & guards
- Parse confidence low → ask-the-gaps card, never a guessed quote.
- Price present but < plausible floor for scope (config `MIN_SANITY_$/room`) → warn on card.
- Duplicate quote for same client+address open → card shows "v2 supersedes v1".
- PDF render failure → deliver clean HTML email fallback, log effector error.

## Compliance notes
- Quote = direct response to a request (consent: existing inquiry). Still: identification block
  + unsubscribe on the covering SMS/email.
- Australian Consumer Law: no misleading claims; guarantees rendered exactly as configured,
  warranty terms must match the written T&Cs version shipped with the PDF.
- NSW Home Building Act: >$20k jobs prompt the card to remind Owner about home warranty
  insurance requirements *(verify current threshold with Fair Trading before first big job)*.
- Fail-closed principle (v1.1): where licensing/compliance applicability is uncertain, the
  quote stays internal (`REQUIRES_LICENCE_REVIEW`); an AI must never make the final call on
  statutory scope.
