---
type: companion-auth
status: active
mode: observe-only
tags: [orangepi, doctor, readonly, companion-auth, 2026-08-22]
created: 2026-08-22
token: OCTOPUS-ORANGEPI-DOCTOR-READONLY-RERUN-20260822
companion_to: OCTOPUS-DOCTOR-AUTOPATCH-20260822
---

# Companion auth — Orange Pi Doctor readonly re-run

## Token
`OCTOPUS-ORANGEPI-DOCTOR-READONLY-RERUN-20260822`

## Mode
**Observe-only.** No merge, no auto-patch, no flag writes on Pi.

## Relation
Companion to laptop unlock token `OCTOPUS-DOCTOR-AUTOPATCH-20260822` (laptop MAY_MERGE gate only).

## Allowed
- Readonly doctor re-run
- Observe / report vitals
- Read-only evidence capture

## Forbidden
Merge, auto-patch, setting `OCTOPUS_DOCTOR_MAY_MERGE`, production writes, `git add -A`, money/webhook, MQTT/LAN/torch/keys mutations.

## Evidence
`F:\backup\06-EVIDENCE\OCTOPUS-DOCTOR-AUTOPATCH-2026-08-22\`
