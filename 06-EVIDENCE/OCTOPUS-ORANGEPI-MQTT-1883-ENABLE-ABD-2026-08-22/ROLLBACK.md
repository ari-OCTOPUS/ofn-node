# ROLLBACK - Orange Pi MQTT 1883 ENABLE ABD

**Authorization:** `OCTOPUS-ALL-DOORS-OPEN-20260822` + `OCTOPUS-MQTT-ENABLE-ABD-20260822`  
**Written (AEST):** 2026-08-22T22:40:00+10:00  
**Target safe SoT:** MQTT **CLOSED** (no listener on 1883 / prior pre-enable state) + no UFW public 1883

## Steps

1. `systemctl stop <broker-unit>` then `systemctl disable <broker-unit>` (unit name = the one enabled/started in execute; typically `mosquitto`).
2. Restore prior conf (disable listener / re-apply MQTT_DISABLED policy / revert conf.d drop-in added during execute). Prefer reversing the **same** drop-in rather than deleting unrelated files.
3. Remove any LAN-only firewall allow for TCP 1883 added during execute. Confirm **no** `Anywhere` / WAN allow remains for 1883/8883.
4. Confirm `ss`: nothing listening on 1883 (or exact pre-CHG recorded state).
5. Doctor: if an existing mqtt/1883 field was updated during execute, restore prior CLOSED/DISABLED assertion in receipt. Do **not** Doctor auto-patch.
6. Leave board-local password_file secrets in place or rotate per owner follow-up - do **not** copy secrets to laptop evidence during rollback.
7. Receipt: `ROLLBACK-ACK` with before/after listen addresses, unit name, conf path restored, firewall delta.

## Abort / escalate

If unit fails to stop or a foreign process still binds 1883 -> stop further mutate; kill only the known broker PID if safe; report journals to owner via ari. Never open WAN as a "fix".
