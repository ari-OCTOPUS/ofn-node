# PLAN — Homeostasis from live feeds (snapshot timer)

**Authorization:** `OCTOPUS-HOMEO-FEEDS-SNAPSHOT-20260823`  
**Board:** sensorium-opi5pro @ 192.168.0.182  
**Executor:** sensoriom  
**mutate_device:** true (bounded, read-only effects)

## Goal

Periodically compute advisory vitals from EXTERNAL_PUBLIC_FEED last-run evidence:

| Homeostasis var | Source |
|---|---|
| `sensor_coverage` | `LAST_RUN.ok_count / len(ALLOWLIST.feeds)` |
| `evidence_age_s` | age of `LAST_RUN.ts` |

Outputs advisory `mode` / `severity` only (`normal` / `conserve` / `would_lockdown`).

## Sequence

0. Confirm owner accepted OWNER-AUTHORIZATION (status ≠ PROPOSED)
1. Install script (copy from proven sketch)
2. Install systemd service + timer (OnUnitActiveSec≈15m or OnCalendar aligned)
3. `daemon-reload` + `enable --now` timer
4. One-shot prove: snapshot JSON exists; `mutates_host=false`; feeds timer untouched
5. Receipt `RECEIPT-HOMEO-FEEDS-SNAPSHOT.json` → exchange + FROM-PI

## Explicit non-goals

- Doctor repairs_attempted > 0
- Restarting `octopus-external-feeds.*` on stale age
- Zero-filling missing coverage
- Applying lockdown / actuator changes

## Success

- Timer active; snapshot refreshed; doctor still PASS; feeds timer still active; WAVE0 ARMED=false unchanged
