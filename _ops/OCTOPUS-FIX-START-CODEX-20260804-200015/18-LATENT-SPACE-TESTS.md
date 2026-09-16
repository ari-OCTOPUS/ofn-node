# 18 — latent_space test results

Both run directly this session with `PYTHONIOENCODING=utf-8 PYTHONUTF8=1`.

## `test_latent_space.py` — 14/14 pass (baseline behavior, pre-existing)

embed+retrieve, nearest-neighbors, mean-pool integrate (+ empty + missing-keys variants),
dim validation/auto-pad, empty-space similarity, zero-vector similarity (no div-by-zero),
duplicate-key overwrite, similarity threshold, metadata tracking, persist save/load
round-trip, `keys_by_layer`, `remove`.

## `test_latent_space_fail_closed.py` — 6/6 pass (blindspot #53 specific)

1. data persisted (setup sanity)
2. corrupt file written (setup — deliberately malformed JSON to force the exception path)
3. `_load()` (via `__init__`) did not crash on the corrupt file
4. `_corrupt_load_error` registered with the exception detail
5. corrupt file quarantined (renamed to `*.corrupt.<ts>.json`), not left in place misleading
   a future load
6. quarantine file actually exists on disk after the run

This is a genuine synthetic-exception test (writes malformed JSON to disk, constructs a new
`SharedLatentSpace` pointed at it, asserts on the resulting object state) — not a mock that
bypasses the real `_load()` code path. Confirmed by reading the test file directly.

## Status: PASS, 20/20 across both files.
