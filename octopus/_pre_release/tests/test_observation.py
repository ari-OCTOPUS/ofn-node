from __future__ import annotations

from octopus_sensorium.observation import make_observation
from octopus_sensorium.pipeline import PipelineError, run_pipeline
from octopus_sensorium.sensors.base import RawObservation


def test_observation_has_provenance_and_clock_trust():
    obs = make_observation(
        board_id="sensorium-opi5pro-68e44cdf",
        sensor_id="OCT-SENSE-053.THERMAL",
        sensor_agent_id="agent://sensor/OCT-SENSE-053.THERMAL",
        observed_property="host.soc.temperature",
        value=24.1,
        unit="Cel",
        sequence_number=1,
        source_id="sysfs-thermal",
        collector_version="0.1.0",
        transformations=["milliC_to_C"],
        clock_trust="SYNCED_NTP",
    )
    assert obs["provenance"]["content_hash"].startswith("sha256:")
    assert obs["provenance"]["clock_trust"] == "SYNCED_NTP"
    assert obs["provenance"]["signature_verified"] is False
    assert obs["result"]["encoding"] == "json"
    assert obs["policy"]["actionable"] is False
    assert obs["evidence"]["supporting_event_ids"] == []
    assert obs["quality"]["valid"] is True
    assert obs["time"]["valid_until"]
    assert obs["sensorium_board_id"] == "sensorium-opi5pro-68e44cdf"


def test_pipeline_drops_out_of_range():
    raw = RawObservation(payload={"sequence": 1}, source_id="x", bytes_len=16)
    try:
        run_pipeline(
            raw,
            board_id="b",
            sensor_id="s",
            sensor_agent_id="a",
            observed_property="t",
            value=9000,
            unit="Cel",
            sequence_number=1,
            source_id="x",
            collector_version="0.1.0",
            transformations=[],
            clock_trust="SYNCED_NTP",
            ttl_seconds=5,
            range_check=lambda v: -40 <= float(v) <= 125,
        )
        assert False, "should have failed"
    except PipelineError as exc:
        assert exc.stage == "RANGE_CHECK"
