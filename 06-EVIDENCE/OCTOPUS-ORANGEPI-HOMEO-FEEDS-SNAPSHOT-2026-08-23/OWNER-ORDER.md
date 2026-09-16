# OWNER-ORDER — Homeostasis ← live feeds snapshot (READ-ONLY)

**Package:** `F:\backup\06-EVIDENCE\OCTOPUS-ORANGEPI-HOMEO-FEEDS-SNAPSHOT-2026-08-23\`  
**Written (AEST):** 2026-08-23T02:41:00+10:00  
**Author:** sensoriom (teach-through lab) for owner via ari  
**Tokens:** `OCTOPUS-HOMEO-FEEDS-SNAPSHOT-20260823` (+ `OCTOPUS-ALL-DOORS-OPEN-20260822` if owner re-cites)

## Intent

Install a **read-only** timer on sensorium-opi5pro that maps live external feeds (`ALLOWLIST` + `LAST_RUN`) into an advisory Homeostasis snapshot. **No repair. No feed restart. No WAVE0 arm. No host lockdown.**

## Proven sketch

- Script concept: `lab-doctor/05_homeo_feeds_sketch.py`
- Live dry-run on Pi: 7/7 feeds → `mode=normal`, `severity=healthy`, `mutates_host=false`

## Accepts (when owner signs)

- Enable `octopus-homeo-feeds-snapshot.timer` (cadence ~15m, aligned with feeds timer)
- Write `/var/lib/octopus/state/homeostasis/feeds_snapshot.json`
- Evidence session under `/var/lib/octopus/evidence/session-homeo-feeds-snapshot-*/`

## Does NOT accept

- Doctor calling repair/restart on stale feeds
- Treating `would_lockdown` as an applied host action
- Auto-install without this token accepted

## Rollback

`systemctl disable --now octopus-homeo-feeds-snapshot.timer`; remove unit files; leave snapshot files as audit (or delete if owner asks).
