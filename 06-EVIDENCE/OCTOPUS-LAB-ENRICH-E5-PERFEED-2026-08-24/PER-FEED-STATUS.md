# E5 Per-feed status (readonly)
captured: 20260824T062646Z  ARMED=false

**PASS=True** ? 7 feeds; taxonomy {'OK': 7, 'FAIL': 0, 'MISSING': 0, 'STALE': 0}
last_run_age?422s  snapshot_freshness_age?116s

| feed | sensor_id | status | age_s | event |
|---|---|---|---|---|
| open_meteo_sydney | OCT-FEED-OPENMETEO | OK | 422 | 1021eb8e? |
| open_meteo_aqi | OCT-FEED-AQI | OK | 422 | ea4877e1? |
| timeapi_io_sydney | OCT-FEED-TIME | OK | 422 | 96988fd6? |
| frankfurter_aud | OCT-FEED-FX-AUD | OK | 422 | 2dc99b4d? |
| bom_sydney_obs | OCT-FEED-BOM-SYD | OK | 422 | 72820557? |
| guardian_au_rss | OCT-FEED-NEWS-AU | OK | 422 | 2ffe8884? |
| usgs_quakes_2p5 | OCT-FEED-USGS-QUAKE | OK | 422 | fc243ba5? |

Gap: `feeds_snapshot.readings` still meta-only (evidence_age_s, sensor_coverage). Proposed per-feed readings shape in PROPOSED-READINGS.json (writer HOLD ? E5 readonly only).
E6?E7 HOLD per owner.
