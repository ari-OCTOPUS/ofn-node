---
tags: [octopus, connector-gap, concepts-to-code, 2026-08-23]
date: 2026-08-23
timezone: Australia/Sydney
status: GAP_MAP_ACTIVE
SoT: F:\backup
---

# GAP-MAP — Concepts→Code (2026-08-23)

## OAuth connector gaps (no invent metrics)

| gap_id | connector | status | until |
|---|---|---|---|
| CG-001 | GA4 | WAITING_OWNER_OAUTH | OAuth + property-mapping signoff (D1/D7) |
| CG-002 | GSC | WAITING_OWNER_OAUTH | OAuth + verified-property binding (D1/D7) |
| CG-003 | Google Ads | WAITING_OWNER_OAUTH | OAuth + account-approval signoff (D1/D7) |

Registry: `F:\backup\06-EVIDENCE\OCTOPUS-LAPTOP-CONCEPTS-TO-CODE-2026-08-23\CONNECTOR-GAP-REGISTRY.json`  
Runtime hook: `_ops/evidence_plane/connector_gap_loader.py` (flag `connector_gap_hook` in `_ops/organs/WIRING.json`)

## Evidence Store gaps addressed this pass

| rule | implementation |
|---|---|
| evidence_id / source_type / estimate / confidence / valid_for | `agents/octopus_evidence/connector_evidence.py` + `_ops/evidence_plane/connector_evidence.py` |
| missing evidence_id OR invalid source_type → unverified | `normalize_record()` |
| estimate requires confidence + valid_for | enforced in `normalize_record()` |

## Explicit non-gaps / non-actions

- WAVE0 hardware remains KEEP_LOCKED (not unlocked)
- MQTT remains CLOSED
- Mining remains deferred
- No secrets written
- No money invent

## Probe queue (not OAuth gaps; still no invent)

Similarweb Premium, Statista, CB Insights, Realtime Finance Data, GitHub, Hugging Face — PENDING_RUNTIME_PROBE per registry.
