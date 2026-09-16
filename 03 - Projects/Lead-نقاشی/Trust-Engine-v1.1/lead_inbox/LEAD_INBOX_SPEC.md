# LEAD INBOX — ingestion boundary, canonical contract + three Day-1 paths
**Version:** 1.1 (2026-07-21) · Resolves the `WIRE_LEAD` bottleneck: one signed boundary, three producers.
**v1.1 changes (reviewer corrections, accepted):** endpoint renamed to `/api/v1/lead-candidates`;
HMAC/timestamp/nonce/idempotency controls made mandatory; `candidate_type` taxonomy adopted
(`consented_inbound | public_b2b | market_signal`); consent block extended (evidence,
retention_class, compliance_reason); event contract added; no external automation may reach
`/gate/*` — the approval surface is Octopus-owned.

---

## 0. The single boundary (everything funnels here)

Producers never talk to Legs, cards, or gates. They submit one signed shape; Octopus normalises,
dedupes, classifies, applies the consent firewall, and routes internally.

```
POST /api/v1/lead-candidates        (the ONLY endpoint external automation may call)

Required controls (all fail-closed):
- HMAC-SHA256 signature over `${timestamp}.${nonce}.${body}` (per-source secret)
- timestamp expiry (±300s) · nonce replay protection · Idempotency-Key header
- source allowlist (X-Octopus-Source) · JSON Schema validation · payload size limit
- attachment isolation (photos by reference, scanned before touch)
- rate limit per source · structured error codes
- append-only receipt event for EVERY submission (accepted or quarantined)
- invalid/unverifiable payloads → quarantine store + alert card (never silent drop)
```

## 1. Canonical Lead Candidate contract (v1.1)

```json
{
  "schema_version": "1.1",
  "lead_id": "uuid (assigned by inbox, not producer)",
  "idempotency_key": "source:external_id",
  "candidate_type": "consented_inbound | public_b2b | market_signal",
  "source": {
    "channel": "telegram_manual|website_form|missed_call|meta_lead_ad|facebook_group|nsw_da|domain_listing|synthetic_test|other",
    "source_id": "producer identifier from allowlist",
    "external_id": "string",
    "source_url": null,
    "received_at": "ISO-8601"
  },
  "contact": {
    "name": null, "organisation": null,
    "phone": null, "email": null,
    "preferred_channel": "sms|email|phone|null"
  },
  "consent": {
    "basis": "explicit | inferred_business | none | unknown",
    "evidence": "e.g. submitted_quote_form | office_contact_conspicuously_published | null",
    "captured_at": "ISO-8601",
    "outreach_allowed": false,
    "retention_class": "consented_customer | b2b_prospect_12m | signal_30d",
    "compliance_reason": "machine-checkable tag, e.g. SpamAct_inbound_request"
  },
  "property": { "address": null, "suburb": null, "postcode": null, "property_type": null },
  "request": {
    "service": null, "scope_text": "required — whatever was actually observed",
    "urgency": "emergency|within_1_week|within_2_weeks|flexible|unknown",
    "budget_aud": null, "photos": []
  },
  "qualification": {
    "intent_score": 0, "fit_score": 0, "urgency_score": 0,
    "estimated_value_low_aud": null, "estimated_value_high_aud": null,
    "risk_flags": []
  },
  "workflow": {
    "status": "received",
    "owner_action_required": true,
    "external_send_allowed": false,
    "next_action": "qualify"
  }
}
```

## 2. The consent firewall (structural, not advisory)

| candidate_type | May trigger outbound draft? | May be stored long-term? | Notes |
|---|---|---|---|
| `consented_inbound` | ✅ (response to their own request) | ✅ as customer/prospect | best input for ResponseQuote |
| `public_b2b` | ✅ only if `consent.basis=inferred_business` **and** contact is a conspicuously published, role-relevant business contact; every message carries unsubscribe; caps apply | 12 months | an *account*, not a lead — research + draft, human sends |
| `market_signal` | ❌ NEVER | 30 days, aggregated | fuels targeting/context only. **A signal is not a lead.** |

Hard rules enforced in code: `market_signal` cannot set `outreach_allowed=true` (schema-level);
a `public_b2b` contact can never be treated as residential consent; missing/unknown consent
fails closed (`outreach_allowed=false`); global suppression (STOP, unsubscribe, bounce,
do-not-contact) is checked before ANY proposal is even drafted; `external_send_allowed` flips
true only via owner verdict → LANGAR → EffectorGate, never by a producer or Leg.

## 3. Event contract (append-only, minimum set)

```
lead.candidate.received      lead.candidate.rejected      lead.normalized
lead.duplicate.detected      lead.qualified               lead.compliance_blocked
response.draft.prepared      quote.draft.prepared         proposal.routed
proposal.owner_approved      proposal.owner_edited        proposal.owner_rejected
effect.released              communication.sent           communication.failed
customer.replied             inspection.booked            quote.sent
quote.won                    quote.lost                   invoice.paid
outcome.recorded
```

Envelope for every event:

```json
{
  "event_id": "uuid", "event_type": "lead.qualified", "occurred_at": "ISO-8601",
  "correlation_id": "lead_id", "causation_id": "previous_event_id",
  "source_component": "LeadQualificationLeg", "schema_version": "1.0", "payload": {}
}
```

Owner verdicts (`proposal.owner_*`) are **internal quality signals**; market events
(`customer.replied` … `invoice.paid`) are **business outcome signals**. The Governor must never
conflate the two.

---

## 4. Path A — Manual `/lead` (activate Day 1; also the synthetic-test channel)

The Owner is the first producer. Any lead from any channel (missed call, Airtasker, referral,
someone at the paint shop) gets thumbed into Telegram in one message.

```
/lead sarah 0412345678 mosman interior 3br presale "wants quote before 9 aug open home" src:referral
/lead TEST|interior painting|Mosman        ← synthetic lead for the P0 acceptance test
```
- LLM parse (free-form; fields any order). Low parse confidence → clarify card, never a guess.
- → `candidate_type=consented_inbound`, `consent.basis=explicit` (they asked us),
  `outreach_allowed=true` → qualification → response draft → owner card.
- `/lead-fwd`: Owner forwards a screenshot/text of an inquiry; OCR+parse effector.
- Synthetic leads (`source.channel=synthetic_test`) traverse the FULL internal pipeline but are
  hard-blocked at EffectorGate (no external send possible, by type).
- **This path alone is enough to reach the first 20 outcomes. Nothing may block it.**

## 5. Path B — NSW Planning DA poller (activate Week 1)

Source verified 2026-07-21: NSW Planning Portal "Online DA Data API" — free open data,
statewide, no ToS risk (planningportal.nsw.gov.au/opendata).

Pipeline (n8n, daily 06:00):
1. Pull DAs updated in last 24h for `LGA_WHITELIST` (start 4–8 LGAs, not 40).
2. Filter `development_type` (alterations & additions, change of use; new dwellings off by
   default) and status per config.
3. Classify (LLM): painting-relevant? niche tag (reno-followup / fitout / heritage)? horizon.
4. Submit as **`candidate_type=market_signal`** → suburb/segment intelligence + weekly digest
   card ("14 approved renovations in your zone — 3 look paint-heavy").
5. Escalation to `public_b2b` only when a **business** applicant/builder is identifiable via a
   conspicuously published business contact — then Module 1's gated outreach flow may engage.
   **Private homeowners from DA records are NEVER cold-contacted** (privacy + Spam Act + brand
   damage travels fast in a suburb). The weekly digest card is the human gate for escalation.
   Volume guard: `MAX_DA_CANDIDATES_PER_WEEK = 10`.

## 6. Path C — Facebook Groups monitor via Apify (activate Week 2)

Highest warmth, highest ToS risk (Meta prohibits unauthorised automated collection — accepted
operating risk, mitigated as below). Verified: actors live (`apify/facebook-groups-scraper`).

Rules of engagement (non-negotiable, encoded):
1. **Read-only monitoring.** No auto-posting, no auto-DM, no auto-friending. Ever.
2. Actor runs 2×/day on `GROUP_WHITELIST` (10 suburb/community groups max at start).
3. Keyword prefilter (`painter, painting, gyprock, plaster, mould, end of lease, handyman,
   recommend`) → LLM classify {is_lead, intent, suburb, urgency, summary}.
4. Submit as `candidate_type=market_signal` with `consent.basis=none`, `outreach_allowed=false`.
   Octopus renders a card with a **suggested reply the Owner posts himself from his own
   profile**. The system never touches Facebook's write surface. When the person then contacts
   the business → Owner logs `/lead ... src:facebook` → THAT is the consented_inbound lead.
5. Data hygiene: store post text + link only while the card is open; purge on "Not a lead";
   never build a member-profile database.
6. Reply craft (LLM guidance): lead with usefulness ("that stain pattern usually means the
   leak's above the cornice — fix that first or paint won't hold"), then availability. The
   neighbour-who-knows tone wins; the salesman tone gets flagged by admins.

## 7. Activation order & error budget (Owner-approved rollout)

| Step | Action | Success gate before next step |
|---|---|---|
| 0 | Phase A runtime audit (Opus) — read-only | 00_RUNTIME_TRUTH.md delivered |
| 1 | Path A live + synthetic lead traverses full loop (no external send) | owner verdict recorded + outcome event observed |
| 2 | First REAL inbound via Path A → gated real send | reply/inspection tracked |
| 3 | Path B poller live (signals + weekly digest) | first digest triaged; junk < 50% |
| 4 | Path C monitor on 5 groups | false-positive ≤ 20%; expand to 10 |
| 5 | Module 1 outreach queue consumes escalated candidates | first PM walk-through booked |

Kill rule: any path > 50% junk cards for a week → fix-or-pause card from the Governor. Producers
never fail silently — 48h without a heartbeat submission raises an alert.

## 8. Minimal schema additions (extends prior `leads` table)
```
leads.candidate_type        text   -- consented_inbound | public_b2b | market_signal
leads.consent_basis         text   -- explicit | inferred_business | none | unknown
leads.outreach_allowed      bool   default false
leads.retention_class       text
leads.idempotency_key       text   unique
leads.first_response_at     timestamptz
suppression (channel_value, reason, created_at)   -- checked before every draft
quarantine (raw_payload, reason, received_at)     -- invalid submissions, never dropped
```
