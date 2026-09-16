# 110B lineage — send-path tests parked here (owner ruling 2026-09-17)

## What these are
- `tests/test_hf.py` (5 tests) — the HF hotfix pack's regression tests from the
  release/p0 branch (supervisor hotfixes, cap/min-area routing, rollback
  no-resend, card-hash stability). Historical intent: protect the fixes behind
  the "first 5 autonomous sends" campaign (PAINT-L5-001).
- `tests/test_teeth.py` (3 tests) — capability-token integrity tests
  (tamper/expiry/R1 healthy path) for the send-token mechanism.

## Why they are red here (expected)
They assert the quote **send path** (`quote_engine.quote(..., dry=False)`
side-effects, `capability_token.verified_send`, WAL bookkeeping) that main
**deliberately removed** in PR #110A (scope-split; documented in
`ofn/agents/quote_engine.py` docstring) and that the owner's containment
(INCIDENTS رخداد ۶: `OCTOPUS_WIRE_LEAD_OUTBOUND_WAL` → "0", send flag not
re-armed) keeps parked. On this branch they fail by design.

## Conditions to turn green (the 110B contract)
1. The send path returns in a separate PR (110B lineage) with honest
   independent review — capability_token + transport + WAL wiring restored or
   superseded.
2. These tests are run against that reintroduced path and updated ONLY in
   lock-step with its real contract (no weakening assertions).
3. Until then this branch is the parking lot: tests are excluded from PR #71's
   scope (owner: "PORT TO 110B، حذف نکن").

## Provenance
Moved out of `landing/release-p0-20260902` @ ba1464d on 2026-09-17 per owner
ruling; original commits: 0e02d05/e87943c/cfb9d98 lineage (release/p0).
