# SENSORIOM-EXECUTE-BRIEF - ESP32-INET-DATA-START Phase A ONLY

**Package:** OCTOPUS-ORANGEPI-ESP32-INET-DATA-START-2026-08-22
**Status:** EXECUTE_READY_PHASE_A
**Board:** sensorium-opi5pro @ 192.168.0.182
**Executor:** sensoriom
**Auth:** mutate_device=true; phase=A_EXTERNAL_PUBLIC_FEED_ONLY; tokens OCTOPUS-ESP32-INET-DATA-START-20260822 + OCTOPUS-ALL-DOORS-OPEN-20260822
**Locks:** no_pwm=true; wave0_keep_locked=true; esp32_hardware=deferred; mqtt=PARKED_CLOSED
**Written (AEST):** 2026-08-22T22:51:00+10:00

---

## Phase A - Observe-only public feed ingest (EXECUTE NOW)

### Goal
Ingest allowlisted **public** internet feeds into the existing NATS JetStream **OBSERVATION** envelope (`models/observation.py`). Observe-only. No invent. No zero-fill. Do not promote into WAVE0 required set (051-053).

### DISCOVER_FIRST - allowlist (verified 2026-08-22 AEST)

| Source | URL / path | Status | Notes |
|--------|------------|--------|-------|
| Open-Meteo Sydney weather | `https://api.open-meteo.com/v1/forecast?latitude=-33.8688&longitude=151.2093&current=temperature_2m,relative_humidity_2m,weather_code` | **PUBLIC OK** | Non-commercial ToS; HTTPS GET JSON |
| Time (worldtimeapi alternative) | `https://timeapi.io/api/Time/current/zone?timeZone=Australia/Sydney` | **PUBLIC OK** | worldtimeapi.org returned 503/500 at verify - do **not** hard-depend on it; prefer timeapi.io or re-check worldtimeapi before enable |
| Optional FX AUD | `https://api.frankfurter.dev/v1/latest?base=AUD&symbols=USD,EUR` | **PUBLIC OK** | frankfurter.dev / frankfurter.app; optional |
| FROM-LAPTOP datasets | `/var/lib/octopus/inbound/FROM-LAPTOP/datasets/` | Local drop | Owner-curated JSON/CSV + provenance sidecar required |

**Forbidden feeds:** paywall scrape; OnlyFans / adult; mining pools / mining ESP32 organism feeds; invent values; BOM scrape if ToS blocks automated fetch (prefer Open-Meteo).

### Implementation steps (sensoriom)

1. **Confirm locks before mutate**
   - MQTT still PARKED/CLOSED (no 1883 listen; do not reopen).
   - WAVE0 / actuator_authority remains NONE / KEEP_LOCKED.
   - No PWM / Path H / legs.

2. **FROM-LAPTOP drop path** (if used)
   - Ensure dir: `/var/lib/octopus/inbound/FROM-LAPTOP/datasets/`
   - Each drop: data file + `provenance.json` (`source_type`, `curator`, `license`, `fetched_at` or `dropped_at`).
   - Reject drops without provenance.

3. **Observe-only ingest**
   - Plugin or sidecar: HTTPS GET allowlist **or** read local dataset file.
   - Emit `Observation` on NATS `OBSERVATION` (or evidence JSONL consumed by reserved sensor id).
   - Provenance required on every obs:
     - `source_type=EXTERNAL_PUBLIC_FEED`
     - `authority=external`
     - `untrusted_content` as appropriate
     - Never claim phenomenon_time as local hardware board sense.

4. **Signed registry slot** (only if new sensor id required)
   - Prefer unused MANIFEST_ONLY network/meta slot.
   - Registry change via **laptop signed** path (root-v2) - no casual edit on Pi.
   - Do **not** add EXTERNAL_FEED into WAVE0 required coverage.

5. **Prove**
   - Observations land (NATS / evidence / sensor shadow or active as designed).
   - `doctor` / health path **not broken** (no fail-unit regression; existing 051/052/053 stay healthy).
   - Write receipt -> `/var/lib/octopus/inbound/TO-LAPTOP/exchange/` and copy into this package `FROM-PI/`.

6. **Rollback**
   - Disable feed sensor / stop sidecar / revert registry enable.
   - Leave MQTT CLOSED; leave WAVE0 locked.
   - Receipt `result=ROLLED_BACK` if invoked.

### Phase B - DEFERRED (do not execute)

- ESP32 USB-UART JSON telemetry **deferred until hardware present** (`esp32_hardware=deferred`).
- Precheck later: ttyUSB/ttyACM appear; then separate BRIEF reopen.
- No mining ESP32 wire; no PWM topics.

---

## Forbidden (all phases this package)

Buy parts; WAVE0 Path H / PWM / legs unlock; WAN MQTT; invent / zero-fill; mining ESP32; secrets in chat; paywall/OF/mining feeds; Phase B mutate without hardware + reopen.
