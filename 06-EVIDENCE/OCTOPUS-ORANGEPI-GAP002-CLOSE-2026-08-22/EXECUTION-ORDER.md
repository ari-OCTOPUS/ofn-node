# EXECUTION-ORDER - Orange Pi GAP-002 registry close

**Authorization:** `OCTOPUS-ORANGEPI-GAP002-CLOSE-20260822`  
**Written (AEST):** 2026-08-22T21:13:00+10:00  
**Executor:** sensoriom @ sensorium-opi5pro (192.168.0.182)  
**WAVE0_hardware:** KEEP_LOCKED | **MQTT:** CLOSED

## Sequence

| Step | Action | Gate |
|------|--------|------|
| 0 | DISCOVER-FIRST: locate `open-gaps.json` (prefer `/opt/octopus/current/manifests/open-gaps.json`) + `doctor/latest.json` | Paths exist; document if different |
| 1 | Capture before: sha256 + GAP-002 object + doctor gap002/signature messages | BEFORE receipt |
| 2 | Match GAP-002 field shape from CLOSED examples in same registry | Shape locked; no invented enums |
| 3 | Backup `open-gaps.json` (timestamped copy + sha256) | Backup PASS |
| 4 | Edit **only** GAP-002 fields â†’ `pass=true` + `EXTERNALLY_CHECKPOINTED` (or CLOSED example status) | JSON valid; other gaps unchanged |
| 5 | Re-run doctor **readonly** | After report captured |
| 6 | Prove gap002 cleared (no NEED_OWNER / no `signature_does_not_close_registry` for GAP-002) | PROVE PASS |
| 7 | Receipts + TO-LAPTOP exchange ack | Files present |

## Why this order

Discover + CLOSED-example match prevents inventing schema. Backup before edit enables rollback. Doctor readonly prove is the acceptance gate (live gap file already CLOSED_BY_SIGNED_CHECKPOINT is insufficient alone).

## Parallelism

- Do **not** combine with WAVE0 hardware, MQTT, torch, LAN:9101, or Doctor auto-patch packages.
- Quiet board preferred.

## Abort

- open-gaps path missing and not discoverable from doctor â†’ STOP, write NEED_OWNER path report (do not invent file).
- CLOSED example shape cannot be matched â†’ STOP, report schema, do not invent fields.
- JSON invalid after edit â†’ restore backup immediately (ROLLBACK.md).
- Doctor still flags gap002 after correct shape patch â†’ STOP, do not broaden edit; report via ari.