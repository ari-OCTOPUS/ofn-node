# Handoff — H1 buy.nsw Adapter (Day 5)

Start from repo clone. Branch work/h1-buysw off canonical c1969bce.
Read this before touching source adapters.

Files added this session:
- ofn/agents/h1_buysw.py — buy.nsw OCDS adapter (read-only, stdlib only)
- tests/test_h1_buysw.py — 9 acceptance tests
- tests/fixtures/buysw/ — schema_example.json + synthetic_tenders.json + README.md

commit: 4fcd773 (local only — push BLOCKED, see below)

## Update 2026-08-31 — H1 adapter built, fixture-driven

- **H1 buy.nsw adapter done (fixture-driven).** Parses NSW eTendering OCDS
  releases into painting_tenders fields via LeadStore.create_tender().
  Deterministic filter: keyword + UNSPSC + Sydney regions + min value $400.
  build_score_inputs() maps to tender_score P/G/E/D/M/Q/R/C (all 0-1).
- Tests: **9 passed, 1 skipped** in test_h1_buysw.py; full suite
  **2144 passed** (was 2135), **zero regression** from this change.
- **The 1 skip is intentional** — test_golden_vector_filter needs a REAL
  API response, which we do not have. Per tests/fixtures/README.md rule
  (anything that generates its own test input is validating itself), filter
  logic stays UNSPOKEN (skipped, not green) until a golden vector arrives.

- **OCDS field mapping (verified against official schema example):**
  tender.RFTUUID -> tender_id (lead:tender:buysw:<uuid>) ·
  tender.title -> title · buyer.name -> buyer_name ·
  tender.deliveryLocation.gazetteer.Identifiers[] -> location ·
  tender.tenderPeriod.endDate -> closing_at ·
  tender.value.amount -> min-value filter ·
  tender.items[].classification.id -> UNSPSC filter.
- Sydney service regions (from OCDS xNSWRegions): Sydney, Cumberland/Prospect,
  Nepean, Northern Sydney, Inner West, South East Sydney, South West Sydney,
  Central Coast, Illawarra, Hunter.
- UNSPSC: accept 72151300/01/02 (painting service), reject 31211500
  (paint product — supply, not service).

- **BLOCKED on push:** Elahe-z has no write access to ari-OCTOPUS/ofn-node
  (HTTP 403). Code is committed locally on work/h1-buysw but cannot be
  pushed. Armin must add Elahe-z as Write collaborator.
- **BLOCKED on real data:** api.nsw.gov.au needs an API key (free, but
  registration required). Old tenders.nsw.gov.au API is dead (301->403
  CloudFront). Armin to register for the key; then only the fetch layer
  gets wired to live data — parser/filter/score are already done.

- **AustralianTenders rejected (owner decision):** official API needs paid
  Core plan ($99/mo); site is a Vue SPA + Algolia whose internal endpoint
  needs a session (bypassing it violates hard-rule 11 on source terms).
  Armin chose Option 2 (free government sources). AustralianTenders parked
  in backlog if it later proves worth the fee.

- **Baseline correction (carry forward):** the 14 red tests are NOT
  network/LLM/clock-skew as earlier notes claimed. All 14 are in
  tests/test_cockpit_v2_frontend.py — Node.js v18 running ES-module JS
  without "type":"module" (SyntaxError: Unexpected token export).
  Unrelated to Python/adapter code.

Next: after Armin grants write access -> push + open PR. Then start H3
strata directory adapter using this same fixture-driven pattern. Also check
I1/I2 status (still unexamined).

Safety: adapter is read-only, never sends, no schema change, no secrets read.
Rollback = git switch main (standalone file).
