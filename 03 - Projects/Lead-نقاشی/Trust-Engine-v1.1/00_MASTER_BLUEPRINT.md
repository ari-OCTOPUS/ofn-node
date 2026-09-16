# OCTOPUS OS — MASTER BLUEPRINT v1.1
## Sydney Painting & Maintenance: Trust & Network Engine
**Date:** 2026-07-21 (v1.1 same day — external architecture review applied) · **Audience:** Opus co-worker agent (architect) + Owner
**Supersedes & consolidates:** (a) the network-playbook blueprint (renamed: **Premium Trust-and-Response playbook** — the model is defined by measurable behaviours, not nationality), (b) 50 API/MCP source list, (c) 5-company reverse-engineering + market map. Where those documents conflict, THIS document rules.
**Companion files:** `01_VERIFICATION_REPORT.md` · `legs/` (module specs) · `lead_inbox/LEAD_INBOX_SPEC.md` (canonical contract v1.1) · `module1_b2b_infiltrator/*` · `OPUS_MISSION_PROMPT.md`
**v1.1 corrections applied (reviewer, accepted):** n8n stripped of all gate/approval/outbound access; candidate taxonomy `consented_inbound|public_b2b|market_signal` made canonical; P0 re-sliced funnel-first; licensing decisions fail-closed; synthetic-lead milestone precedes any real send.

---

## 1. Mission (one paragraph, non-negotiable)

We are not building a marketplace, a directory, or a lead reseller — that model just died in
public (Oneflare retired 30 Jun 2026; see §2). We are building a **Trust & Network Engine** for
one Sydney painting & maintenance business: software that reproduces the four behaviours of the
market's proven winners — closed B2B networks, sub-5-minute articulate response, premium
presentation, and community presence — under a strict human-approval gate (Octopus invariants
I1–I10). Win on trust and speed, never on price.

## 2. Verified reality (deltas every prior document must absorb)

Full sourcing in `01_VERIFICATION_REPORT.md` (accessed 2026-07-21).

| # | Fact | Consequence |
|---|---|---|
| R1 | **Oneflare retired 30 Jun 2026**; brand folded into Airtasker | Remove from all plans. The pay-per-lead post-mortem is settled history — validates the whole owned-demand thesis. |
| R2 | **Google LSA not available in Australia** (eligibility list excludes AU) | Delete LSA line from channel plan (50-list item #35 void for Sydney). Budget goes to Google Ads + GBP. Quarterly re-check trigger. |
| R3 | **ACMA SMS Sender ID Register in force since 1 Jul 2026** — unregistered alpha sender IDs get stamped "Unverified" | Day-0 decision: dedicated virtual number (default) or registered sender ID. Branded-looking SMS without registration now actively harms trust. |
| R4 | **NSW licence:** residential painting > $5k needs contractor licence; stand-alone *internal* paintwork exempt since 2015; fines $22k/$110k | Reference facts only — **the system never auto-decides licence applicability.** Quote flow fails closed: uncertain → `quote_status=REQUIRES_LICENCE_REVIEW`, external send blocked until Owner confirms. Licence number on every asset regardless (trust). |
| R5 | **Spam Act lanes confirmed:** inbound reply ≠ unsolicited; existing customers = inferred consent; B2B = published, role-relevant contacts only; harvested lists prohibited; ACMA enforcement active | Consent taxonomy is enforced structurally in the Lead Inbox (`consent_basis` field), not by goodwill. |
| R6 | **NSW Planning Online DA API** = free, open, statewide | First automated ingestion source (Path B). |
| R7 | **Domain API live, tiered**, public listing + agency data OK with attribution; enquiry data needs agency OAuth (not needed) | Module 1 feasible as designed. Fallback = manual agency entry if plan access stalls. |
| R8 | Apify FB Groups actors live; Meta ToS risk unchanged | Path C runs read-only with human-posts-everything protocol. |

## 3. Stack ruling (resolves the n8n-vs-Python contradiction)

The three research passes flip-flopped between n8n/Make/GHL and custom Python. Ruling:

```
┌─────────────────────────────────────────────────────────────┐
│  OCTOPUS (custom Python) = BRAIN + LEDGER + GATE + VOICE    │
│  • Ingestion boundary POST /api/v1/lead-candidates          │
│    (HMAC + timestamp + nonce + idempotency, fail-closed)    │
│  • Normalise → dedupe → classify → consent firewall         │
│  • Qualification, drafting, Proposal Router                 │
│  • Telegram approval surface — Octopus's OWN bot renders    │
│    cards and receives verdicts                              │
│  • Human verdict → LANGAR append → EffectorGate →           │
│    Octopus-owned outbound worker (the ONLY send path)       │
│  • Outcome events → Governor learning                       │
├─────────────────────────────────────────────────────────────┤
│  n8n (self-hosted) = COLLECTION LIMBS ONLY                  │
│  • Pollers (Domain, NSW DA, Apify runs), parsing, glue      │
│  • ALLOWED:   signed POST /api/v1/lead-candidates           │
│  • FORBIDDEN: /gate/*, approval callbacks, Telegram cards,  │
│    Twilio/SendGrid outbound, LANGAR, release, settlement    │
│    (see module1_b2b_infiltrator/n8n_wf2_REMOVED_README.md)  │
├─────────────────────────────────────────────────────────────┤
│  Dropped for MVO: GoHighLevel, Make, HubSpot (revisit ≥P2   │
│  only if a concrete gap appears). ServiceM8 = P2 effector.  │
└─────────────────────────────────────────────────────────────┘
```

One send path means one audit trail, one suppression list, one place invariants live. External
automation can only *propose through the signed boundary*; nothing outside Octopus holds a
capability that could touch the world. Required negative test: n8n has no gate credentials and
no reachable gate endpoint.

## 4. Lead ingestion — three paths, Day-1 wiring (Owner decision 2026-07-21)

Contract + full rules: `lead_inbox/LEAD_INBOX_SPEC.md`.

| Path | Source | candidate_type | Activation | Guard |
|---|---|---|---|---|
| A | Manual `/lead` + `/lead-fwd` (Telegram); also carries the synthetic test lead | consented_inbound | **Day 1** | none — this path must never block |
| B | NSW Planning DA poller (open data) | market_signal → weekly digest → owner-escalated public_b2b | Week 1 | homeowners never cold-contacted; ≤10 escalations/week |
| C | FB Groups monitor (Apify, read-only) | market_signal → card → owner posts reply himself | Week 2 | no auto-post/DM ever; purge non-leads; ≤10 groups |

Consent firewall (structural, schema-enforced): `market_signal` can never set
`outreach_allowed=true`; only `consented_inbound` and qualifying `public_b2b`
(`consent.basis=inferred_business`, published role-relevant contact) can produce outreach
drafts — the latter solely through Module 1's capped, unsubscribe-carrying flow. **A signal is
not a lead. A public business is not residential consent. Missing consent fails closed.**

## 5. P0 — the funnel engine (re-sliced v1.1, funnel-first)

P0 is the smallest auditable closed loop, not a content factory. Four components; all
propose-only; all outcomes event-recorded.

| P0 component | Responsibility | Spec source |
|---|---|---|
| **LeadInboxLeg** | signed ingestion boundary, validation, HMAC/nonce/idempotency, classification, quarantine — never sends | `lead_inbox/LEAD_INBOX_SPEC.md` §0–§3 |
| **LeadQualificationLeg** | service/suburb/urgency/fit/value scoring, missing-question detection, compliance & licensing risk flags → Proposal only | contract §1 `qualification` block |
| **ResponseQuoteLeg** | first-response draft + inspection options; quote draft only when information suffices; states assumptions; never invents prices/licences/credentials; never sends | `legs/LEG_P0-1_speed_to_lead.md` (response) + `legs/LEG_P0-2_quote_draft.md` (quote) |
| **OutcomeAttributionLeg** | full funnel tracking: received → qualified → delivered_to_owner → verdict → sent → delivered → replied → inspection_booked → quote_sent → won/lost → paid → gross_profit → repeat/referral. **Owner verdicts = internal quality signal; customer response & payment = market outcome signal. Never conflated.** | event contract, `lead_inbox/LEAD_INBOX_SPEC.md` §3 |

Reclassified to **P1** (reviewer correction, accepted): `review_request` and `case_study`
(specs retained in `legs/`, nothing wasted). Pull-forward exception the Owner may exercise:
`review_request` consumes `job.completed` events from the EXISTING business — it does not
depend on the new funnel — so if jobs are completing weekly today, it may be activated early
as a config decision, consciously trading build focus for review velocity.

**Milestone order (binding):**
1. **Synthetic loop:** `/lead TEST|interior painting|Mosman` → inbox → qualify → draft →
   owner card → verdict → outcome event. **No external message of any kind.**
2. **First real inbound** (Path A) → gated real send → reply/inspection tracked.
3. **Twenty real outcomes** — funnel data (sent, replied, inspection, quote, won/lost, paid,
   lost-reason), not merely owner verdicts — before ANY discovery/content agent is built.

## 6. Module 1 — B2B Infiltrator (the network moat)

Full design: `module1_b2b_infiltrator/MODULE1_API_MAPPING.md` + two importable n8n workflows.
Persona A: property managers (end-of-lease 48–72h pack — vacancy-day compression). Persona B:
sales agents (pre-listing refresh). Discovery via Domain listings API in 4–8 premium suburbs;
enrichment to *published office contacts only*; LLM-drafted peer-tone intro; Telegram card;
Octopus sends after approval. Caps: 5 new agencies/day, 1 follow-up max, quarterly value-add
after that. Success gate: ≥15% reply rate at n=40 before any volume increase.
**This module is the software implementation of the closed-referral-network behaviour: few, warm, specific, relentless.** (v1.1: n8n ends at the signed ingestion boundary; card, verdict and send are Octopus-owned — see `n8n_wf2_REMOVED_README.md`.)

## 7. Trust asset backlog (from the 5-company DNA — build order)

The ten shared patterns of the reverse-engineered winners, sequenced:

| When | Asset | Source pattern |
|---|---|---|
| Day 0–7 | Licence + ABN + insurance on every surface; owner face/name/number; SMS sender identity fixed (R3) | all five; Upscale |
| Day 0–7 | Written guarantee stack (G1–G5) as reusable quote blocks | Upscale |
| Week 2–4 | GBP hygiene: categories, service areas, weekly photo, Q&A seeded, 100% review replies | all five |
| Week 2–6 | First 5 suburb-named case studies + before/after pairs (Leg P0-4 output) | Upscale, Brushworks |
| Week 4–8 | Transparent pricing page (bands per room/house type) + 2 niche pages (end-of-lease patch+paint; mould-resistant bathroom) | Upscale pricing; Brushworks niches |
| Week 6–10 | PM/strata capability one-pager (PDF) fed by case-study library | Higgins ABM |
| Quarter 2 | ROI story page (real numbers only), climate/seasonal content, Dulux accreditation pursuit | Brushworks; Upscale; all five |

## 8. Channel plan (post-verification)

| Tier | Channel | Role | Note |
|---|---|---|---|
| Core | GBP + Maps | primary inbound | review velocity from P0-3 is the ranking engine |
| Core | Google Ads (3 campaigns: painter-near-me/suburbs; end-of-lease+gyprock; pre-sale) | paid intent | LSA does NOT exist in AU (R2) — no substitute badge claims |
| Core | Module 1 B2B | recurring revenue | the moat |
| Support | Website quote form + `/lead` funnel | capture | forms feed Path A automatically later |
| Support | FB groups (Path C) | warm community | human-posted only |
| Supplementary | Airtasker (small jobs), Hipages (filtered trial only) | volume filler | Oneflare gone (R1); never core spend |
| Watch | LSA availability AU · PropTrack/Cotality APIs · ServiceM8 sync | quarterly review card | auto-created by Governor |

## 9. Compliance guardrails (operational, all verified)

1. Every outbound: business identification + functional opt-out; STOP/unsubscribe →
   suppression table → hard block in Inbox (not in Leg logic).
2. SMS: sender-ID decision per R3; quiet hours 07:30–20:30; inbound replies exempt.
3. B2B outreach: published role-relevant contacts only; no harvested lists (Spam Act
   prohibition); ≤5 new/day; DNC wash before any voice call.
4. DA/listing data: `signal_only` → never contact homeowners; agents/agencies only.
5. FB: read-only monitor, human posts, purge non-leads, no member profiling.
6. Licence display everywhere; licensing decisions fail closed per R4 (`REQUIRES_LICENCE_REVIEW`
   blocks send; same fail-closed rule for lead paint, asbestos, waterproofing, electrical,
   plumbing, working-at-heights/rope access, mould remediation — flagged, never auto-cleared);
   no incentivised reviews (Google policy / ACL); ROI claims only with real consented figures;
   photos suburb-only + EXIF stripped.
7. Privacy: collect the minimum, state the purpose, delete on request; suppression survives
   everything.

## 10. Governor & KPIs (what "learning" concretely means)

Weekly Governor card (KEEP/FIX/SCALE/STOP per channel and per Leg) computed from:

- **Speed:** time-to-first-response p50/p95 (target 5min/30min business hours)
- **Conversion:** lead→inspection, inspection→quote, quote→win %, by channel × suburb × niche
- **Trust velocity:** reviews/month, rating, % replied, case-study assets/month
- **Network:** PM replies, walk-throughs, first jobs, repeat jobs per agency
- **Economics:** revenue per channel, est. gross margin per niche, cost per won job
- **Hygiene:** junk-card rate per source (>50%/week → fix-or-pause card), suppression growth

Wiring requirement (was the missing link): `record_proposal_outcome()` events MUST flow into
`goal_directed.measure()` — the Governor reads outcomes, not intentions. `/won` `/lost`
`/meeting` `/dead` owner commands are part of the product, not admin chores.

## 11. Rollout — audit-first, synthetic-first (v1.1 order)

| Phase | Deliverable | Exit gate |
|---|---|---|
| 0. Audit | Opus Phase A read-only runtime reconciliation (branch truth, flags, STOP anomaly, router liveness) — see `OPUS_MISSION_PROMPT.md` | `00_RUNTIME_TRUTH.md` delivered; every stage classified LIVE/SHADOW/DISCONNECTED/… |
| 1. Contracts | Opus Phase B: contracts + state machines + threat model reviewed by Owner | contracts approved |
| 2. Synthetic loop | P0 four components in isolated worktree; `/lead TEST\|interior painting\|Mosman` traverses full internal pipeline; suppression + quarantine live; SMS identity decided (R3) | synthetic DoD met; ZERO external sends; replay-safe |
| 3. First real lead | Path A live; one real inbound → card → approve → gated send → reply tracked | first market response recorded |
| 4. Widen intake | Path B poller + weekly digest; then Path C on 5 groups | digest junk <50%; FB false-positive ≤20% |
| 5. Module 1 | WF1 imported (signed submission only), Domain plan active, first 5 candidate cards | ≥1 approved outreach, ≥1 walk-through |
| 6. Operate | Tune prompts from Owner edit-diffs; Governor v0 weekly card | **20 real outcomes with funnel data** |
| 7. Only then | P1 backlog (review/case-study activation if not pulled forward, suburb-page factory, niche pages, follow-up leg, PM cadence, strata pack) — each unlocked by Governor evidence, not enthusiasm | — |

## 12. Risks & open questions (Owner answers when convenient)

1. **Capacity honesty:** speed-to-lead marketing writes cheques the crew must cash. What is
   realistic weekly job capacity? (Feeds a capacity guard on how many leads we *pursue*.)
2. **Licence & insurance state:** confirm current NSW licence class/number + insurance cover
   figures for templates (R4 branch depends on it).
3. **Review link:** GBP review short-link needed before P0-3 goes live.
4. **Domain plan tier:** confirm entry-tier quota covers 8 suburbs × 2 listing types daily;
   else halve suburbs (quality over coverage).
5. **Sequence-approval policy:** P0-3 default is one approval per cadence (see leg file). If
   invariants demand per-message gating, set `REVIEW_SEQ_MODE=per_message` and accept the
   friction consciously.
6. **Apify budget & FB account risk appetite** for Path C (can start Path C paused if unsure —
   Paths A+B alone can hit the 20-outcome gate).

---
*Build the small loop. Feed it real leads. Let outcomes, not documents, vote on what gets built next.*
