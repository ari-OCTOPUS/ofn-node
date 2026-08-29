from octopus_cognition.doctor import DoctorCheck, doctor_status, require_key
from octopus_cognition.doctor.chain import GENESIS, canonical, chain_hash
from octopus_cognition.doctor.coverage import observation_datetime


def test_blocking_fail_is_fail():
    checks = [
        DoctorCheck("a", "integrity", "blocking", "FAIL", "PASS", "/e", passed=False),
    ]
    assert doctor_status(checks) == "FAIL"


def test_degrading_without_blocking_is_degraded():
    checks = [
        DoctorCheck("a", "integrity", "blocking", "PASS", "PASS", "/e", passed=True),
        DoctorCheck("b", "sensing", "degrading", "STALE", "FRESH", "/e2", passed=False),
    ]
    assert doctor_status(checks) == "DEGRADED"


def test_missing_evidence_is_unknown_not_pass():
    checks = [
        DoctorCheck("a", "integrity", "blocking", "PASS", "PASS", None, passed=True),
    ]
    assert doctor_status(checks) == "UNKNOWN"


def test_all_pass_with_evidence():
    checks = [
        DoctorCheck("a", "integrity", "blocking", "PASS", "PASS", "/e", passed=True),
        DoctorCheck("b", "sensing", "informational", "MISSING", "PRESENT", "/e2", passed=False),
    ]
    assert doctor_status(checks) == "PASS"


def test_missing_metric_key_is_not_zero():
    result = require_key({"cpu_ratio": 0.1}, "sensor_coverage")
    assert result is not None
    assert result.observed == "MISSING"
    assert result.reason == "missing_not_healthy"
    assert result.passed is False


def test_chain_hash_is_order_independent_via_canonical():
    a = {"z": 1, "a": 2}
    b = {"a": 2, "z": 1}
    assert canonical(a) == canonical(b)
    assert chain_hash(GENESIS, a) == chain_hash(GENESIS, b)


def test_chain_edit_breaks_successor():
    h1 = chain_hash(GENESIS, {"n": 1})
    h2 = chain_hash(h1, {"n": 2})
    tampered = chain_hash(GENESIS, {"n": 99})
    assert chain_hash(tampered, {"n": 2}) != h2


def test_meta_sensor_timestamp_not_imputed():
    dt, src = observation_datetime({"anomaly": {"score": 1}})
    assert dt is None
    assert src == "MISSING_TIMESTAMP"
    dt2, src2 = observation_datetime(
        {"evidence": {"baseline_window_end": "2026-08-17T04:00:00+00:00"}}
    )
    assert dt2 is not None
    assert src2 == "evidence.baseline_window_end"
