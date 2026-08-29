from __future__ import annotations

import pytest

from octopus_sensorium.schema_ids import SensorIdCollision, assert_no_sensor_id_collision


def test_thermal_must_not_use_054():
    with pytest.raises(SensorIdCollision):
        assert_no_sensor_id_collision(
            [
                {
                    "sensor_id": "OCT-SENSE-054",
                    "name": "thermal",
                    "plugin": {"type": "thermal"},
                }
            ]
        )


def test_canonical_wave0_ids_ok():
    assert_no_sensor_id_collision(
        [
            {"sensor_id": "OCT-SENSE-051", "name": "filesystem", "plugin": {"type": "filesystem"}},
            {"sensor_id": "OCT-SENSE-053", "name": "system_resources", "plugin": {"type": "system_resources"}},
            {
                "sensor_id": "OCT-SENSE-053.THERMAL",
                "name": "board_thermal",
                "plugin": {"type": "thermal"},
            },
            {"sensor_id": "OCT-SENSE-054", "name": "structured_logs", "status": "not_enabled"},
        ]
    )
