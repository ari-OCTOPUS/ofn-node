---
type: project
status: active
tags: [octopus, diagnosis, this-host-only]
created: 2026-09-05
updated: 2026-09-05
lane: U-WHY-NOT-LIVE-20260905
---

# U-WHY-NOT-LIVE-20260905 — چرا اختاپوس واقعاً زنده نشده

## Role

Quality diagnosis only. `PROPOSE_ONLY`. `may_authorize: false`.
This OS is the laptop vault (`DESKTOP-KA9RFN5` / Wi-Fi `192.168.0.191`). Session label «board 180» is **stopped** (eth0/Wi-Fi contradiction).

## Owned paths

- `09-LANES/U-WHY-NOT-LIVE-20260905/`

## Forbidden

- Enable `OCTOPUS_WIRE_*`, `OFN_WIRE_*`, `OBSERVATORY`, `CORTEX_HYPOTHESIS`, `auto_email`
- Start/restart `ofn.run`; source `OCTOPUS-flags.cmd`; Enable watchdogs
- SSH write/restart on 138/180; bind 0.0.0.0; send; pay; commit; push; deploy
- SSH to 138 is read-only plus local-forward to 138 loopback; no shell writes, no `ofn.service` restart
- Other lanes' files; production state outside this lane (except prior B-safe organism writes)

## Allowed this GO

- This-host verify scripts and receipts in this lane
- Localhost listen classify for 8771/8772 and 8791–8796
- Do not infer 138/180 liveness from laptop absence
- Layer 3: SSH local-forward laptop → 138 loopback, bind `127.0.0.1` only, ports `18791-18796` (never laptop `8791`)
- Layer 3: one BatchMode publickey try to `ari@192.168.0.180`; do not decide 180 role

## Exit gate

Lane report + diagnosis with arbiter envelope; every number sourced or `unverified`; no service started.
