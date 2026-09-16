# CONTROL_URL findings — Board2 Phase-3

Searched:
- `F:\backup\06-EVIDENCE\BOARD2-WIRE-WINDOWS-2026-08-22\`
- `F:\octopus-wire\`

## Exact strings found

1. **Intended Phase-3 CONTROL_URL:** `https://cp.master-painting.com`
   - `MESSAGES-WINDOWS.md` / AFTER copy: "CONTROL_URL جدید آماده است: https://cp.master-painting.com"
   - Same host for `OCTOPUS_BRIDGE_CONTROL_URL` update request in id:cp-rescue-1

2. **Legacy LAN candidate:** `https://192.168.0.191:8801`
   - `WIRE.md`: "CONTROL_URL … `https://192.168.0.191:8801`"
   - Also referenced with `OUTBOUND=1` / `BOARD_CP_PULL=1` as historical example

## Verdict
Not MISSING. Use **https://cp.master-painting.com** as planned CONTROL_URL for Phase-3 unlock authorization.
Do not invent alternate URLs. Do not arm OUTBOUND/CONTROL_URL from this evidence pack — marketing owns execution.
