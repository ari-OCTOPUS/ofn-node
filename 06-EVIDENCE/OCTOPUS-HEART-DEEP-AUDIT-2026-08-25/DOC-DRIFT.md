# DOC-DRIFT (status only, no theory rewrite)
Stamp: 2026-08-25T08:16:03+10:00

## Live row 2026-08-25 (SUPERSEDE any 75s/42s/126s quotes)
| Surface | Period | Wire |
|---|---|---|
| arbiter-latest | 97.2s GREEN 3/3 advisory_only | wire_open=true |
| cardiac vote | 42.43s mice CONSTANT | GREEN |
| control_law vote | 255.36s velocity-tracking | GREEN |
| rhythm vote | 79.92s STEADY/GREEN | GREEN |
| heart-shadow | 259.13s | production_wire.open=false |
| heartstate | 255.36s shadow_only | wire_open=false |
| work_pump last health | 276.75s | gate0 false |

## Docs found
- `_ops/MEGAPROMPT-AUDIT-2-BRAINS-HEART-2026-08-03.md` (stale 2026-08-03). SUPERSEDE: read live arbiter-latest + heart-shadow-latest, not this file.
- HEARTS-BRAINS-4D-STATUS / Metaphor Decode / HEARTS-TIME / Octopus_Heart_Design_v1: not present at `_ops` root, `_ops/docs`, `06-EVIDENCE`, or backup root. If they live elsewhere, stamp SUPERSEDE there later. Do not invent paths.

## Adjacent heartbeat-named files (not the organ)
- `_ops/off_heartbeat.py` — OFF-status emitter, not pacemaker
- `_ops/doctor/uniqueness_heartbeat.py` — RO uniqueness probe
- evidence: `06-EVIDENCE/OCTOPUS-DOCTOR-UNIQUENESS-HEARTBEAT-2026-08-23`

## Do not
Rewrite Octopus_Heart_Design_v1 theory as if live. Do not patch MEGAPROMPT in place this wave (this pack is the 2026-08-25 live row).
