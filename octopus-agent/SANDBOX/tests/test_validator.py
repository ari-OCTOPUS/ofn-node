"""P3 validator tests — every hard_rejections rule must fire, and exactly one
well-formed manifest (the real batching experiment) must be accepted.
Run from the SANDBOX root: /opt/octopus/venv/bin/pytest tests/ -q
Also runnable standalone: /opt/octopus/venv/bin/python tests/test_validator.py
"""
from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

SANDBOX = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SANDBOX))
from validate_manifest import validate  # noqa: E402

import hashlib  # noqa: E402

FIXTURE = "FIXTURES/tainted.jsonl"
FIXTURE_SHA = hashlib.sha256((SANDBOX.parent / FIXTURE).read_bytes()).hexdigest()
CODE = "/opt/octopus/current/src/octopus_sensorium/evidence/store.py"
CODE_SHA = hashlib.sha256(Path(CODE).read_bytes()).hexdigest()


def base_manifest() -> dict:
    return {
        "experiment_id": "exp-test-valid-0001",
        "created_at": "2026-08-17T11:00:00Z",
        "authorization_ref": "OWNER-DECISIONS.md D2",
        "hypothesis": "batching index writes reduces disk writes with zero drift",
        "fixture": {"file": FIXTURE, "sha256": FIXTURE_SHA, "records": 2000},
        "code_under_test": {"source_path": CODE, "sha256": CODE_SHA,
                            "integrity_anchor": "release SHA256SUMS"},
        "modes": {
            "baseline": {"env": {"OCTOPUS_INDEX_FLUSH_EVERY": 1}, "note": "old behavior"},
            "candidate": {"env": {"OCTOPUS_INDEX_FLUSH_EVERY": 200,
                                  "OCTOPUS_INDEX_FLUSH_MAX_AGE": 300.0}, "note": "deployed"},
        },
        "frozen_criteria": {
            "index_content_equal": True, "event_count_equal": True,
            "event_order_equal": True, "schema_equal": True,
            "write_reduction_min_percent": 80, "errors_zero": True},
        "runs_required": 3,
        "limits": {"cpu_s": 300, "as_mb": 1536, "fsize_mb": 512, "wall_s": 600},
        "network": "denied",
        "rollback": "delete sandbox outputs; production untouched",
        "may_authorize": False,
    }


def run_case(tmp_path: Path, manifest: dict, expect_rule: str) -> None:
    f = tmp_path / "m.json"
    f.write_text(json.dumps(manifest))
    ok, errors = validate(str(f))
    assert not ok, f"expected rejection {expect_rule}, got ACCEPT"
    assert any(e.startswith(expect_rule) for e in errors), f"{expect_rule} not in {errors}"


def test_positive_base_manifest_accepted(tmp_path):
    f = tmp_path / "ok.json"
    f.write_text(json.dumps(base_manifest()))
    ok, errors = validate(str(f))
    assert ok, errors


def test_r01_bad_experiment_id(tmp_path):
    m = base_manifest(); m["experiment_id"] = "Not A Valid Id"
    run_case(tmp_path, m, "R01")


def test_r02_bad_created_at(tmp_path):
    m = base_manifest(); m["created_at"] = "2026-08-17 11:00:00"
    run_case(tmp_path, m, "R02")


def test_r03_missing_authorization(tmp_path):
    m = base_manifest(); m.pop("authorization_ref")
    run_case(tmp_path, m, "R03")


def test_r04_empty_hypothesis(tmp_path):
    m = base_manifest(); m["hypothesis"] = "   "
    run_case(tmp_path, m, "R04")


def test_r05_fixture_outside_agent(tmp_path):
    m = base_manifest(); m["fixture"]["file"] = "/etc/passwd"
    run_case(tmp_path, m, "R05")


def test_r06_fixture_hash_mismatch(tmp_path):
    m = base_manifest(); m["fixture"]["sha256"] = "0" * 64
    run_case(tmp_path, m, "R06")


def test_r07_records_zero(tmp_path):
    m = base_manifest(); m["fixture"]["records"] = 0
    run_case(tmp_path, m, "R07")


def test_r08_missing_sidecar(tmp_path):
    m = base_manifest(); m["fixture"]["file"] = "FIXTURES/fixture-manifest.json"
    m["fixture"]["sha256"] = hashlib.sha256(
        (SANDBOX.parent / "FIXTURES/fixture-manifest.json").read_bytes()).hexdigest()
    run_case(tmp_path, m, "R08")


def test_r09_code_outside_opt(tmp_path):
    m = base_manifest(); m["code_under_test"]["source_path"] = "/tmp/store.py"
    run_case(tmp_path, m, "R09")


def test_r10_code_hash_mismatch(tmp_path):
    m = base_manifest(); m["code_under_test"]["sha256"] = "a" * 64
    run_case(tmp_path, m, "R10")


def test_r11_modes_incomplete(tmp_path):
    m = base_manifest(); m["modes"]["candidate"]["env"].pop("OCTOPUS_INDEX_FLUSH_EVERY")
    run_case(tmp_path, m, "R11")


def test_r12_criteria_incomplete(tmp_path):
    m = base_manifest(); m["frozen_criteria"].pop("schema_equal")
    run_case(tmp_path, m, "R12")


def test_r13_criteria_flag_false(tmp_path):
    m = base_manifest(); m["frozen_criteria"]["event_order_equal"] = False
    run_case(tmp_path, m, "R13")


def test_r14_reduction_out_of_range(tmp_path):
    m = base_manifest(); m["frozen_criteria"]["write_reduction_min_percent"] = 130
    run_case(tmp_path, m, "R14")


def test_r15_runs_below_floor(tmp_path):
    m = base_manifest(); m["runs_required"] = 2
    run_case(tmp_path, m, "R15")


def test_r16_limits_below_floor(tmp_path):
    m = base_manifest(); m["limits"]["as_mb"] = 8
    run_case(tmp_path, m, "R16")


def test_r17_network_allowed(tmp_path):
    m = base_manifest(); m["network"] = "allowed"
    run_case(tmp_path, m, "R17")


def test_r18_rollback_empty(tmp_path):
    m = base_manifest(); m["rollback"] = ""
    run_case(tmp_path, m, "R18")


def test_r19_may_authorize_true(tmp_path):
    m = base_manifest(); m["may_authorize"] = True
    run_case(tmp_path, m, "R19")


def test_r20_malformed_json(tmp_path):
    f = tmp_path / "broken.json"
    f.write_text("{not json")
    ok, errors = validate(str(f))
    assert not ok and any(e.startswith("R20") for e in errors)


def test_real_experiment_manifest_accepted():
    real = SANDBOX / "experiments" / "batching-index-writes.v1.json"
    if real.is_file():
        ok, errors = validate(str(real))
        assert ok, errors


if __name__ == "__main__":
    import tempfile
    failures = 0
    with tempfile.TemporaryDirectory() as td:
        tp = Path(td)
        for name, fn in sorted(globals().items()):
            if name.startswith("test_"):
                try:
                    fn(tp) if "tmp_path" in fn.__code__.co_varnames else fn()
                    print(f"PASS {name}")
                except AssertionError as exc:
                    failures += 1
                    print(f"FAIL {name}: {exc}")
    print("failures:", failures)
    sys.exit(1 if failures else 0)
