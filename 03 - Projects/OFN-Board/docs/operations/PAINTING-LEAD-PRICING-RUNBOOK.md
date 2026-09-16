# Painting Lead to Phone Intake to Pricing Runbook
Updated: 2026-08-06

Goal: lead arrives on Armin phone, gets qualified, priced, quoted, and tracked.

Phase 1 Access/health:
- Check ofn active, panel health, lead health.
- Confirm port 8765 backup server stopped.
- Add Armin numeric Telegram ID to OWNER and LEAD allowlists.
- Confirm bot token status without printing values.

Phone intake order:
1. Customer name, phone, email, preferred contact, source.
2. Suburb/postcode, property type, decision maker, access.
3. Interior/exterior, rooms/areas, surfaces, dimensions.
4. Condition: cracks, holes, peeling, mould, water damage.
5. Photos/video/floor plan and whether site visit is required.
6. Materials, finish, paint supplier, brand preference.
7. Timing, deadline, occupied/vacant, working hours.
8. Budget, other quotes, urgency, next step.
9. Risks: height, strata, lead paint, asbestos, insurance/licence docs.

Pricing states:
- estimate_needed
- rough_range
- draft_quote
- site_visit_required
- owner_approved_quote
- sent

Every price needs scope, assumptions, exclusions, materials, duration, confidence, next action.
Force site_visit_required for uncertain access, damage, complex strata/commercial, missing photos on large jobs.

Code completion checklist:
- Data model: customer, scope, pricing_state, assumptions, exclusions, follow_up, photos, site_visit flag.
- API: create/update lead, incremental intake, quote draft, quote state, follow-up, owner-only sensitive routes.
- UI: phone-friendly intake card, question wizard, pricing card, missing-info checklist, Flight Deck labels.
- Tests: math, store, owner API, partner permissions, no outbound with OFN_WIRE_OUTBOUND=0.

Debug: compile, targeted tests, full pytest with TMPDIR, restart ofn, health checks, journal logs, DB schema check, rollback if needed.
