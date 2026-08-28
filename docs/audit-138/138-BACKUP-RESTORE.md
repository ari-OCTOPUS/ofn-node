# BACKUP/RESTORE (2026-08-28T00:14:00Z)
- `ofn-backup.timer` active (daily); `ofn-backup.service` last run 2026-08-27T17:18:12Z, exit 0.
- Destination `/home/ari/.local/share/ofn/backups/20260827-171817/`: 14 sqlite DBs (+manifest). ledger sha256 prefix 0368ad973e44fee59bd5.
- Restore rehearsal (temp only): copied ledger+painting to tmp; `PRAGMA integrity_check` = ok on both; originals untouched; tmp removed.
- RPO/RTO proposal: Painting/Ziman/Studio RPO ≤24h (timer), RTO ≤15min (copy-back + service restart under owner GO). Mesh tree is NO_GIT and not in ofn backups → **GAP-3: mesh state/audit not covered by ofn-backup**.
- Full-repo restore not rehearsed → production readiness stays BLOCKED for restore-until-rehearsed (per directive §6).
