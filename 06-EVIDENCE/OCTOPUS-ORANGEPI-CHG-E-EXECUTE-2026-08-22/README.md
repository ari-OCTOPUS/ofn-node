# OCTOPUS-ORANGEPI-CHG-E-EXECUTE-2026-08-22

Owner-authorized Orange Pi **CHG-E** execute package (evidence compaction).  
Written 2026-08-22T19:08:12+10:00 AEST; **executor = sensoriom**.  
**Status: BLOCKED_NEED_ARCHIVE_ROOT** (skeleton complete; not EXECUTE_READY).

Supersedes auth-only folder: `../OCTOPUS-ORANGEPI-CHG-E-2026-08-22/` (`mutate_device: false` vs `execute: true` conflict).

| File | Role |
|------|------|
| OWNER-AUTHORIZATION.json | Binding auth; **mutate_device=true**; gate BLOCKED |
| OWNER-CHG-GRANT-SENSORIOM.json | Execute grant (gated) |
| PLAN.md | Reversible compaction plan + owner input placeholders |
| EXECUTION-ORDER.md | GATE → E0 → E1 → E2 → E3 → RECEIPT |
| ROLLBACK.md | Restore-from-archive procedure |
| SENSORIOM-EXECUTE-BRIEF.md | One-screen paste brief |

## Auth id

`OCTOPUS-ORANGEPI-CHG-E-20260822`
