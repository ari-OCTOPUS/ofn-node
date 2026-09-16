# Live Verification Report — Sydney Painting Growth System
**Accessed:** 2026-07-21 (AEST) · **Method:** live web search + primary-source fetch
**Purpose:** Close the "Verified/Unverified" gaps in the three prior research passes before they feed the Master Blueprint, the P0 Legs, and Module 1.

Legend: ✅ CONFIRMED (primary source) · ⚠️ CORRECTED (prior claim wrong/stale) · ℹ️ DIRECTIONAL (secondary sources, treat as inference)

---

## 1. Marketplace landscape

| # | Claim in prior research | Verdict | What the live check found |
|---|---|---|---|
| 1.1 | "Oneflare is still active; test it with limited budget" | ⚠️ **CORRECTED** | **Oneflare was retired on 30 June 2026.** Airtasker (which acquired Oneflare for $9.8M) shut the brand; site/app now redirect to Airtasker. Any strategy referencing Oneflare as a live channel is void. The "Oneflare post-mortem" is now literal: the pay-per-lead model lost. |
| 1.2 | "Hipages still active, shared-lead complaints persist" | ℹ️ DIRECTIONAL | Hipages operates; tradie review platforms (ProductReview, Trustpilot) continue to show recurring complaints about lead cost/quality. Use as a *supplementary* channel only, never core. |
| 1.3 | "Airtasker for small handyman jobs" | ✅ CONFIRMED | Airtasker is now the consolidated marketplace (38k+ weekly tasks claimed post-Oneflare migration). |

**Impact on blueprint:** the "don't build another marketplace / own your demand" thesis is now *proven by market events*, not just argued.

## 2. Google ecosystem

| # | Claim | Verdict | Finding |
|---|---|---|---|
| 2.1 | "Google Local Services Ads = مستقیم‌ترین مسیر for painter leads in Sydney" (50-API list, item #35) | ⚠️ **CORRECTED** | **LSAs are NOT available in Australia** as of July 2026 — **confirmed against Google's own official Local Services Help page** ("Getting started with Local Services Ads", support.google.com/localservices/answer/6224841): available countries are "Austria, Belgium, Canada, France, Germany, Ireland, Italy, Spain, Switzerland, United Kingdom, United States". Australia absent. (Independent AU-market source agrees.) Anyone selling "Google Guaranteed setup in AU" is selling vapor; "Google Guaranteed" badge rebranded to "Google Verified" (late 2025) in eligible countries. **Remove LSA from the Sydney plan; substitute Google Ads + GBP + local SEO.** Quarterly watch trigger for AU launch. |
| 2.2 | GBP API, Places API, Google Ads API available | ✅ CONFIRMED | Standard availability; no change. |

## 3. Property data

| # | Claim | Verdict | Finding |
|---|---|---|---|
| 3.1 | Domain Developer API open for listing data | ✅ CONFIRMED (with conditions) | developer.domain.com.au live, tiered plans by industry/volume. Public listing + agent/agency search endpoints accessible. **Conditions:** "powered by Domain" attribution, backlinks to listings, analytics beacon, agent contact must remain visible. Agency *performance/enquiry* data requires the agency's own OAuth consent — irrelevant to Module 1 (we only need public listing + listing-agent identity). |
| 3.2 | NSW Planning Portal "Online DA Data API" is free open data | ✅ CONFIRMED | Dataset + API + data dictionary published on planningportal.nsw.gov.au opendata (mirrored on data.nsw.gov.au / data.gov.au). Statewide DA records since 2019+. Zero licence cost, zero ToS risk. **This is the safest automated ingestion source — wire it first among the automated paths.** |
| 3.3 | PropTrack / CoreLogic (Cotality) APIs | ℹ️ DIRECTIONAL | Portals exist; access is partner/commercial-grade. Defer to P2 — not needed for MVO. |

## 4. Compliance (the ones that bite)

| # | Claim | Verdict | Finding |
|---|---|---|---|
| 4.1 | "NSW painting licence needed above ~$5k" | ✅ CONFIRMED + **NUANCE** | Contractor licence required for residential painting **> $5,000 labour+materials incl. GST**. **Exemption since 2015: stand-alone contracts for *internal* paintwork need no licence** unless part of other home building work. Penalties: up to $22,000 (individual) / $110,000 (company) under Home Building Act 1989. → Quote-Draft Leg must branch on internal-only vs external/mixed scope. |
| 4.2 | "Twilio SMS — just wire it" | ⚠️ **CORRECTED (time-critical)** | **ACMA SMS Sender ID Register: from 1 July 2026** (already in force), alphanumeric sender IDs that are not registered get **over-stamped "Unverified"** by telcos — your branded SMS will literally arrive labelled like a scam. Action for MVO: **either register your sender ID via your SMS provider (ClickSend/MessageMedia/Twilio route through carrier) or send from a dedicated virtual mobile number (no alpha tag)**. This must be a config decision before the first Speed-to-Lead SMS. |
| 4.3 | Spam Act 2003 rules | ✅ CONFIRMED | Commercial electronic messages need consent (express or inferred), sender identification, functional unsubscribe. **Inferred consent** covers (a) existing customer relationships and (b) B2B addresses *conspicuously published* where the message is *directly relevant to the recipient's role* — this is the lane Module 1 must stay in. **Address-harvesting software output is explicitly prohibited** — scraped bulk email lists are out; individually identified, role-relevant PM/agency contacts from public listings are the defensible pattern. ACMA enforcement is active (recent multi-$100k penalties across sectors). |
| 4.4 | Do Not Call Register | ✅ CONFIRMED | Applies to voice telemarketing to registered numbers. B2B outreach to business numbers generally lower-risk, but wash outbound call lists against DNC. SMS is governed by Spam Act (4.3), not DNC. |
| 4.5 | Facebook Groups scraping via Apify | ✅ tool exists / ⚠️ risk stands | Multiple live Apify actors (incl. `apify/facebook-groups-scraper`). Meta ToS prohibits unauthorised automated collection → account/legal risk is real. Mitigation in spec: read-only monitoring, no auto-posting, no auto-DM, human posts every reply from their own account, no storage of personal data beyond the lead card. |

## 5. Ops tooling

| # | Claim | Verdict | Finding |
|---|---|---|---|
| 5.1 | ServiceM8 REST API | ✅ CONFIRMED | developer.servicem8.com live: REST + OAuth, jobs/quotes/clients objects. Fine as the job-management effector later; not required for MVO. |
| 5.2 | n8n self-hosted as orchestrator | ✅ CONFIRMED | Unchanged; used in Module 1 deliverable. |

---

## Net deltas the Master Blueprint must absorb

1. **Delete LSA from the Sydney channel plan** (not available in AU). Replace with Google Ads + GBP.
2. **Delete Oneflare everywhere** (retired 30 Jun 2026). Marketplace tier = Airtasker + Hipages (supplementary only).
3. **SMS sender identity decision is now a Day-0 task** (ACMA register in force since 1 Jul 2026).
4. **Quote-Draft Leg needs the licence branch** (internal-only exemption vs >$5k licensed work).
5. **Module 1 outreach stays strictly in the inferred-consent B2B lane** — individually identified, role-relevant contacts; no harvested bulk lists; unsubscribe in every message.
6. **NSW DA open data is the first automated ingestion source to wire** (free, legal, zero ToS risk).

## Sources (accessed 2026-07-21)

- Airtasker Support — "Oneflare has retired": https://support.airtasker.com/hc/en-au/articles/59294413002393
- Airtasker Blog — Oneflare acquisition ($9.8M): https://www.airtasker.com/blog/airtasker-acquires-oneflare/
- Google (official) — Getting started with Local Services Ads (country availability list): https://support.google.com/localservices/answer/6224841
- SearchScope — LSA availability in Australia (2026, corroborating): https://searchscope.com.au/local-seo/google-local-service-ads-for-businesses/
- NSW Government — Painting work licensing: https://www.nsw.gov.au/business-and-economy/licences-and-credentials/building-and-trade-licences-and-registrations/painting-work
- ACMA — SMS Sender ID Register rules: https://www.acma.gov.au/sms-sender-id-register-rules-telcos
- ACMA — Avoid sending spam: https://www.acma.gov.au/avoid-sending-spam
- NSW Planning Portal — Online DA Data API: https://www.planningportal.nsw.gov.au/opendata/dataset/online-da-data-api
- Domain Developer Portal + FAQ: https://developer.domain.com.au/ · https://developer.domain.com.au/docs/v2/support/faq/
- Apify — Facebook Groups Scraper: https://apify.com/apify/facebook-groups-scraper
- ServiceM8 Developer Portal: https://developer.servicem8.com/
- Hipages reviews (directional): https://www.productreview.com.au/listings/home-improvement-pages · https://au.trustpilot.com/review/hipages.com.au
