# SUPERSEDED — use EXECUTE package

**This folder is AUTH-ONLY and SUPERSEDED.**

| Field | Value |
|-------|-------|
| This path | `F:\backup\06-EVIDENCE\OCTOPUS-ORANGEPI-CHG-E-2026-08-22\` |
| Conflict | `OWNER-AUTHORIZATION.json` had `mutate_device: false` while `OWNER-CHG-GRANT-SENSORIOM.json` had `execute: true` |
| Superseding package | `F:\backup\06-EVIDENCE\OCTOPUS-ORANGEPI-CHG-E-EXECUTE-2026-08-22\` |
| Auth id (unchanged) | `OCTOPUS-ORANGEPI-CHG-E-20260822` |
| Written (AEST) | 2026-08-22T19:08:12+10:00 |
| Gate on execute package | **BLOCKED_NEED_ARCHIVE_ROOT** |

Do **not** treat this auth-only folder as executable CHG-E. Sensoriom must use the EXECUTE package (mutate_device=true) and must still wait for owner ARCHIVE_ROOT inputs before Pi mutation.
