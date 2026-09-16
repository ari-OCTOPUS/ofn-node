---
type: unlock-receipt
status: active
tags: [doctor, auto-patch, unlock, owner-auth, 2026-08-22]
created: 2026-08-22
token: OCTOPUS-DOCTOR-AUTOPATCH-20260822
---

# 90-DOCTOR-AUTOPATCH-UNLOCK-2026-08-22

## Choice
Unlock Doctor auto-patch auth on the **laptop** organism.

## Token
`OCTOPUS-DOCTOR-AUTOPATCH-20260822`

## Observed before (no invent)
- `doctor-vitals.json` `dry_run: false` already (prior unlock 2026-08-22 12:23 +10)
- `FREEZE.flag` / `GITWRITE-FAILED.flag` absent (archived earlier same day)
- `OCTOPUS_DOCTOR_MAY_MERGE` **unset** on flags/env surfaces
- Clear existing gate: `OCTOPUS-DOCTOR/doctor/daemon.py::_merge` requires `OCTOPUS_DOCTOR_MAY_MERGE=1` when not dry_run

## Changed
1. Created evidence dir + `OWNER-AUTHORIZATION.json` + `BEFORE.json`
2. Appended `set OCTOPUS_DOCTOR_MAY_MERGE=1` to `F:\backup\_ops\OCTOPUS-flags.cmd`
3. Backup: `OCTOPUS-flags.cmd.bak-20260822-doctor-autopatch`
4. Annotated `doctor-vitals.json` with auto_patch unlock metadata (dry_run left false)

## Not done
- No `git add -A`
- No Orange Pi mutation
- No new invented flag names
- Process reload still required for live organism to source flags.cmd

## Evidence
`F:\backup\06-EVIDENCE\OCTOPUS-DOCTOR-AUTOPATCH-2026-08-22\`
