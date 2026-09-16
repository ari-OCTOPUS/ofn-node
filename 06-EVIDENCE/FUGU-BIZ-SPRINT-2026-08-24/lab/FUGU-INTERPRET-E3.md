# Fugu Lab Day1 — E3 interpretation (model=fugu)

**Status:** DEGRADED (not FAIL)

**Headline:** Feeds **count** is healthy (7/7, no fails). DEGRADED because **snapshot timestamp stays stale** (age >>300s) and **readings only expose 2 meta fields**, so per-feed quality is still dark.

## Anomalies / holds
1. **SNAP_TS_STALE** — last_run/ts age up to ~1780s while ok_count stays 7.
2. **READINGS_SCHEMA_THIN** — readings_n=2 vs expected_feeds=7.
3. **HOMEO_OK_FLAP** — intermittent; known; no WAVE0 unlock.

## Non-issues
- bus CONNECTED, ARMED=false, timers active, observation_age metric live (E1).

## Fugu call
Keep locked. No ultra. Next cheap win: refresh feeds_snapshot timestamps on timer (prove readonly first).

Paths: F:\backup\06-EVIDENCE\FUGU-BIZ-SPRINT-2026-08-24\lab\
