# SENSORIOM-EXECUTE-BRIEF - GAP-002 registry close

OWNER EXECUTE GRANT `OCTOPUS-ORANGEPI-GAP002-CLOSE-20260822` (AEST 2026-08-22T21:13:00+10:00; **owner_fix_all=true**): on sensorium-opi5pro (192.168.0.182) close **gap002_registry** NEED_OWNER.

**Intent:** live GAP-002 gap file already `CLOSED_BY_SIGNED_CHECKPOINT` `pass=true`, but doctor says `signature_does_not_close_registry`. Align `/opt/octopus/current/manifests/open-gaps.json` (or documented path) GAP-002 to `pass=true` + `EXTERNALLY_CHECKPOINTED`.

**Prefer CHG-A style:** backup file -> edit **only** GAP-002 fields -> doctor **readonly** re-run -> prove gap002 cleared.

**DISCOVER-FIRST (if schema unknown):** read current `open-gaps.json` + `doctor/latest.json`; match GAP-002 entry shape from CLOSED examples; then patch. Do not invent enums/fields.

**Hard bounds:** `WAVE0_hardware=KEEP_LOCKED`; `MQTT=CLOSED`; **no** zero-fill keys; **no** WAVE0 unlock invent; **no** Doctor auto-patch (readonly prove only); laptop does **not** SSH - sensoriom executes.

**Package:** `F:/backup/06-EVIDENCE/OCTOPUS-ORANGEPI-GAP002-CLOSE-2026-08-22/`
**Rollback:** restore `open-gaps.json` from timestamped backup + re-run doctor readonly.