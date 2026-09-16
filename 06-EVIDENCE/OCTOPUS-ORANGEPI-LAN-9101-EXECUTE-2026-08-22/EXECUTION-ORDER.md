# EXECUTION-ORDER - Orange Pi LAN:9101 EXECUTE

**Authorization:** `OCTOPUS-ORANGEPI-LAN-9101-20260822`  
**Authorization ID:** `OCTOPUS-ORANGEPI-LAN-9101-EXECUTE-20260822`  
**Written (AEST):** 2026-08-22T19:22:00+10:00  
**Executor:** sensoriom @ sensorium-opi5pro (192.168.0.182)  
**Laptop:** plans + grant only (no SSH)

## Sequence (numbered for sensoriom)

| Step | Action | Gate before next |
|------|--------|------------------|
| 1 | Precheck: `ss` :9101; map PID->unit; locate existing bind knob (systemd drop-in / board.yaml field / stability env/CLI) | Before JSON: listen addr, unit, config path |
| 2 | Record firewall + doctor `lan_9101` current assertion | Implications noted |
| 3 | Apply bind change only: `127.0.0.1` -> `0.0.0.0` or `192.168.0.182` via **existing** knob (prefer drop-in/env/board.yaml) | Config syntax OK; no new service/protocol |
| 4 | LAN ACL if firewall active (subnet allowlist only; no WAN) | Rules recorded |
| 5 | `daemon-reload` (if needed) + restart **only** 9101-owning unit | Unit active |
| 6 | Verify listen + laptop LAN health **without** `ssh -N -L` | PASS from 192.168.0.x |
| 7 | Document doctor `lan_9101` implications (update existing field if present; else receipt-only; **no** auto-patch) | Note in receipt |
| 8 | Write board receipts + TO-LAPTOP exchange ack | Files present |
| 9 | Confirm ROLLBACK.md steps match actual knob used | Rollback path concrete |

## Parallelism

- None. Do not combine with TORCH / WAVE0 / MQTT / CHG-C / CHG-E in the same mutate window.

## Abort

Any WAN bind, invented protocol/port/service, Doctor auto-patch, MQTT/WAVE0/key/zero-fill/CHG-C touch, or verify FAIL -> STOP, execute ROLLBACK.md, report via ari.
