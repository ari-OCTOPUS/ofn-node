# Board2 Phase-3 re-probe after LISTEN proof
Time: 2026-08-22 ~18:54 AEST
Auth: OCTOPUS-BOARD2-PHASE3-CONTROL-OUTBOUND-20260822

## Bridge config (unchanged this probe)
CONTROL_URL=https://cp.master-painting.com
OUTBOUND_ENABLED=1
BOARD_CP_PULL=1
CA_FILE=/etc/octopus-bridge/board-cp-ca.pem

## Canonical CONTROL_URL probes
- https://cp.master-painting.com/healthz → Cloudflare 530 / 1033
- https://cp.master-painting.com/api/board-cp/pull → 530 / 1033
- same with legacy CA pin → 530 / 1033

## Diagnostic LAN (NOT set as CONTROL_URL)
- https://192.168.0.191:8801/api/board-cp/pull with CA pin → HTTP 401 {"ok":false,"reason":"board_bearer_required"}
- same with -k → HTTP 401 board_bearer_required
→ DietPi can reach laptop origin; fail-closed auth OK. Tunnel/CF path still broken.

## Verdict
Phase-3 PASS not yet (CF 530). CONTROL_URL left on cp.master-painting.com.
