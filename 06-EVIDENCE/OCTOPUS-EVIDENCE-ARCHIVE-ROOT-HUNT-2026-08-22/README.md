# OCTOPUS-EVIDENCE-ARCHIVE-ROOT-HUNT-2026-08-22

**Written (AEST):** 2026-08-22T21:47:00+10:00  
**Scope:** Locate ARCHIVE_ROOT candidates for CHG-E (~4.7G cold evidence). No delete/cleanup. No SSH.

## Prior BLOCKED package

- `F:/backup/06-EVIDENCE/OCTOPUS-ORANGEPI-CHG-E-EXECUTE-2026-08-22`
- Gate: **BLOCKED_NEED_ARCHIVE_ROOT** / EXECUTE_READY=false
- Auth: `OCTOPUS-ORANGEPI-CHG-E-20260822`
- Template still REPLACE_ME: `OWNER-ARCHIVE-SUPPLY.template.json`
- Supersedes auth-only: `../OCTOPUS-ORANGEPI-CHG-E-2026-08-22`

## Documented preferred ARCHIVE_ROOT?

**None.** No filled path in plans/auth. Pi paths seen only for session receipts under `/var/lib/octopus/evidence/...` (HOT/session, not ARCHIVE_ROOT).

Therefore: **no ABD CHG-E archive package skeleton drafted** (would invent a path).

## Laptop candidates (real, existing)

| Path | Free on volume | Notes |
|------|----------------|-------|
| F:\backup\99-ARCHIVE | F: 58.32G | Empty dedicated archive folder — best laptop-side candidate |
| F:\backup-Archive | F: 58.32G | Legacy archive tree (Apps/Logs/...) |
| F:\backup\_Archive | F: 58.32G | Busy vault archive |
| E:\deploy-snapshots | E: 54.35G | Deploy snapshots; wrong semantic unless owner chooses |
| M:\ (pick subdir) | M: 80.8G | Largest free; no CHG-E subdir yet |
| D:\backup | D: 33.49G | Enough but tightest of data drives |

Full JSON: `CANDIDATES.json`

## Owner must confirm (to clear gate)

1. **ARCHIVE_ROOT** on Pi or attached volume (primary; laptop paths alone do not satisfy Pi mutate gate)
2. HOT_EVIDENCE_ROOT
3. HOT_RETENTION_WINDOW
4. DISK_FREE_TARGET
5. INDEX_REBUILD_COMMAND / sensoriom rebuild procedure
6. no_casual_truncate_affirmation=true
7. Optional: laptop mirror root (suggest `F:\backup\99-ARCHIVE`)

Fill: `OCTOPUS-ORANGEPI-CHG-E-EXECUTE-2026-08-22/OWNER-ARCHIVE-SUPPLY.json`