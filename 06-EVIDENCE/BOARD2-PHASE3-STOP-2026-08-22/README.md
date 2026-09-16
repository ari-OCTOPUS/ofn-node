# Board2 Phase-3 STOP — 2026-08-22

Auth: OCTOPUS-BOARD2-PHASE3-CONTROL-OUTBOUND-20260822

## Before (DietPi octopus-bridge already)
- CONTROL_URL=https://192.168.0.191:8801
- OUTBOUND_ENABLED=1
- BOARD_CP_PULL=1
- CA pinned; API key present

## Probes
- LAN :8801 from board: connect failed
- cp.master-painting.com: Cloudflare 530 / 1033
- Laptop: no TCP listener on 8801

## Action taken
STOP — no URL rewrite, no flag change, no secrets invented.

## Need
Laptop board_cp up + owner-canonical CONTROL_URL choice (LAN vs cp.master-painting.com).
