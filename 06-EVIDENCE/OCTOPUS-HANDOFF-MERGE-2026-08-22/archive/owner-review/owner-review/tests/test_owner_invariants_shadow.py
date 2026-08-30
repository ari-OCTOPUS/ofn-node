"""Shadow-package coverage of owner invariants INV-04, INV-06, INV-07, INV-09."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from octopus_shadow.enforcement import Authority, EnforcementGuard
from octopus_shadow.ledger import LedgerError, PredictionLedger
from octopus_shadow.policy import Wave0ObserveOnlyPolicy
from octopus_shadow.stress import samples

import sys

sys.path.insert(0, "/opt/octopus/cognition/src")
from octopus_cognition.owner_authorization import outcome_timestamp_ok  # noqa: E402


def test_inv04_outcome_without_prediction_rejected(tmp_path: Path) -> None:
    ledger = PredictionLedger(tmp_path / "predictions.db")
    with pytest.raises(LedgerError, match="outcome_without_prediction"):
        ledger.outcome("pred-missing", {"actual": [0.0, 0.0, 0.0, 0.0], "usable": True})


def test_inv05_spec_stale_timestamp_and_duplicate(tmp_path: Path) -> None:
    ledger = PredictionLedger(tmp_path / "predictions.db")
    pid = ledger.prediction(
        {
            "domain": "stability",
            "state": [0.1, 0.2, 0.05, 0.5],
            "action": "NO_ACTION",
            "mean": [0.1, 0.2, 0.05, 0.5],
            "baseline": [0.1, 0.2, 0.05, 0.5],
            "model_version": "persistence-v1",
            "issued_at_ns": 1000,
        }
    )
    ok, reason = outcome_timestamp_ok(1000, 500)
    assert ok is False
    assert reason == "outcome_timestamp_before_prediction"
    ledger.outcome(pid, {"actual": [0.11, 0.21, 0.05, 0.5], "usable": True, "resolved_at_ns": 2000})
    with pytest.raises(LedgerError, match="duplicate_outcome"):
        ledger.outcome(pid, {"actual": [0.0, 0.0, 0.0, 0.0], "usable": True})


def test_inv06_duplicate_outcome_rejected(tmp_path: Path) -> None:
    ledger = PredictionLedger(tmp_path / "predictions.db")
    pid = ledger.prediction({"domain": "stability", "state": [0.1], "mean": [0.1], "baseline": [0.1]})
    ledger.outcome(pid, {"actual": [0.1], "usable": True})
    with pytest.raises(LedgerError, match="duplicate_outcome"):
        ledger.outcome(pid, {"actual": [0.2], "usable": True})


def test_inv07_shadow_tampered_chain_fails(tmp_path: Path) -> None:
    ledger = PredictionLedger(tmp_path / "predictions.db")
    ledger.prediction({"domain": "stability", "state": [0.1], "mean": [0.1], "baseline": [0.1]})
    valid, broken = ledger.verify()
    assert valid is True
    assert broken is None
    ledger.database.execute("UPDATE events SET body='{}' WHERE seq=1")
    ledger.database.commit()
    valid, broken = ledger.verify()
    assert valid is False
    assert broken == 1


def test_inv09_synthetic_samples_do_not_enter_live_skill() -> None:
    live = json.loads(Path("/var/lib/octopus/state/skill/latest.json").read_text(encoding="utf-8"))
    assert live.get("domain") == "sensorium_health"
    assert "shadow-chaos" not in json.dumps(live)
    production: list[dict] = []
    for scenario in ("energy_depletion", "error_burst", "model_degradation"):
        for observation in samples(scenario, count=5):
            assert observation["synthetic"] is True
            assert observation["source"] == "shadow-chaos"
            if not observation["synthetic"]:
                production.append(observation)
    assert production == []
    window = Path("/var/lib/octopus/state/skill/window.json")
    if window.is_file():
        blob = window.read_text(encoding="utf-8")
        assert "shadow-chaos" not in blob
        assert "synthetic" not in blob


def test_inv13_and_inv14_shadow_policy_wave0() -> None:
    policy = Wave0ObserveOnlyPolicy()
    decision = policy.decide({"compute_pressure": 0.9}, {"recommendation": "PLAN_ALLOWED_ADVISORY", "executable": True})
    assert decision.executable is False
    assert decision.recommendation == "NO_ACTION"
    assert decision.authority == "NONE"
    ok, reason = EnforcementGuard().authorize(
        "ADVISORY_THROTTLE",
        Authority(
            profile="WAVE0_OBSERVE_ONLY",
            execute_enabled=True,
            registry_signature_valid=True,
            verifier_ready=True,
            gates_failed=(),
            owner_approval=True,
            skill_lower_bound=0.4,
        ),
    )
    assert ok is False
    assert reason == "denied_observe_only"
