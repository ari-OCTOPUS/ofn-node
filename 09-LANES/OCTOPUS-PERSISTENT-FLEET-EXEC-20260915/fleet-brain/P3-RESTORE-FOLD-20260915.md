# P3 verified restore fold (ARCH · 2026-09-15)

**receipt:** `P3-VERIFIED-RESTORE-RECEIPT.json` sha `83d525134317e7b2de93986684309ba2bb4bd96b9ee79566e5494035bf801d11`  
**verdict:** **PASS** · 9/9 file MATCH  
**source:** 138 (`fleet-memory` + `fleet-jobs`)  
**dest:** 180 `/opt/octopus-restore-copies/p3-20260915T033708Z` — **verified_restore_copies_ONLY** · not primary SoT  
**method:** sha256 manifest → tar stream → per-file sha256 MATCH  
**commander_node_id:** 138 · **dual_commander:** false · **customer_send:** false

Design cite: `P3-RESTORE-COPY-DESIGN` `fce33477…` / EXEC `52887e1a…`.

## RPO/RTO addendum (2026-09-15)

- `RPO_seconds`: **0** (point-in-time snapshot; continuous lag not claimed)
- `RTO_seconds`: **3** (START→END wall for verified copy+MATCH)
- Live schema cite in restore tree: `fleet_job.v1` sha **`49eb6c0be2f4a9afbd0520feba4cff00500bab73f4b5eae7a89695138ab70d59`**
- Addendum: `P3-RPO-RTO-ADDENDUM.json` sha `5262d4eae4531b9b76cfcbc3068a3abbdc86cb2993c6a6b61f29a1604d656335`
- Parent receipt sha **unchanged** (`83d52513…`)

