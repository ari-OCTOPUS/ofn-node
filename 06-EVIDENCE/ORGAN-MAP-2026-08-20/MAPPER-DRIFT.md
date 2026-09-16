# T69 — mapper drift (actionable lists)

Live cartographer still reports a **count** (`drift_files` ~1256–1271) and `proposals_total: 0`. This sidecar turns that into paths.

## This session

| list | n | honesty |
|---|---|---|
| modified_files (`_ops/*.py` mtime > map `updated: 2026-07-29`) | 1257 (400 paths stored) | same rule as `wiring._cartographer_map_signal` |
| new_files | 0 | no prior hash inventory — not fabricated |
| deleted_files | 0 | same |
| orphan_modules | 0 this run | `orphan_scan` not invoked (hung under AV); last measured 2026-08-16: checked=667 total=101 weighty=18 |
| dead_imports | bounded; stdlib filtered after first dump | first dump flagged `hmac`/`secrets`/… as missing — false positives |
| duplicate_capabilities | stem collisions, cap 30 | heuristic |
| untested_modules | cap 80 | `test_<stem>` presence only |

Machine copy: `MAPPER-DRIFT.json`.

Backlog from this: persist a hash inventory so the **next** run can fill new/deleted; do not treat 1257 as 1257 bugs — it is “newer than the map.”
