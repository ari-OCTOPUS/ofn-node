# P0 DISCOVERY — persistent fleet (READ ONLY)

UTC: 2026-09-15T03:27:37Z

SEC SoT: `GO-PERSISTENT-FLEET-EXEC-20260915.md` sha `52887e1a088d6d4e87f2a8c14879db392a647d450afe8473ea0a5e620022d268`

## Verdicts

- **NATS_ON_182:** `YES`
- **NATS_ON_138:** `UNKNOWN`
- **JETSTREAM:** `YES`
- **JETSTREAM_CONSUMER_PROOF:** `PARTIAL_ZERO_CONSUMERS`
- **NATS_MONITOR_8222_FROM_138_TO_182:** `UNREACHABLE`
- **JETSTREAM_DETAIL_182:** `{'memory': 0, 'storage': 31726959, 'streams': 8, 'consumers': 0, 'messages': 68814, 'bytes': 31726959, 'config_store': None}`
- **JETSTREAM_STREAMS:** `['FEATURE', 'LEG', 'OBSERVATION', 'SENSORIUM', 'SENSOR_HEALTH', 'WORLD', 'AUDIT', 'COMMAND']`

## 182 JetStream streams

| stream | messages | consumers | subjects |
|---|---|---|---|
| FEATURE | 7353 | 0 | octopus.sensor.feature.> |
| LEG | 0 | 0 | octopus.leg.> |
| OBSERVATION | 3125 | 0 | octopus.sensor.observation.> |
| SENSORIUM | 262 | 0 | octopus.sensorium.> |
| SENSOR_HEALTH | 1071 | 0 | octopus.sensor.health.>, octopus.sensor.anomaly.> |
| WORLD | 1575 | 0 | octopus.world.> |
| AUDIT | 55425 | 0 | octopus.audit.> |
| COMMAND | 0 | 0 | octopus.command.> |

## 138 file surfaces (observe only)

- NATS server: **inactive / unit absent**
- mesh inbox empty; outbox has dated JSON
- autonomy `queue.jsonl` at `/home/ari/ofn/state/autonomy/queue.jsonl`
- revenue-drive queues exist — **DENY reuse for brain**

## ARCH gap closed

- 138→182:8222 LAN curl: **timeout** (monitor bound `http_host=127.0.0.1`)
- Proof path: mesh SSH root@182 then localhost:8222/jsz

No enqueue. No dual-commander. **STOP before P1.** HOLD customer_send.
