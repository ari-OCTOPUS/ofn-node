# SYNC DECISIONS - owner-delegated, applied

All five original proposals are CLOSED. Each was resolved by running code, not
by editing a document. This file records the decision and its evidence.

## P-1: stale "207 tests" reference -- CLOSED

Decision: adopt 171 as the live number, keep 207 recorded as a superseded
claim with its cause.

Evidence: pytest returned 171 passed (72 + 72 + 27). The 207 figure counted the
app/NBB-CP suite deleted in commit ea69126 on 2026-08-03. BACKUP-README was
correct and MANIFEST.yaml was stale. Contradiction C-001.

Current state: scanner reports zero stale 207 references in the repo. Nothing
left to patch.

## P-2: threshold n -- CLOSED

Decision: n>=60 stands. The earlier n>=20 figure is superseded.

Reasoning: the amendment to 60 was recorded BEFORE the first resolution, so
pre-registration integrity is intact. Lowering it now, after observation began,
would invalidate the test. A stricter threshold costs time, not validity.

Evidence: MIN_RESOLUTIONS = 60 at src/nbb_cp/adapters/observatory/verifier.py:12.
The sync engine now checks against 60, not 20. The earlier FAIL was a defect in
the checker, not in the code.

## P-3: observation window -- CLOSED

Decision: 30 days.

Reasoning: removing BOM from the allowlist cut available data, so the window was
extended from 14 to 30 days to reach sufficient n.

Evidence: scanner reports window value 30, single occurrence. The 14-day
scheduled task was corrected.

## P-4: USGS allowlist -- CLOSED

Decision: earthquake.usgs.gov admitted as row F of allowlist v2.

Basis: its robots.txt returns 404. Under RFC 9309 section 2.3.1.3 a 4xx response
means "unavailable", and a crawler MAY access all. This is the same reasoning
that admitted row E (data.api.abs.gov.au, 403) and is distinct from BOM, which
returned a valid robots.txt that explicitly disallowed the data path.

Row G (hacker-news) was admitted on an explicit Allow: /*.json$ directive
matching exactly the endpoints in use.

The needs_formal_allowlist debt is discharged.

## P-5: prediction strategy -- CLOSED

Decision: replaced with a Bayesian Poisson-Gamma predictor.

Root cause found: run_observatory.py lines 120-135 copied the persistence signal
(0.8 / 0.1), which is why OCTOPUS equalled persistence at 0.80 and made the
Brier comparison meaningless.

New model: prior Gamma(1,1) over the rate lambda; posterior Gamma(1+k, 1+t) from
k events above threshold in t hours; prediction is
P(at least one event in 24h) = 1 - (beta/(beta+24))^alpha.

Measured on live USGS data (k=14, n=284): OCTOPUS 0.99 vs persistence 0.80.
20 tests, all passing. Independent of persistence by construction.

---

# REMAINING OPEN ITEM

## C-007: test-count disagreement in the hypothesis engine

ADR-039 states 133 tests. CURRENT-TRUTH states 45 + 20. Neither figure has been
produced by a run in this session. TestPlan in the epistemics module turned out
to be a Pydantic model, not a test class, so the 45/20 figure has no verified
source.

Decision: neither number is adopted. Both are marked unverified until a targeted
pytest run on the real epistemics test path produces a figure.

Standing rule established: a test count in a document is not a claim unless it
carries the command that produced it and the date it was run. Any count without
that pair is to be treated as unverified, regardless of which document holds it.

This is the same rule that resolved C-001, C-002 and C-008.

## Deliberately not closed

ADR sequence gaps 24 through 32: no evidence these ADRs ever existed. Absence of
a document is not a defect unless something references it. Nothing does. Left as
recorded fact, not as a gap to fill.

Archive candidates OCTOPUS-PRIME and _octopus: NOT archived. The three-number
test showed OCTOPUS-PRIME is loaded by the PRE-0 conformance test, _octopus was
written today, and langar/Ziman import from it. The earlier stale labels were
wrong and were corrected.
