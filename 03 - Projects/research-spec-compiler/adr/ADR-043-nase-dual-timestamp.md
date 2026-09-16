# ADR-043 — NASE dual timestamp (occurred_at vs recorded_at)

- **Status:** PROPOSED — numbers measured 2026-08-13; clocks not yet accepted as independently meaningful
- **Date:** 2026-08-13
- **Source DB:** `_ops/state/spine/spine.db` table `events` (n=2907)

## Problem

A 100-row newest-per-domain sample had `occurred_at == recorded_at` **zero times**. That falsifies “the two columns are always identical.” It does **not** by itself prove bitemporal `valid_time` vs `transaction_time`.

Prior audit note (`memory_provenance_map.md`) that spine tests sometimes stamp both from `_utc_now_iso()` remains relevant: two names can still be one clock.

## Acceptance addition (required before calling the pair “independent”)

```text
Report the distribution (min/median/max/stddev) of
(recorded_at - occurred_at) across the 100-row sample.
If stddev ≈ 0, treat the clocks as NOT independently meaningful
until proven otherwise.
```

## Measurement (same 100-row pick as `nase_extract.json`)

Parsed with `datetime.fromisoformat` (offsets kept). Unit = microseconds.

| stat | value |
|---|---|
| n | 100 |
| min | 6 µs |
| median | 11.5 µs |
| mean | 118.57 µs |
| max | 9726 µs (9.726 ms) |
| stdev | 971.41 µs |
| zero deltas | 0 |
| negative deltas | 0 |
| all recorded_at > occurred_at | true |

Raw: `c:\Users\Armin\Desktop\octopus_audit_report\nase_delta_stats.json`

## Verdict on independence

- **Not identical strings.** Equal-timestamp count = 0.
- **Not a 1-second fake offset.** Max gap < 10 ms.
- **stdev ≈ 1 ms**, median ≈ 12 µs — consistent with two consecutive `datetime.now(timezone.utc)` calls in the same write, not with a delayed ingest vs event time.
- Relative to spine beat spacing (~minutes), stdev is ≈ 0. **Treat clocks as NOT independently meaningful** until a producer is shown to set `occurred_at` from an external event time distinct from write time.

Code path for the default stamp: `_ops/spine/event_spine.py:40` `_utc_now_iso` and tests `_ops/tests/test_spine_single_surface.py:99-102` (both columns default to the same helper). Whether live `system.beat` rows use two calls vs one: **NOT VERIFIED beyond the distribution**.

## Non-claims

No NASE-product file format. No change to spine writers in this ADR.
