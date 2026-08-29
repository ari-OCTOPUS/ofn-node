from octopus_cognition.homeostasis.core import classify, evaluate
from octopus_cognition.homeostasis.models import (
    HomeostaticMode,
    VariableSpec,
    VariableStatus,
    VitalSeverity,
    interpret_mode,
)


CPU = VariableSpec("compute_pressure", "cpu_utilisation", (0.0, 0.70), critical_high=0.90)


def test_idle_cpu_is_healthy_not_attracted_to_45_percent():
    snap = evaluate(
        {
            "compute_pressure": 0.10,
            "memory_pressure": 0.18,
            "thermal_integrity": 27.0,
            "storage_integrity": 0.05,
            "evidence_freshness": 4.0,
            "sensor_coverage": 0.95,
            "model_skill": None,
            "prediction_calibration": None,
        }
    )
    assert snap.variables["compute_pressure"].status == VariableStatus.HEALTHY
    assert snap.host_in_range is True
    assert snap.mode == HomeostaticMode.NORMAL
    assert snap.severity == VitalSeverity.HEALTHY
    assert "model_skill" in snap.unknown
    assert snap.variables["model_skill"].value is None


def test_missing_skill_is_unknown_not_zero():
    snap = evaluate({"compute_pressure": 0.1, "model_skill": 0.0, "prediction_calibration": 0.0})
    # explicit zero is a real reading; callers must omit the key or pass None
    snap_none = evaluate({"compute_pressure": 0.1, "model_skill": None, "prediction_calibration": None})
    assert snap_none.variables["model_skill"].status == VariableStatus.UNKNOWN
    assert snap_none.variables["model_skill"].value is None
    assert snap.variables["model_skill"].status == VariableStatus.CRITICAL


def test_low_coverage_is_critical_not_filled():
    snap = evaluate(
        {
            "compute_pressure": 0.1,
            "memory_pressure": 0.2,
            "thermal_integrity": 30.0,
            "storage_integrity": 0.05,
            "evidence_freshness": 5.0,
            "sensor_coverage": 0.50,
            "model_skill": None,
            "prediction_calibration": None,
        }
    )
    assert snap.variables["sensor_coverage"].status == VariableStatus.CRITICAL
    assert snap.host_in_range is True
    assert snap.data_ok is False
    assert snap.in_envelope is True
    assert snap.homeostasis_ok is False
    assert snap.mode == HomeostaticMode.WOULD_LOCKDOWN
    assert snap.severity == VitalSeverity.CRITICAL
    assert snap.mode != "lockdown"


def test_protect_label_maps_to_would_lockdown():
    assert interpret_mode("protect") is HomeostaticMode.WOULD_LOCKDOWN
    assert interpret_mode("lockdown") is HomeostaticMode.WOULD_LOCKDOWN
    assert interpret_mode(HomeostaticMode.WOULD_LOCKDOWN) is HomeostaticMode.WOULD_LOCKDOWN
    assert not hasattr(HomeostaticMode, "LOCKDOWN")
    assert not hasattr(HomeostaticMode, "PROTECT")


def test_classify_watch_between_healthy_and_critical():
    assert classify(CPU, 0.80, False) == VariableStatus.WATCH
    assert classify(CPU, 0.91, False) == VariableStatus.CRITICAL
    assert classify(CPU, 0.20, False) == VariableStatus.HEALTHY
    assert classify(CPU, None, False) == VariableStatus.UNKNOWN
