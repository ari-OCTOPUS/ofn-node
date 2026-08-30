# EXECUTION-ORDER - Orange Pi MQTT 1883 ENABLE ABD

**Authorization:** `OCTOPUS-ALL-DOORS-OPEN-20260822` + `OCTOPUS-MQTT-ENABLE-ABD-20260822`  
**Written (AEST):** 2026-08-22T22:40:00+10:00  
**Executor:** sensoriom @ sensorium-opi5pro (192.168.0.182)  
**Laptop:** plans + grant only (no SSH)

## Sequence (numbered for sensoriom)

| Step | Action | Gate before next |
|------|--------|------------------|
| 0 | Read this package (PLAN.md, OWNER-AUTHORIZATION.json, ROLLBACK.md). Confirm tokens. Confirm WAVE0 hardware stays locked. | Tokens present; scope understood |
| 1 | Precheck: `ss` :1883/:8883; map any PID->unit; list mosquitto/emqx/mqtt units; read MQTT_DISABLED.md / board mqtt fields if present | Before JSON: listen state CLOSED or existing owner |
| 2 | Discover auth surfaces + firewall rules for 1883/8883; record doctor mqtt assertion | Auth path + ACL/firewall noted; secrets NOT copied to laptop |
| 3 | Choose bind: **127.0.0.1** (default) OR LAN `192.168.0.0/24`-only. Refuse WAN. | Bind choice recorded in receipt |
| 4 | Install mosquitto **only if** no suitable broker exists; else configure existing | Package/unit identified |
| 5 | Apply conf: listener + `allow_anonymous false` + password_file/ACL via `DISCOVER_OR_GENERATE_LOCAL_ONLY` | Config syntax OK; anonymous disabled |
| 6 | Firewall: if LAN bind, allow `192.168.0.0/24` only; **never** UFW public 1883. If loopback-only, no public allow. | Rules recorded |
| 7 | `enable --now` broker unit (or restart existing) | Unit active; `ss` matches chosen bind |
| 8 | Verify: anonymous DENIED; local auth probe PASS on harmless topic (no PWM/legs) | Auth gates PASS |
| 9 | Document doctor mqtt implications (update existing field if present; else receipt-only; **no** auto-patch) | Note in receipt |
| 10 | Write board receipts + TO-LAPTOP exchange ack citing this package | Files present |
| 11 | Confirm ROLLBACK.md matches actual unit/conf used (stop+disable path) | Rollback concrete |

## Parallelism

- None. Do not combine with WAVE0 Path H hardware unlock, PWM invent, TORCH, CHG-C, CHG-E, LAN:9101 rebind, or key ceremonies in the same mutate window.

## Abort

Any WAN/public 1883, anonymous allow, invented credentials on laptop evidence, Doctor auto-patch, WAVE0 hardware/PWM/legs touch, or verify FAIL -> STOP, execute ROLLBACK.md (stop+disable), report via ari.
