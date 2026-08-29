# OCTOPUS Sensorium Wave 0 — architecture (Deliverable 3)

Wave 0 messaging is implemented with **NATS Core and JetStream**.
NATS Core provides the live Observation and telemetry path.
JetStream provides retention, replay, and durable consumers.
Redis, if used at all, is only a cache or short-lived state store for
other OCTOPUS components. It is not the Sensorium backbone.

| Concern | Retired choice | Final decision |
|---|---|---|
| Sensory bus | Redis Streams | NATS Core + JetStream |
| Live messages | Redis consumer groups | NATS pub/sub |
| Durable data | Redis Streams | JetStream streams |
| MCU boards | undefined | MQTT listener or NATS client |
| Provisioning | inside Sensorium Agent | independent `sensorium-provisioner` tool |
| Agent access | create streams | limited publish/consume |
| Provisioner access | undefined | stream management, no actuator access |

## Ownership

```
sensorium-provisioner   (one-shot, not a daemon)
    ├── create/update streams
    ├── create durable consumers
    ├── verify retention limits
    ├── apply schema migration
    └── exit

sensorium-agent
    ├── publish observations
    ├── publish health
    ├── consume signed commands
    ├── consume active-sensing requests
    └── never create/delete streams
```

The runtime agent must not hold `$JS.API.STREAM.>` or `$JS.API.CONSUMER.>`.
After bootstrap, provisioner credentials stay off the agent user and should
be removed or disabled on the board.
