# PLAN — ESP32 + internet public data START (ABD propose)

**Package id:** OCTOPUS-ORANGEPI-ESP32-INET-DATA-START-20260822  
**Status:** PROPOSED / NEED_OWNER_EXECUTE_GRANT (mutate_device TBD)  
**Board:** sensorium-opi5pro  
**Executor (future):** sensoriom  
**Laptop:** ari writes grant + BRIEF; sensoriom executes after BRIEF

## Intent

Start professional organism growth via (A) honest public internet/dataset feeds into Sensorium Observations and (B) prepare ESP32 sensor telemetry path — **without** buying physical e-stop yet and **without** unlocking WAVE0 hardware actuators.

## Phase A — Inet public data ingest (software-only, EXECUTE-ready once granted)

1. Allowlist of public sources (examples to confirm per license/ToS before fetch):
   - Australia BOM / open weather observations (Sydney) — public feed if ToS allows automated fetch
   - Open-Meteo (non-commercial terms) or similar documented open API
   - Curated CSV/JSON datasets dropped under `/var/lib/octopus/inbound/FROM-LAPTOP/datasets/` (owner-curated, provenance file required)
2. Implement observe-only plugin or sidecar:
   - Read allowlisted URL or local file
   - Emit `Observation` via existing NATS `OBSERVATION` path OR write evidence JSONL consumed by a MANIFEST→SHADOW sensor id reserved for EXTERNAL_FEED
   - Mark provenance: `source_type=EXTERNAL_PUBLIC_FEED`, `authority=external`, never claim board phenomenon_time as local hardware
3. Do **not** promote EXTERNAL_FEED into WAVE0 required coverage set (051–053) without owner gate.
4. Torch already installed (cpu) — optional later training job on Pi or laptop using exported features; out of scope for first mutate unless BRIEF says so.

## Phase B — ESP32 telemetry path (discover hardware first)

1. Precheck: USB serial appear? WiFi endpoint documented?
2. Prefer JSON line protocol → Pi agent → Observation (no actuator topics).
3. Alternate: finish MQTT loopback auth, then enable `OCT-SENSE-064` via **signed** registry (laptop root-v2), still observe-only.
4. Forbidden: PWM/leg/motor topics; treating ESP32 GPIO as estop substitute without PARTS + prove.

## Phase C — Later replace

When real sensors + physical estop exist: cut EXTERNAL_FEED to secondary/shadow; promote physical streams; then consider Path H.

## Explicit non-goals this package

Buy parts; WAVE0 hardware unlock; invent PWM; WAN MQTT; mining ESP32 flash; Doctor auto-patch; CHG-C re-run.
