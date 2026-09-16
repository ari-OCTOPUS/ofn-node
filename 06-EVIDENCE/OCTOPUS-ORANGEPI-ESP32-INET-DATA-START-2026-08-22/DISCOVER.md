# DISCOVER SUMMARY — ESP32 / inet-data start (Orange Pi)

**Session:** OCTOPUS-ORANGEPI-ESP32-INET-DATA-START-2026-08-22  
**Board:** sensorium-opi5pro @ 192.168.0.182  
**Written (AEST):** 2026-08-22T22:50:00+10:00 (approx)  
**Auth context:** owner strategy via ari (register + propose; NOT buy; NOT unlock actuators)  
**Board evidence:** `/var/lib/octopus/evidence/session-esp32-inet-data-start-20260822/`

## MQTT status (in-flight prior)

- ENABLE ABD reached `unit=failed` (no `127.0.0.1:1883` listen).
- **PARKED** under OWNER STRATEGY supersede: broker stopped/disabled intent; `ss` 1883 = NONE; no UFW 1883; **CLOSED**.
- Receipt: `/var/lib/octopus/inbound/TO-LAPTOP/exchange/RECEIPT-MQTT-ENABLE.json` → `result=PARKED_FAIL_UNIT`.
- Re-open only with a fix BRIEF (conf/journal debug) — do not continue in this package window.

## WAVE0

- `KEEP_WAVE0_LOCKED` / `actuator_authority=NONE`
- Software ESTOP_LATCH PROVE PASS; hardware still `BLOCKED_NEED_ESTOP` (`safety_mcu=ABSENT`)
- Physical PARTS-LIST deferred (stays on disk); **no buy** this package

## ESP32 hooks on Orange Pi / octopus tree

| Surface | Finding |
|---------|---------|
| Code/docs `esp32` / Espressif under `/opt/octopus` | **NONE** |
| USB serial ESP (`ttyUSB`/`ttyACM`/CH340/CP210) | **NONE attached** (hubs only) |
| Sensor plugins present | Host only: `filesystem_watch`, `system_resources`, `thermal`, `process` |
| `OCT-SENSE-064 mqtt_bridge` | `DISABLED_BY_POLICY` — reason historically "port 1883 must stay closed"; `mqtt_forbidden: true` |
| Live ACTIVE host set | 051/052/053 (+ thermal) — WAVE0 required set |
| SHADOW meta | 092 anomaly, 095 contradiction (and related shadow counts) |
| MANIFEST_ONLY | ~62 sensors (slots exist; no plugin yet) including network/otel slots |
| Ingest bus | NATS JetStream `OBSERVATION` / `SENSORIUM` / `FEATURE` — universal `Observation` envelope in `models/observation.py` |
| Laptop ESP32 trees | Mining deploy paths under `.claude/worktrees/**/Mining/**/esp32` — **Mining deferred / out of organism queue**; do not wire mining firmware into Sensorium without separate owner reopen |

## Honest growth path (proposed)

1. **Inet public feeds (software, no PWM):** new observe-only ingest that pulls **licensed/public** datasets/APIs into Observation envelopes with `provenance` marking `EXTERNAL_PUBLIC_FEED` / `untrusted_content` as appropriate. Prefer file-drop or HTTPS GET allowlist. Never invent sensor values; never zero-fill missing physical sensors.
2. **ESP32 telemetry later:** when a board is present — USB-UART JSON lines **or** (after MQTT fix) publish into local MQTT then bridge via OCT-SENSE-064 under signed registry change. Keep actuators/PWM/legs locked.
3. **Replace later:** swap EXTERNAL_PUBLIC_FEED sources for real physical streams once ESP32+sensors (+ estop parts) exist.

## Constraints carried forward

- No invent unsafe PWM / legs / Path H unlock
- No buy parts this package
- No secrets to chat; MQTT remains CLOSED until fix BRIEF
- Signed `registry.yaml` changes need laptop sign path (not casual edit on Pi)
