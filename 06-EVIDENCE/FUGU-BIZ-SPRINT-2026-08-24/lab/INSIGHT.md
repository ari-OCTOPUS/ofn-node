# INSIGHT — Lab E3 Feeds Quality (Fugu / BrainPort)
**Sprint:** FUGU-BIZ-SPRINT-2026-08-24 · Day1 lab  
**Model:** fugu (not ultra)  
**Constraints:** ARMED=false · WAVE0 locked · no hardware buy

## Verdict
E3 soak **DEGRADED** — feed **counts** are healthy (**7/7**, fail empty) but **freshness debt** makes the green count misleading.

## What the data says
- Samples: 15 over ~842s
- Holds: snapshot_age_gt_300s; homeo_ok_false_seen; readings_cover_lt_expected_feeds
- Snapshot age max: ~1780s (≫300s bar)
- Readings schema thin: only meta fields (evidence_age_s, sensor_coverage), not 7 named feeds
- Host observation_age metric (E1) still live; bus CONNECTED; timers active

## BrainPort takeaway (short)
Treat **ok_count** as necessary but not sufficient. Gate “feeds healthy” on **(ok_count==expected) AND (snapshot_age < threshold) AND (per-feed status present)**. Until timestamp refresh lands, dashboards should show **DEGRADED freshness**, not green.

## Next safe enrich (proposals only — no execute)
1. **E4_TS_REFRESH_PROVE** — readonly: prove homeo-feeds-snapshot timer writes fresh `ts_utc`/`last_run_ts` each fire; if not, reversible patch to stamp on write (no ARM).
2. **E5_PER_FEED_STATUS** — expand snapshot `readings` to one row per expected feed (status/age) for real triage (readonly schema then small reversible writer).
3. **E6_WAVE01_RANGE_TRIAGE** — readonly triage `quarantine/wave01-range.json` (still KEEP); clear only on owner GO.
4. **E7_BOOT_REPORT_LIVE** — stop doctor/ops relying on ancient `boot_report.json`; point checks at live snapshot (observe-only).

## Do not do
- WAVE0 unlock / ARMED=true / estop buy / PWM / ultra unless weekly budget allows and owner asks

## Artifacts
- `FEEDS-QUALITY.json` · `RECEIPT-E3.json` · `samples.jsonl` · this `INSIGHT.md`
- Also: `FUGU-INTERPRET-E3.json` · `FUGU-USAGE.json`
