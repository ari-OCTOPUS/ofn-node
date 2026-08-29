"""Historical Wave 0 identifier migrations. Evidence of the old IDs is preserved."""

MIGRATIONS = (
    {
        "from": {"sensor_id": "OCT-SENSE-002", "semantic": "board_thermal"},
        "to": {"sensor_id": "OCT-SENSE-053.THERMAL", "semantic": "host.soc.temperature"},
        "reason": "sensor identifier collision with SENSORIUM-100 OCT-SENSE-054 logs",
    },
    {
        "from": {"sensor_id": "OCT-SENSE-054", "semantic": "board_thermal"},
        "to": {"sensor_id": "OCT-SENSE-053.THERMAL", "semantic": "host.soc.temperature"},
        "reason": "sensor identifier collision",
    },
    {
        "from": {"sensor_id": "OCT-SENSE-001", "semantic": "system_resources"},
        "to": {"sensor_id": "OCT-SENSE-053", "semantic": "host.system_resources"},
        "reason": "SENSORIUM-100 host sensor numbering",
    },
    {
        "from": {"sensor_id": "OCT-SENSE-003", "semantic": "filesystem"},
        "to": {"sensor_id": "OCT-SENSE-051", "semantic": "filesystem"},
        "reason": "SENSORIUM-100 host sensor numbering",
    },
)


def apply_id_migration(sensor_id: str) -> str:
    for event in MIGRATIONS:
        if event["from"]["sensor_id"] == sensor_id:
            return str(event["to"]["sensor_id"])
    return sensor_id
