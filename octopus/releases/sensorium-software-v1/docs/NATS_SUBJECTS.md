# NATS_SUBJECTS

Streams (historical, 8): SENSORIUM, OBSERVATION, FEATURE, SENSOR_HEALTH, WORLD, AUDIT, COMMAND, LEG.

Subjects used by the agent:
- octopus.sensor.observation.<id>
- octopus.sensor.feature.<id>
- octopus.sensor.health.<id>
- octopus.sensor.anomaly.OCT-SENSE-092
- octopus.world.contradiction
- octopus.sensorium.{heartbeat,health,birth,alert,capabilities}
- octopus.audit.sensorium
- octopus.command.sensorium (receive only; commands do not execute)

EVIDENCE and ANOMALIES streams are not provisioned. Local evidence jsonl is the store.
A provisioning bundle exists; runtime must not create streams.
