# How laptop OCTOPUS flags are set (observed 2026-08-22)

## Surfaces (no invent)

| Surface | Path | Role |
|---------|------|------|
| Primary flags | `F:\backup\_ops\OCTOPUS-flags.cmd` | Sourced at limb/Center boot by RESTART-ALL.ps1 / RESTART-PROCESS.ps1 / watchdogs into process env |
| Board/CP env | `F:\backup\_ops\OCTOPUS.env` | Small overlay (board CP / miniapp); **does not** hold doctor merge gate |
| Loaded snapshot | `F:\backup\_ops\state\flags-loaded-*.json` | Receipt of what a process loaded at start (center/organism/live/cortex/miniapp-gateway) |
| FREEZE | `F:\backup\_ops\budget\FREEZE.flag` | Present = freeze; **absent** now |
| Gitwrite block | `F:\backup\_ops\backup\GITWRITE-FAILED.flag` | Present = gitwrite block; **absent** now |
| Doctor state | `F:\backup\OCTOPUS-DOCTOR\90-_meta\state\doctor-vitals.json` | `dry_run` + unlock metadata (annotation only; merge gate is env) |
| Code gate | `F:\backup\OCTOPUS-DOCTOR\doctor\daemon.py::_merge` | Requires `os.environ["OCTOPUS_DOCTOR_MAY_MERGE"] == "1"` when `dry_run` is false |
| Lab contract | `F:\backup\LAB-DOCTOR-CONTRACT.yaml` | Policy: scheduled propose_only; doctor_patches_production_directly forbidden as standing rule |

## Load path
1. Operator / watchdog runs `RESTART-*.ps1`
2. Script parses `OCTOPUS-flags.cmd` (`set KEY=VAL`) into child process environment
3. Writes `flags-loaded-<limb>.json`
4. Running processes do **not** hot-reload `OCTOPUS-flags.cmd` into `os.environ`

## Doctor auto-patch gate
- Flag name (existing): `OCTOPUS_DOCTOR_MAY_MERGE=1`
- File surface now set: `OCTOPUS-flags.cmd` (tail block 2026-08-22)
- Effective when: Center/Doctor limb restart that sources flags (deferred — see NEED_CENTER_RESTART_AFTER_PHASE3.json)
