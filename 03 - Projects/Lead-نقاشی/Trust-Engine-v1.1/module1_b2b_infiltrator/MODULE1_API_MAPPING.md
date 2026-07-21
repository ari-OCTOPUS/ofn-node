# MODULE 1 — B2B INFILTRATOR: API mapping & workflow design
**Version:** 1.1 · **Goal:** implement the **Premium Trust-and-Response playbook**'s
closed-network behaviour as software — a recurring pipeline of Property Managers (PMs) and
sales agents in premium LGAs, fed by listing signals, converted through hyper-professional,
human-approved outreach.
**Stack ruling applied (v1.1, hardened):** n8n = collection limb only (poll, parse, normalise,
signed submission). Octopus = brain, ledger, gate, approval surface, and the ONLY component
that sends. n8n holds no gate, Telegram, or outbound credentials — see
`n8n_wf2_REMOVED_README.md` for the binding allowed/forbidden matrix.

## 1. Why PMs first (the economics)
One homeowner = one job. One PM = 80–200 managed properties with recurring end-of-lease
patch-and-paint, tenant damage, and landlord refresh work. The PM's pain is **vacancy days**, not
price. The offer is therefore turnaround, not discount: *"48–72h patch & paint between tenants,
fixed prices per room, photo evidence, invoice-ready."* Sales agents (pre-sale refresh before
open home) are the second persona, same pipeline, different offer variant.

## 2. Stage map

| Stage | What happens | Tooling | Human gate |
|---|---|---|---|
| S1 Discover | Daily pull of new FOR-RENT (PM persona) and FOR-SALE (agent persona) listings in target suburbs | Domain API `POST /v1/listings/residential/_search` | — |
| S2 Identify | Extract listing agency + listed agent from the listing payload (public data) | same response; `GET /v1/agencies/{id}` for office details | — |
| S3 Enrich | Agency office contact (published), ABN check, portfolio-size hint (# active rental listings via agency listings endpoint) | Domain agencies/listings endpoints + ABN Lookup API | — |
| S4 Qualify & dedupe | New agency/contact? Suppressed? Score by LGA fit + portfolio size + listing freshness | n8n Code + Octopus inbox dedupe | — |
| S5 Draft | Persona-matched intro email (LLM, prompt §5) | Anthropic API via n8n HTTP node | — |
| S6 Propose | Signed POST of candidate+draft to the Octopus ingestion boundary; **Octopus** renders the Telegram card from its own bot | `POST /api/v1/lead-candidates` (candidate_type=`public_b2b`; HMAC + timestamp + nonce + idempotency key) | **Owner approves/edits/rejects — callback handled by Octopus's own bot, never n8n** |
| S7 Send | On approve: LANGAR append → EffectorGate → email send from business mailbox | Octopus-owned outbound worker (SMTP/Gmail API) | gated |
| S8 Cadence | No reply after 6 business days → ONE follow-up proposal; then quarterly value-add only (market snapshot, new case study) | Octopus scheduler → new cards | each send gated |
| S9 Outcome | reply / meeting / first job / no-response → `record_proposal_outcome()` | Octopus | `/won`, `/meeting`, `/dead` commands |

## 3. Domain API specifics (verified 2026-07-21)
- Portal: developer.domain.com.au — create project, subscribe to a plan (tiers by industry/volume; entry tiers exist). Auth: API key (`X-Api-Key`) or OAuth2 client-credentials
  depending on package.
- Endpoints used:
  - `POST /v1/listings/residential/_search` — body: `{"listingType":"Rent","locations":[{"state":"NSW","suburb":"Mosman","postCode":"2088"}],"pageSize":50,"listedSince":"<ISO8601>"}` (persona A). Same with `"listingType":"Sale"` for persona B.
  - Listing payload includes `advertiser` (agency id/name) and `contacts`/agent display fields.
  - `GET /v1/agencies/{id}` — office name, address, published office contact details.
  - `GET /v1/agencies/{id}/listings` — portfolio-size proxy (count of active rentals).
- **Conditions that are part of the licence:** "powered by Domain" attribution + listing
  backlinks wherever listing data is displayed (our Telegram cards are internal tooling; keep the
  listing URL on the card anyway), analytics beacon for public display (N/A internally), do not
  hide agent contact info. Enquiry/performance APIs (agency OAuth) are NOT used.
- Fallback if plan access stalls: the same S1–S3 can run on realestate.com.au **manually**
  (Owner forwards agency names via `/lead ... kind:b2b`) — the pipeline shape survives without
  the API; only S1 automation degrades.

## 4. Compliance lane (hard-coded)
- Contact = **agency office / role contact conspicuously published** (agency site, listing page).
  Message = directly relevant to their role (property maintenance services for managed
  properties) → Spam Act inferred-consent lane. Every email: business identification + working
  unsubscribe + physical suburb of operation.
- Forbidden: bulk scraped lists, personal emails of individuals not published in a business
  capacity, contacting homeowners from listing data (that data identifies the AGENT, not the
  vendor — vendors are out of scope entirely), any SMS to numbers not published for business
  contact. Unsubscribe → suppression list → hard block at inbox level.
- Volume guard: `MAX_NEW_OUTREACH_PER_DAY = 5`, `MAX_FOLLOWUPS = 1`. This is a relationship
  play, not a spray. Five personal, listing-specific emails beat fifty templates — and keep us
  defensible under ACMA's active enforcement posture.

## 5. Draft prompt (system, used at S5)
```
You draft first-contact emails for {{OWNER_NAME}}, owner of {{BUSINESS_NAME}}, a licensed
Sydney painting & maintenance business (NSW Lic {{NSW_LICENCE_NO}}, insured {{INSURANCE_COVER}}).
Audience: a specific property manager or sales agent, identified from a real listing.

Rules:
- Subject ≤ 55 chars, concrete, no clickbait, no "quick question".
- ≤ 130 words. Structure: (1) one line proving this isn't a blast — name the actual
  listing/suburb context ("saw your new rental on {{street_or_suburb}}"); (2) the offer in
  their KPI language — for PMs: vacancy-day compression ("patch & paint between tenants,
  48–72h, fixed per-room pricing, photo report you can forward to the landlord"); for sales
  agents: pre-listing refresh before photography/open home; (3) proof: one suburb-named case
  study line + review count; (4) CTA: "happy to do a walk-through of one property this week —
  no charge, you'll get a fixed price menu you can keep on file."
- Tone: peer-to-peer trade professional. Zero marketing adjectives. No attachments on first
  touch.
- Footer (always): {{BUSINESS_NAME}} · NSW Lic {{NSW_LICENCE_NO}} · {{SUBURB_BASE}} ·
  "If maintenance vendors aren't your thing to manage, reply 'unsubscribe' and I won't email again."
Output JSON: {"subject": str, "body": str, "persona": "pm|sales_agent", "listing_ref": str}
```

## 6. Telegram card (S6 — rendered and owned by Octopus, spec only)
```
🏢 B2B CANDIDATE — {{agency_name}} ({{persona}})
{{contact_name_or_office}} · {{suburb}} · portfolio≈{{active_rentals}} rentals
Trigger listing: {{listing_url}}
── Draft email ──
Subj: {{subject}}
{{body}}
[✅ Approve send] [✏️ Edit] [⏸ Not now] [🚫 Never this agency]
```

## 7. n8n implementation (files in this folder) — v1.1
- `n8n_wf1_discovery_to_approval.json` — schedule → Domain search per suburb → flatten →
  dedupe (politeness pre-filter; authoritative idempotency is Octopus's) → agency contact →
  LLM draft → build canonical candidate → **HMAC-sign → POST /api/v1/lead-candidates**.
  That POST is the ONLY endpoint n8n may call on Octopus. **No card, no gate, no send path
  exists in n8n.**
- `n8n_wf2_REMOVED_README.md` — records why the v1.0 callback workflow was deleted and the
  binding allowed/forbidden matrix. The approval surface (card render + callback + verdict)
  is implemented inside Octopus.
- Import WF1, then: bind credentials (Domain API key, Anthropic key — nothing else), set the
  CONFIG node (incl. `OCTOPUS_INBOX_HMAC_SECRET`, scoped to candidate submission only), set
  n8n env `NODE_FUNCTION_ALLOW_BUILTIN=crypto`, and confirm node typeVersions on import
  (written against n8n 1.x).
- **Standalone fallback mode** (Octopus HTTP surface not yet deployed): replace the final POST
  node with a Gmail **create-draft** node (never send); the owner reviews and sends manually
  from Gmail. No gate semantics are simulated in n8n even in fallback.

## 8. Metrics (fed back via Octopus)
- outreach → reply rate (target ≥ 15% at n=40 before scaling volume)
- reply → walk-through booked · walk-through → first job · first job → jobs/quarter per agency
- cost: Domain plan + ~an hour of Owner approvals per week. Break-even = one end-of-lease job.

## 9. Failure modes
- Domain quota/auth failure → alert card, poller pauses (never silent).
- Agency appears with no published office email → card offers "call instead" task (DNC-checked)
  rather than skipping silently.
- LLM returns non-JSON → one retry with repair prompt → else raw-notes card for manual draft.
- Same agency triggered by multiple listings same week → single card, listings aggregated.
