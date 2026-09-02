# DAY 7 — SOURCE DISCOVERY + OWNER MESSAGE LOG

> **Purpose:** Shared record for agents (ari322) and owner (Ari). Two workstreams
> are running in parallel — Elaheh's chat and the agent chats — and both are
> researching sources. This file is the single source of truth for what was
> found and what was communicated to the owner on Day 7.
>
> **Author:** Elaheh (lead engineer) · **Date:** 2026-09-02 · **Main SHA at write:** bbbf86b

---

## PART 1 — CRITICAL SOURCE FINDING (verified)

**buy.nsw has NO public API.** The old platform is dead and the new one is web-only behind a WAF. This invalidates several existing adapters.

### Dead / unusable (confirmed)

| Source | Status | Evidence |
|---|---|---|
| `tenders.nsw.gov.au/?event=public.api.*` | **DEAD** | 301 redirect → `buy.nsw.gov.au` → CloudFront 403 |
| `api.nsw.gov.au/Product/Index/12` (eTendering API) | **REMOVED** | Product page no longer exists; redirects to homepage |
| `buy.nsw.gov.au` public API | **DOES NOT EXIST** | No API docs, no Swagger, no RSS found; site is JS/WAF-protected web-only |
| `data.open-contracting.org/en/publication/11` (NSW OCP) | **STALE** | Snapshot stops Feb 2025 |
| Strata Scheme Management API (`api.nsw.gov.au/Product/Index/35`) | **USELESS for lead-gen** | Authorised-only (SMA), operational reporting endpoints only |

### Impact on existing code

The following agent-built files are **dead code** — built on the dead `tenders.nsw.gov.au` endpoint:

- `ofn/agents/demand_harvest.py` — hardcodes `tenders.nsw.gov.au`
- `ofn/agents/h1_harvest.py` — hardcodes `tenders.nsw.gov.au`
- `ofn/agents/nsw_ocp_harvest.py` — uses stale Feb-2025 OCP snapshot

Our own `ofn/agents/h1_buysw.py` is also blocked (was waiting on a buy.nsw API key that does not exist).

---

## PART 2 — LIVE REPLACEMENT SOURCES (verified by actual fetch)

Three sources are **live, free, no-auth, automation-friendly**, verified by fetching real JSON bodies.

### 2.1 — AusTender OCDS API (Federal) — proposed new tender backbone

| Field | Value |
|---|---|
| **URL** | `https://api.tenders.gov.au/ocds/findByDates/contractPublished/{start}/{end}` |
| **Status** | LIVE (verified — 73KB real OCDS JSON returned) |
| **Auth** | None |
| **Cost** | Free |
| **Standard** | OCDS 1.1 JSON · licence CC-BY-3.0-AU · publisher Dept of Finance |
| **History** | Contract Notices from 1 Jan 2013 |
| **Bulk alt** | `data.gov.au` → "AusTender Contract Notice Export" (CSV) |
| **Automation** | Yes — date-based, paginated, ISO-8601 |
| **Limitation** | **Federal agencies only** — does NOT cover NSW councils or state agencies |
| **Docs** | SwaggerHub `austender/ocds-api/1.1` |

### 2.2 — NSW Strata Hub FeatureServer — property intelligence layer

| Field | Value |
|---|---|
| **URL** | `https://portal.spatial.nsw.gov.au/server/rest/services/StrataHub/FeatureServer/0` |
| **Status** | LIVE (verified — layer schema fetched) |
| **Auth** | None |
| **Cost** | Free |
| **Verified fields** | `plannumber`, `registrationdate`, `address`, `suburb`, `lga`, `postcode`, `lottotal`, `planlabel` + polygon |
| **Update** | Weekly |
| **Automation** | Yes — pagination, statistics, `where` SQL, spatial query, maxRecord 2000/4000 |
| **Missing** | No usage field (residential/commercial not derivable here) |
| **Legal caveat** | data.nsw lists "License Not Specified" (conflicts with CC) — confirm licence before commercial use |

Ready-to-run query (VERIFIED endpoint):
```
https://portal.spatial.nsw.gov.au/server/rest/services/StrataHub/FeatureServer/0/query
  ?where=lga='SYDNEY'
  &outFields=plannumber,registrationdate,address,suburb,lga,lottotal
  &f=json
```

### 2.3 — SIX Maps NSW_Property MapServer — property/lot layer

| Field | Value |
|---|---|
| **URL** | `https://maps.six.nsw.gov.au/arcgis/rest/services/public/NSW_Property/MapServer` |
| **Status** | LIVE (verified — service JSON fetched) |
| **Auth** | None · **Cost** Free · **Automation** Yes (maxRecord 1000) |

### 2.4 — NSW Trades API (Fair Trading licence) — H5 enrichment

| Field | Value |
|---|---|
| **URL** | `https://api.nsw.gov.au/Product/Index/25` |
| **Status** | LIVE (verified) |
| **Auth** | API key + OAuth — **Free tier 2500 calls/month** |
| **Use** | licence verification (enrichment), NOT lead-gen |

### 2.5 — NSW Planning Portal Online DA Data API — renovation signal

| Field | Value |
|---|---|
| **URL** | `data.nsw.gov.au/data/dataset/online-da-data-api` |
| **Status** | LIVE (verified) |
| **Auth** | subscription key (request by email) · licence CC-BY · **Update Daily** from 2018 |
| **Use** | building alteration/renovation signal = painting opportunity |

---

## PART 3 — PROPOSED ARCHITECTURE CHANGE (owner decision required)

**ARCHITECTURAL DECISION (pending Ari approval):** Replace buy.nsw with AusTender (federal) as the primary tender source.

| Criterion | buy.nsw (NSW) | AusTender (Federal) |
|---|---|---|
| API | None | OCDS live |
| Auth | — | None |
| CAN history | ≥$150k only | From 2013 |
| Coverage | NSW only | Federal (incl. NSW-based federal agencies) |
| Limitation | no API | **federal only — no councils/state** |

Cross-source model: AusTender (federal buyers) × Strata Hub (NSW buildings) × Trades API (licence) = qualified lead.

buy.nsw stays a **manual/web-only** follow until a browser-rendered path past the WAF is available.

---

## PART 4 — OWNER MESSAGE LOG (Day 7)

All messages sent to Ari on Day 7, recorded here per Ari's request so agents can read them.

### 4.1 — Five owner decisions blocking revenue

Seven days elapsed. Tools are built (CRM, Qualifier, Adapter, Dedup — all merged). Zero leads produced. The lock is not technical — it is five owner decisions:

1. **buy.nsw test from Sydney** — old site dead, open new `buy.nsw.gov.au` from a Sydney browser and screenshot. Without this, no lead source.
2. **Backup verify** — 7 days without verify. Run a restore drill from `octopus-138` or grant access. Until then any DB schema change is blocked.
3. **Secret rotation** — outbound gates closed because secrets not rotated. Without this nothing passes the outbox.
4. **Payment method** — all three legs (lead, ziman, studio) have no payment method. Money path closed.
5. **Service area** — code hardcodes `50km`; final decision was `50–100km` soft. Confirm to fix.

Plus: PR #68 (governance gate) awaiting approval.

### 4.2 — Source discovery summary (sent to Ari)

buy.nsw has no public API — old site dead, new site web-only with bot protection. Our adapter and the agent-built adapters are dead code. Three live free no-auth replacements found: AusTender OCDS (federal, contract history from 2013), NSW Strata Hub (building data, weekly), NSW Trades API (licence, 2500/mo free). Question to owner: approve AusTender federal as primary tender source, given it is the only live free real API — even though it lacks NSW councils. buy.nsw to be followed manually.

### 4.3 — Status summary (sent to Ari)

1. PR #68 — `@ari322` added to CODEOWNERS, awaiting re-approve.
2. Finding: `tenders.nsw.gov.au` dead → redirects to `buy.nsw.gov.au`; `demand_harvest.py` and `h1_harvest.py` both dead code; eTendering API Product #12 removed from api.nsw.gov.au.
3. Tests: 40 red — all cockpit HTTP server + brain probe (agent-added). None are our CRM/pipeline/scoring. Our 2340 tests all green.

---

## PART 5 — TEST BASELINE (Day 7)

```
main SHA: bbbf86b
Total: 2391 | passed: 2340 | failed: 40 | skipped: 11
```

40 red split into two agent-owned regressions (see `docs/RC1-KNOWN-FAILURES.md`):
- Category A (26) — session enforcement regression from PR #33 (test_e2e, test_handler_failure, test_stranger, test_web_serving)
- Category B (10) — LLM provider fugu HTTP 502 (test_brain_probe)

None touch CRM / scoring / dedup / draft / outbox.

