# Painting Phone Lead to Quote Checklist v2
Updated: 2026-08-06

Purpose: step-by-step path so Armin receives a customer/job on phone, captures all required data, prepares price safely, and manages follow-up.

0 Health/access:
- OFN active; panel and lead health OK.
- backup server 8765 stopped.
- OFN_WIRE_OUTBOUND=0.
- Armin numeric Telegram ID in OFN_OWNER_USER_IDS and OFN_PARTNER_USER_IDS_LEAD.
- Bot token statuses checked without values.

1 Phone intake order:
- Customer: name, mobile, email, preferred contact, lead source.
- Location: suburb/postcode, address when needed, property type, decision maker.
- Scope: interior/exterior/both, rooms/areas, surfaces, dimensions, ceiling height.
- Condition: cracks, holes, peeling, mould, water damage, sanding/patching.
- Evidence: photos, video walkthrough, floor plan, site visit flag.
- Materials: supplied by whom, paint quality, finish, brand preference.
- Timing: desired start, deadline, urgency, occupied/vacant, access hours.
- Qualification: budget, other quotes, decision maker, desired next step.
- Risks: height, strata, asbestos/lead paint, insurance/licence docs.

2 Pricing states:
- estimate_needed
- rough_range
- draft_quote
- site_visit_required
- owner_approved_quote
- sent

Every price must show scope, inclusions, exclusions, assumptions, material policy, estimated duration, confidence, and next action.

Force site_visit_required when access/height is unclear, damage exists, strata/commercial is complex, photos are missing for large jobs, or fixed price is requested with insufficient data.

3 Code completion:
- Data model: contact, location, scope, condition, evidence, materials, timing, budget, risks, pricing_state, quote fields, assumptions, exclusions, follow_up.
- API: create/update lead, save intake step, missing-info, quote draft, site visit flag, follow-up, owner approval, partner-safe entry.
- UI: mobile wizard, owner pipeline, missing-info card, pricing card, confidence warning, Flight Deck help labels.
- Tests: pricing math, missing-info, site-visit rules, store persistence, owner/partner permissions, no outbound when WIRE_OUTBOUND=0, UI markers.

4 Debug loop: backup, compile, targeted tests, full tests, restart, health, logs, DB check, update Obsidian, ask Armin next single question.
