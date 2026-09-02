# DAY 7 — COWORK RESEARCH: Live Source Discovery (full report)

> **Purpose:** Complete, unedited research output from Cowork on live NSW +
> Federal + local procurement and property data sources for Master Painting
> lead generation. Every source labelled "actually fetched" was retrieved with
> a real curl/fetch and its body inspected.
>
> **Author:** Cowork research agent · Compiled by Elaheh · **Date:** 2026-09-02
> **Context prompt:** "We can work as a builder for building and construction."

---

## VERDICT SUMMARY (highest value first)

Three sources are **open, free, no-auth, automation-friendly**, live right now,
with real JSON bodies fetched:

1. **AusTender OCDS API (Federal)** — the only live real contract API found.
   Historical CAN from 2013.
2. **NSW Strata Hub FeatureServer** — strata layer with `registrationdate` +
   `lga` + `lottotal` + `address`. Exactly what the `service_area` gate needs.
3. **SIX Maps NSW_Property MapServer** — statewide property/lot layer.

Bad news: **buy.nsw has no verified public API** and sits behind a WAF. The
automatable NSW-procurement path is via **Federal (AusTender) + register web**,
not a buy.nsw API.

---

## PART 1 — buy.nsw

| Field | buy.nsw Register of Notices | NSW eTendering (old) |
|---|---|---|
| **URL** | `https://buy.nsw.gov.au/notices` · `?noticeTypes=can` | `tenders.nsw.gov.au/...event=public.api.*` |
| **Status** | **LIVE (web)** | **DEAD** |
| **Verified how** | actually fetched — empty body (WAF/JS-rendered) + docs search | confirmed by owner + stale GitHub |
| **Data type** | Web-only + manual download (by agency/date/type) | — |
| **Auth** | None (but bot-protected) | — |
| **Cost** | Free | — |
| **Categories** | CAN/SON/PP construction/maintenance | — |
| **Update** | ~real-time (CAN, 45 days after contract) | — |
| **Automation** | **No/Partial** — WAF, no documented API; needs rendered browser | No |
| **Notes** | CAN only for ≥$150k. CSV/Excel download exists but endpoint could not be captured from behind the WAF (no Chrome attached). **UNKNOWN: whether an up-to-date OCDS download exists.** |

---

## PART 2 — AusTender (Federal) — proposed backbone

| Field | Value |
|---|---|
| **Source** | AusTender OCDS Search API |
| **URL** | `https://api.tenders.gov.au/ocds/findByDates/contractPublished/{start}/{end}` · `/findById/CN...` · `contractStart` / `contractEnd` / `contractLastModified` |
| **Status** | **LIVE** |
| **Verified how** | **actually fetched** — 73KB of real OCDS JSON (`publisher: Department of Finance`, `license: CC-BY-3.0-AU`, `version 1.1`, `releases[]`) |
| **Data type** | REST API (OCDS 1.1 JSON) + bulk CSV on data.gov.au ("AusTender Contract Notice Export") |
| **Auth** | **None** |
| **Cost** | **Free** |
| **Categories** | all federal CN; filterable by UNSPSC/category (painting/building/facility maintenance) |
| **Update** | near real-time; data from **1 Jan 2013** |
| **Automation** | **Yes** — AWS serverless, date-based, paginated, ISO-8601 |
| **Notes** | This is the "historical CAN" identified as the main gap — at the federal level. A 2-week window returned little painting; for volume use a long window + category filter. Docs: SwaggerHub `austender/ocds-api/1.1`. |

---

## PART 3 — Other open sources

| Source | URL | Status | Verified | Auth | Automation |
|---|---|---|---|---|---|
| data.gov.au — AusTender CN Export (bulk) | `data.gov.au/data/dataset/austender-contract-notice-export` | LIVE | documentation | None | Yes (CSV) |
| data.gov.au — Historical Aus Gov Contract (OCDS) | `data.gov.au/.../historical-australian-government-contract-data` | LIVE | search-verified | None | Yes |
| NSW OCP OCDS snapshot | `data.open-contracting.org/en/publication/11` | **STALE (Feb 2025)** | owner-confirmed | None | Yes but stale |
| data.nsw procurement datasets | `data.nsw.gov.au/data/dataset?tags=procurement` | LIVE | search-verified | None | Partial |
| VendorPanel / Tenderlink / council portals | various | **UNKNOWN** | assumption | — | mostly web-only |

Honest note: VendorPanel and council portals were not deep-verified; mostly
web-only with WAFs, low automation value — **do not prioritise**.

---

## PART 4 — Strata / Property — key property intelligence

| Field | NSW Strata Hub FeatureServer | SIX Maps NSW_Property |
|---|---|---|
| **URL** | `https://portal.spatial.nsw.gov.au/server/rest/services/StrataHub/FeatureServer/0` | `https://maps.six.nsw.gov.au/arcgis/rest/services/public/NSW_Property/MapServer` |
| **Status** | **LIVE** | **LIVE** |
| **Verified how** | **actually fetched** — full `strataplan` layer schema | **actually fetched** — full service JSON |
| **Data type** | ArcGIS REST (JSON/geoJSON/PBF) | ArcGIS REST (JSON/geoJSON) |
| **Auth** | **None** | **None** |
| **Cost** | **Free** | **Free** |
| **Verified fields** | `plannumber`, `registrationdate`, `address`, `suburb`, `lga`, `postcode`, `lottotal`, `planlabel` + polygon | `Property`, `Urban_Property`, table `PropertyLot` |
| **Update** | Weekly | static-ish (© 2018) |
| **Automation** | **Yes** — pagination, statistics, `where` SQL, spatial query, maxRecord 2000/4000 | **Yes** — Query, maxRecord 1000 |
| **Notes** | Directly supplies roadmap signals: `registrationdate`=building age, `lottotal`=size, `lga`/`suburb`=service-area. **Missing:** no usage field (residential/commercial). **Legal caveat:** licence on data.nsw is "License Not Specified" (conflicts with CC) — confirm before commercial use. |

Ready-to-run query (VERIFIED endpoint):
```
https://portal.spatial.nsw.gov.au/server/rest/services/StrataHub/FeatureServer/0/query
  ?where=lga='SYDNEY'
  &outFields=plannumber,registrationdate,address,suburb,lga,lottotal
  &f=json
```

---

## PART 5 — Builder / Licence + Major Projects

| Source | URL | Status | Verified | Auth | Automation |
|---|---|---|---|---|---|
| **NSW Trades API** (Fair Trading licence) | `api.nsw.gov.au/Product/Index/25` | **LIVE** | **actually fetched** | API key + OAuth (**Free 2500/mo**) | **Yes** |
| verify.licence (web fallback) | `verify.licence.nsw.gov.au/home/Trades` | LIVE | search-verified | None | Partial (web) |
| **NSW Planning Portal — Online DA Data API** | `data.nsw.gov.au/data/dataset/online-da-data-api` | **LIVE** | **actually fetched** | subscription key (email request) | **Partial** |
| Planning Portal Spatial Viewer / DA open data | `planningportal.nsw.gov.au/opendata` | LIVE | search-verified | None/key | Partial |

Trades API: `Verify`/`Browse`/`Details` endpoints, licence-verification only —
**enrichment (H5)**, not lead-gen. Online DA API: CC-BY, **Daily**, from 2018 —
building alteration/renovation signal (painting opportunity), but needs a key.

---

## VERIFIED vs ASSUMPTION — explicit split

**VERIFIED (body actually fetched):**
- AusTender OCDS API live and open, CAN from 2013.
- Strata Hub FeatureServer with those 8 fields, no auth, weekly.
- SIX Maps NSW_Property live and queryable.
- Trades API live, Free 2500/mo.
- Online DA API live, CC-BY, daily.
- buy.nsw/notices returned an empty body from behind the WAF (JS/bot-protected).

**ASSUMPTION / UNKNOWN:**
- Freshness of buy.nsw's own OCDS download (WAF blocked; no Chrome attached).
- Existence of any public API for buy.nsw (none found → assumption: none).
- Exact painting category coverage in AusTender (needs UNSPSC filter over a long window).
- Usage field in Strata Hub (absent → residential/commercial not from this source).
- VendorPanel/council feeds.

---

## SYSTEM WIRING (no over-engineering)

Three connectors, aligned with the existing pipeline (`H1→I1→I3`):
- **AusTender OCDS** → federal CAN/RFT source (live replacement for the dead buy.nsw API).
- **Strata Hub FeatureServer** → real geo/age/size gate (fixes the decorative `service_area`).
- **Trades API** → H5 verification.

Keep buy.nsw NSW-specific as **web-only/manual** until Chrome is attached and the
CSV download path behind the WAF can be captured.

---

## SOURCES

- AusTender OCDS API — GitHub README: `github.com/austender/austender-ocds-api/blob/master/README.md`
- AusTender OCDS Swagger: `app.swaggerhub.com/apis/austender/ocds-api/1.1`
- buy.nsw Register of notices: `buy.nsw.gov.au/notices`
- NSW Strata Hub — Data.NSW: `data.nsw.gov.au/data/dataset/1-cb153150a28c4f40b66b682e7dc3ff86`
- NSW Strata Hub FeatureServer: `portal.spatial.nsw.gov.au/server/rest/services/StrataHub/FeatureServer`
- SIX Maps NSW_Property MapServer: `maps.six.nsw.gov.au/arcgis/rest/services/public/NSW_Property/MapServer`
- NSW Trades API — api.nsw: `api.nsw.gov.au/Product/Index/25`
- Online DA Data API — Data.NSW: `data.nsw.gov.au/data/dataset/online-da-data-api`
