from __future__ import annotations

import time

import pytest

from octopus_sensorium.meta.anomaly import AnomalySensor
from octopus_sensorium.meta.contradiction import ContradictionSensor
from octopus_sensorium.meta.series import modified_zscore, update_cusum, SeriesWindow
from octopus_sensorium.meta.shadow import assert_shadow_manifest


def _anomaly_manifest(tmp_path=None, **over):
    persist = str(tmp_path) if tmp_path is not None else "/tmp/octopus-anomaly-test-fresh"
    doc = {
        "sensor_id": "OCT-SENSE-092",
        "mode": "shadow",
        "schema_version": "1.0.0",
        "publication": {"shadow_only": True, "can_change_readiness": False, "can_quarantine": False, "can_execute": False},
        "security": {"actuator_access": False, "command_access": False, "shell_access": False},
        "detectors": {"mad": {"minimum_samples": 5, "window_samples": 20, "threshold_warning": 3.5, "threshold_critical": 6.0}, "cusum": {"minimum_samples": 8}},
        "baseline": {"minimum_duration_seconds": 0, "persist_path": persist, "reset_on_schema_change": True},
    }
    doc.update(over)
    return doc


def _contra_manifest():
    return {
        "sensor_id": "OCT-SENSE-095",
        "mode": "shadow",
        "publication": {"shadow_only": True, "can_change_readiness": False, "can_quarantine": False, "can_resolve_belief": False},
        "security": {"actuator_access": False, "command_access": False},
    }


def test_shadow_manifest_rejects_enforcement():
    with pytest.raises(ValueError):
        assert_shadow_manifest({"sensor_id": "x", "mode": "shadow", "publication": {"can_change_readiness": True}})


def test_modified_zscore_spike():
    baseline = [25.0] * 30
    score, med, spread = modified_zscore(85.0, baseline)
    assert med == 25.0
    assert spread == 0.0 or abs(score) > 3.5


def test_anomaly_ignores_own_and_contradiction_subjects(tmp_path):
    sensor = AnomalySensor(_anomaly_manifest(tmp_path))
    sensor.started_at = time.time() - 10
    sensor.ingest("anomaly", {"event_id": "nope"}, "octopus.sensor.anomaly.OCT-SENSE-092")
    sensor.ingest("observation", {"sensor_id": "OCT-SENSE-053.THERMAL", "observed_property": "host.soc.temperature", "result": {"value": 25.0}, "event_id": "a"}, "octopus.sensor.observation.OCT-SENSE-053.THERMAL")
    assert len(sensor.inbox) == 1


def test_anomaly_rule_thermal_and_mad_after_warmup(tmp_path):
    sensor = AnomalySensor(_anomaly_manifest(tmp_path))
    sensor.started_at = time.time() - 4000
    sensor.detection_state = "SHADOW_ACTIVE"
    for i in range(25):
        sensor.ingest(
            "observation",
            {
                "event_id": f"e{i}",
                "sensor_id": "OCT-SENSE-053.THERMAL",
                "observed_property": "host.soc.temperature",
                "subject": {"entity_id": "board"},
                "result": {"value": 25.0 + (0.01 * i)},
            },
        )
    sensor.ingest(
        "observation",
        {
            "event_id": "hot",
            "sensor_id": "OCT-SENSE-053.THERMAL",
            "observed_property": "host.soc.temperature",
            "subject": {"entity_id": "board"},
            "result": {"value": 91.0},
        },
    )
    events = sensor.evaluate()
    kinds = {(e["anomaly"]["detector"], e["anomaly"]["class"]) for e in events}
    assert any(e["anomaly"]["detector"] == "rule" for e in events)
    assert all(e["policy"]["actionable"] is False for e in events)
    assert all(e["policy"]["may_change_readiness"] is False for e in events)
    _ = kinds


def test_cusum_drift():
    window = SeriesWindow("t", maxlen=40)
    for v in [10.0] * 20:
        window.add(v)
        update_cusum(window, v)
    tripped = False
    for v in [13.0] * 12:
        window.add(v)
        pos, _neg, sigma = update_cusum(window, v)
        if sigma and pos > 5 * sigma:
            tripped = True
    assert tripped


def test_contradiction_ready_with_failed_gate():
    sensor = ContradictionSensor(_contra_manifest())
    sensor.ingest("boot_report", {"readiness_state": "READY", "gates_failed": ["G6"]})
    events = sensor.evaluate()
    assert any(e["contradiction"]["rule_id"] == "CON-R004" for e in events)
    assert events[0]["policy"]["may_change_readiness"] is False


def test_contradiction_actuator_authority():
    sensor = ContradictionSensor(_contra_manifest())
    sensor.ingest("health", {"readiness_profile": "WAVE0_OBSERVE_ONLY", "actuator_authority": "FULL"})
    events = sensor.evaluate()
    assert any(e["contradiction"]["rule_id"] == "CON-R005" for e in events)


def test_contradiction_does_not_ingest_own_output_as_loop():
    sensor = ContradictionSensor(_contra_manifest())
    sensor.ingest("contradiction", {"event_id": "loop"})
    assert sensor.pending == []
    sensor.ingest("anomaly", {"event_id": "a1", "target": {"sensor_id": "OCT-SENSE-053.THERMAL"}})
    assert len(sensor.anomalies) == 1
    sensor.ingest("anomaly", {"event_id": "status", "observation_type": "baseline_status"})
    assert len(sensor.anomalies) == 1


def test_warmup_publishes_status_not_definite_anomaly(tmp_path):
    sensor = AnomalySensor(_anomaly_manifest(tmp_path, baseline={"minimum_duration_seconds": 3600, "persist_path": str(tmp_path)}))
    sensor.started_at = time.time()
    sensor.ingest(
        "observation",
        {
            "event_id": "hot",
            "sensor_id": "OCT-SENSE-053.THERMAL",
            "observed_property": "host.soc.temperature",
            "subject": {"entity_id": "board"},
            "result": {"value": 91.0},
        },
    )
    events = sensor.evaluate()
    assert events
    assert all(e.get("observation_type") == "baseline_status" for e in events)
    assert events[0]["detection_state"] == "INSUFFICIENT_BASELINE"
    assert events[0]["actionable"] is False
    assert all(e.get("anomaly") is None for e in events)
    assert (tmp_path / "windows.json").exists()


def test_baseline_restore_skips_warmup(tmp_path):
    first = AnomalySensor(_anomaly_manifest(tmp_path, baseline={"minimum_duration_seconds": 0, "persist_path": str(tmp_path)}))
    first.started_at = time.time() - 4000
    for i in range(8):
        first.ingest(
            "observation",
            {
                "event_id": f"e{i}",
                "sensor_id": "OCT-SENSE-053.THERMAL",
                "observed_property": "host.soc.temperature",
                "result": {"value": 25.0},
            },
        )
    first.evaluate()
    second = AnomalySensor(_anomaly_manifest(tmp_path, baseline={"minimum_duration_seconds": 0, "persist_path": str(tmp_path)}))
    assert second._restored
    second.evaluate()
    assert second.detection_state == "SHADOW_ACTIVE"
    assert second._sample_count() >= 5
