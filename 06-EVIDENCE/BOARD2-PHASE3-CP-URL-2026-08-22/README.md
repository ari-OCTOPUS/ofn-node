# Board2 Phase-3 CONTROL_URL set — prove pending
Auth: OCTOPUS-BOARD2-PHASE3-CONTROL-OUTBOUND-20260822
Canonical URL (ari confirmed): https://cp.master-painting.com

## BEFORE
CONTROL_URL=https://192.168.0.191:8801 (legacy LAN)

## AFTER (DietPi octopus-bridge)
CONTROL_URL=https://cp.master-painting.com
OUTBOUND_ENABLED=1
BOARD_CP_PULL=1
CA_FILE=/etc/octopus-bridge/board-cp-ca.pem (legacy pin; may need update for Cloudflare)

## Probes
healthz → Cloudflare 530 / 1033
pull → Cloudflare 530 / 1033

## Note
API key briefly appeared in local terminal output during env dump — rotate in place; value not copied into this receipt.
