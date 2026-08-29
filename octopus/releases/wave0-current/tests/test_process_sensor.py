from __future__ import annotations

import pytest

from octopus_sensorium.pipeline import PipelineError, run_pipeline
from octopus_sensorium.sensors.base import RawObservation, SensorError
from octopus_sensorium.sensors.process.process_sensor import (
    ProcessSensor,
    assert_no_command_line,
    read_unit,
    redact_secret_text,
)


def _manifest(**overrides):
    doc = {
        "sensor_id": "OCT-SENSE-052",
        "watchlist": {
            "units": [{"unit": "nats-server.service", "critical": True}],
            "processes": [{"label": "nats", "match_executable": "^nats-server$", "minimum_count": 1}],
        },
        "privacy": {"redact_command_line": True, "collect_command_args": False, "collect_environment": False},
        "security": {"actuator_access": False, "shell_access": False},
    }
    doc.update(overrides)
    return doc


def test_empty_watchlist_is_sensor_error():
    with pytest.raises(SensorError):
        ProcessSensor({"sensor_id": "OCT-SENSE-052", "watchlist": {}})


def test_redaction_patterns():
    text = "token=abc123 bearer XYZ.123 $2b$11$" + ("a" * 53) + " https://u:p@host/x"
    out = redact_secret_text(text)
    assert "abc123" not in out
    assert "XYZ.123" not in out
    assert "$2b$11$" not in out
    assert "u:p@" not in out


def test_command_line_rejected():
    with pytest.raises(SensorError):
        assert_no_command_line({"process.command_line": "/usr/bin/nats-server -c /secret"})


def test_observe_has_no_command_line_and_stays_under_20():
    sensor = ProcessSensor(_manifest())
    items = sensor._observations()
    assert items
    assert len(items) <= 20
    blob = str(items).lower()
    assert "command_line" not in blob
    assert "command_args" not in blob
    props = {i["observed_property"] for i in items}
    assert "octopus.unit.healthy" in props
    assert "system.process.count" in props


def test_unit_uses_active_and_sub_state():
    info = read_unit("nats-server.service")
    assert info["found"] is True
    assert "active_state" in info
    assert "sub_state" in info
    assert info["healthy"] == (info["active_state"] == "active" and info["sub_state"] == "running")


def test_self_test_finds_watchlist_units():
    import asyncio

    sensor = ProcessSensor(
        _manifest(
            watchlist={
                "units": [
                    {"unit": "octopus-sensorium.service", "critical": True},
                    {"unit": "nats-server.service", "critical": True},
                    {"unit": "systemd-timesyncd.service", "critical": False},
                ],
                "processes": [{"label": "nats", "match_executable": "^nats-server$"}],
            }
        )
    )
    result = asyncio.run(sensor.self_test())
    assert result.passed
    assert "nats-server.service" in result.measurements["units_found"]
    assert "systemd-timesyncd.service" in result.measurements["units_found"]
    assert "octopus-sensorium.service" in result.measurements["units_found"]


def test_pipeline_drops_command_line_value():
    raw = RawObservation(payload={"sequence": 1}, source_id="x", bytes_len=8)
    with pytest.raises(PipelineError) as exc:
        run_pipeline(
            raw,
            board_id="b",
            sensor_id="OCT-SENSE-052",
            sensor_agent_id="a",
            observed_property="process.cpu.utilization",
            value={"command_line": "nats-server --token secret"},
            unit="1",
            sequence_number=1,
            source_id="x",
            collector_version="0.1.0",
            transformations=[],
            clock_trust="SYNCED_NTP",
            ttl_seconds=5,
        )
    assert exc.value.stage == "PRIVACY_FILTER"


def test_monotonic_clock_marks_time_unverified():
    raw = RawObservation(payload={"sequence": 1}, source_id="x", bytes_len=8)
    obs = run_pipeline(
        raw,
        board_id="b",
        sensor_id="OCT-SENSE-053.THERMAL",
        sensor_agent_id="a",
        observed_property="host.soc.temperature",
        value=22.0,
        unit="Cel",
        sequence_number=1,
        source_id="x",
        collector_version="0.1.0",
        transformations=[],
        clock_trust="MONOTONIC_ONLY",
        ttl_seconds=5,
        range_check=lambda v: -40 <= float(v) <= 125,
    )
    assert obs["quality"]["time_unverified"] is True
    assert obs["provenance"]["clock_trust"] == "MONOTONIC_ONLY"
