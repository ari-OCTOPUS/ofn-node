"""Observation consume is Core-side. This agent does not subscribe to octopus.sensor.observation.>."""

AGENT_SUBSCRIBES = (
    "octopus.command.sensorium",
    "octopus.leg.*.birth",
    "_INBOX.>",
)

AGENT_MUST_NOT_SUBSCRIBE = (
    "octopus.sensor.observation.>",
    "octopus.sensor.anomaly.>",
    "octopus.world.contradiction",
)
