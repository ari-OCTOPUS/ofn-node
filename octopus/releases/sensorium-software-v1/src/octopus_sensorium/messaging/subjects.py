"""NATS subject names. The agent must not create or delete streams."""

SENSORIUM_HEARTBEAT = "octopus.sensorium.heartbeat"
SENSORIUM_HEALTH = "octopus.sensorium.health"
SENSORIUM_BIRTH = "octopus.sensorium.birth"
SENSORIUM_ALERT = "octopus.sensorium.alert"
SENSORIUM_CAPABILITIES = "octopus.sensorium.capabilities"
COMMAND_SENSORIUM = "octopus.command.sensorium"
LEG_BIRTH_WILDCARD = "octopus.leg.*.birth"
ANOMALY_092 = "octopus.sensor.anomaly.OCT-SENSE-092"
CONTRADICTION_095 = "octopus.world.contradiction"


def observation_subject(sensor_id: str) -> str:
    return f"octopus.sensor.observation.{sensor_id}"


def feature_subject(sensor_id: str) -> str:
    return f"octopus.sensor.feature.{sensor_id}"


def health_subject(sensor_id: str) -> str:
    return f"octopus.sensor.health.{sensor_id}"
