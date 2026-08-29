from __future__ import annotations

import ast
import sys
from pathlib import Path
from random import Random

import pytest
import yaml

from octopus_shadow.degradation import degradation_ladder
from octopus_shadow.enforcement import Authority, EnforcementGuard
from octopus_shadow.generator import ChaosGenerator, GeneratorError, validate_destination
from octopus_shadow.ledger import LedgerError, PredictionLedger, SyntheticLedger
from octopus_shadow.observe import ObserveError, parse_synthetic_observation
from octopus_shadow.policy import Wave0ObserveOnlyPolicy
from octopus_shadow.skill import calculate
from octopus_shadow.stress import may_update_production_skill, samples

sys.path.insert(0, "/opt/octopus/cognition/src")

WEIGHTS = [1.0, 1.2, 0.8, 2.0]
SRC = Path(__file__).resolve().parents[1] / "src" / "octopus_shadow"


def test_ledger(tmp_path: Path) -> None:
    ledger = PredictionLedger(tmp_path / "predictions.db")
    pid = ledger.prediction(
        {
            "domain": "stability",
            "state": [0.1, 0.2, 0.05, 0.5],
            "action": "NO_ACTION",
            "mean": [0.1, 0.2, 0.05, 0.5],
            "baseline": [0.1, 0.2, 0.05, 0.5],
            "model_version": "persistence-v1",
        }
    )
    ledger.outcome(pid, {"actual": [0.11, 0.21, 0.05, 0.5], "usable": True})
    valid, broken = ledger.verify()
    assert valid is True
    assert broken is None
    with pytest.raises(LedgerError, match="duplicate_outcome"):
        ledger.outcome(pid, {"actual": [0.0, 0.0, 0.0, 0.0], "usable": True})
    with pytest.raises(LedgerError, match="outcome_without_prediction"):
        ledger.outcome("pred-missing", {"actual": [0.0, 0.0, 0.0, 0.0], "usable": True})
    with pytest.raises(LedgerError, match="duplicate_prediction"):
        ledger.prediction({"prediction_id": pid, "domain": "stability"})
    ledger.database.execute("UPDATE events SET body='{}' WHERE seq=1")
    ledger.database.commit()
    valid, broken = ledger.verify()
    assert valid is False
    assert broken == 1


def test_outcome_not_after_prediction(tmp_path: Path) -> None:
    ledger = PredictionLedger(tmp_path / "order.db")
    pid = ledger.prediction({"domain": "stability"}, created_ns=1000)
    with pytest.raises(LedgerError, match="outcome_not_after_prediction"):
        ledger.outcome(pid, {"actual": [0.0], "usable": False}, created_ns=1000)
    with pytest.raises(LedgerError, match="outcome_not_after_prediction"):
        ledger.outcome(pid, {"actual": [0.0], "usable": False}, created_ns=999)
    ledger.outcome(pid, {"actual": [0.0], "usable": False}, created_ns=1001)


def test_predictions_are_never_updated() -> None:
    source = (SRC / "ledger.py").read_text(encoding="utf-8")
    assert "UPDATE events" not in source
    assert not hasattr(PredictionLedger, "update_prediction")
    assert not hasattr(PredictionLedger, "update")


def test_synthetic_database_cannot_open_runtime_path(tmp_path: Path) -> None:
    runtime = tmp_path / "runtime" / "predictions.db"
    runtime.parent.mkdir()
    with pytest.raises(LedgerError, match="synthetic_database_cannot_open_runtime_path"):
        SyntheticLedger(runtime)
    with pytest.raises(LedgerError, match="synthetic_database_cannot_open_runtime_path"):
        SyntheticLedger("/var/lib/octopus/state/world_model/predictions.db")
    chaos = SyntheticLedger(tmp_path / "chaos" / "predictions.db")
    assert chaos.namespace == "chaos"
    chaos.close()


def _walk(n: int = 60) -> tuple[list, list, list]:
    rng = Random(7)
    state = [0.20, 0.18, 0.05, 0.50]
    model: list[list[float]] = []
    baseline: list[list[float]] = []
    actual: list[list[float]] = []
    for _ in range(n):
        nxt = [min(1.0, max(0.0, value + rng.gauss(0.0, 0.03))) for value in state]
        baseline.append(list(state))
        actual.append(list(nxt))
        model.append(list(nxt))
        state = nxt
    return model, baseline, actual


def test_skill() -> None:
    model, baseline, actual = _walk()
    report = calculate(model, baseline, actual, WEIGHTS, min_samples=50, bootstrap=400, seed=42)
    assert report.samples >= 50
    assert report.score is not None and report.score > 0.5
    assert report.lower is not None and report.lower > 0.0
    assert report.eligible is True


def test_wave0() -> None:
    policy = Wave0ObserveOnlyPolicy()
    decision = policy.decide(
        {"compute_pressure": 0.9},
        {"recommendation": "ADVISORY_RESTART", "executable": True},
    )
    assert decision.recommendation == "NO_ACTION"
    assert decision.executable is False
    assert decision.authority == "NONE"
    assert decision.profile == "WAVE0_OBSERVE_ONLY"


def test_every_shadow_result_non_executable() -> None:
    policy = Wave0ObserveOnlyPolicy()
    guard = EnforcementGuard()
    authority = Authority(
        profile="WAVE0_OBSERVE_ONLY",
        execute_enabled=True,
        registry_signature_valid=True,
        verifier_ready=True,
        gates_failed=(),
        owner_approval=True,
        skill_lower_bound=0.9,
    )
    for action in ("ADVISORY_RESTART", "ADVISORY_THROTTLE", "NO_ACTION"):
        ok, _ = guard.authorize(action, authority)
        assert ok is False
        decision = policy.decide({}, {"recommendation": action, "executable": True})
        assert decision.executable is False


def test_guard() -> None:
    guard = EnforcementGuard()
    wave0 = Authority(
        profile="WAVE0_OBSERVE_ONLY",
        execute_enabled=True,
        registry_signature_valid=True,
        verifier_ready=True,
        gates_failed=(),
        owner_approval=True,
        skill_lower_bound=0.4,
    )
    ok, reason = guard.authorize("ADVISORY_THROTTLE", wave0)
    assert ok is False
    assert reason == "denied_observe_only"
    ok, _ = guard.authorize("NO_ACTION", wave0)
    assert ok is False
    flipped = Authority(
        profile="WAVE1",
        execute_enabled=True,
        registry_signature_valid=True,
        verifier_ready=True,
        gates_failed=(),
        owner_approval=False,
        skill_lower_bound=0.4,
    )
    ok, reason = guard.authorize("NO_ACTION", flipped)
    assert ok is False
    assert reason == "owner_approval_missing"


def test_synthetic() -> None:
    production: list[dict] = []
    chaos: list[dict] = []
    for scenario in ("energy_depletion", "error_burst", "model_degradation"):
        for observation in samples(scenario, count=20):
            assert observation["synthetic"] is True
            assert observation["source"] == "shadow-chaos"
            chaos.append(observation)
            if not may_update_production_skill(observation):
                continue
            production.append(observation)
    assert len(chaos) == 60
    assert production == []


def test_synthetic_never_updates_production_skill() -> None:
    sys_path_skill = pytest.importorskip("octopus_cognition.metacontrol.skill")
    tracker = sys_path_skill.DomainSkillTracker(minimum=50)
    for observation in samples("energy_depletion", count=60):
        assert may_update_production_skill(observation) is False
        if may_update_production_skill(observation):
            tracker.record(0.001, 0.01)
    assert tracker.report().samples == 0
    assert tracker.report().score is None


def test_ladder() -> None:
    _, baseline, actual = _walk(60)
    scores: list[float] = []
    for level in degradation_ladder(actual, seed=3):
        report = calculate(
            level["prediction"],
            baseline,
            actual,
            WEIGHTS,
            min_samples=50,
            bootstrap=200,
            seed=3,
        )
        assert report.score is not None
        scores.append(report.score)
    assert all(left >= right - 1e-9 for left, right in zip(scores, scores[1:]))
    assert scores[0] > scores[-1]


def test_board_config_matches_wave0() -> None:
    path = Path("/etc/octopus/world-model.yaml")
    if not path.is_file():
        path = Path(__file__).resolve().parents[1] / "config" / "world-model.yaml"
    config = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert config["profile"] == "WAVE0_OBSERVE_ONLY"
    assert config["execute_enabled"] is False
    assert len(config["state_names"]) == len(config["homeostatic_weights"])
    assert config["runtime"]["torch_threads"] <= 2
    assert config.get("torch_enabled") is False


def test_observe_extra_forbid_is_422() -> None:
    with pytest.raises(ObserveError) as exc:
        parse_synthetic_observation(
            {
                "synthetic": True,
                "scenario": "energy_depletion",
                "shell": "rm -rf /",
            }
        )
    assert exc.value.status_code == 422
    assert exc.value.message == "extra_forbidden"
    parsed = parse_synthetic_observation(
        {"synthetic": True, "scenario": "energy_depletion", "source": "shadow-chaos"}
    )
    assert parsed["executable"] is False
    assert parsed["action"] == "NONE"


def test_generator_rejects_lookalike_hostname() -> None:
    with pytest.raises(GeneratorError, match="lookalike_hostname_rejected"):
        validate_destination("http://localhost.evil.com:8080/v1/observe/synthetic")
    with pytest.raises(GeneratorError, match="lookalike_hostname_rejected"):
        validate_destination("http://127.0.0.1.attacker.com:8080/v1/observe/synthetic")
    with pytest.raises(GeneratorError, match="query_or_fragment_forbidden"):
        validate_destination("http://127.0.0.1:8080/v1/observe/synthetic?x=1")
    with pytest.raises(GeneratorError, match="path_must_be_observe_synthetic"):
        validate_destination("http://127.0.0.1:8080/v1/work")
    assert validate_destination("http://127.0.0.1:8080/v1/observe/synthetic")


def test_generator_has_no_execution_imports() -> None:
    banned = {"subprocess", "psutil", "docker", "paramiko"}
    tree = ast.parse((SRC / "generator.py").read_text(encoding="utf-8"))
    found: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if any(token in alias.name for token in banned):
                    found.append(alias.name)
        elif isinstance(node, ast.ImportFrom) and node.module:
            if any(token in node.module for token in banned):
                found.append(node.module)
    assert found == []
    source = (SRC / "generator.py").read_text(encoding="utf-8")
    assert "os.system" not in source
    assert "subprocess" not in source


def test_wave0_class_has_no_enforcement_switch() -> None:
    sys = pytest.importorskip("octopus_cognition.metacontrol.gate")
    import inspect

    params = [name for name in inspect.signature(sys.Wave0MetacontrolGate.__init__).parameters if name != "self"]
    assert params == []
    source = inspect.getsource(sys.Wave0MetacontrolGate)
    assert "shadow=False" not in source


def test_would_block_survives_for_dashboard() -> None:
    gate_mod = pytest.importorskip("octopus_cognition.metacontrol.gate")
    models = pytest.importorskip("octopus_cognition.homeostasis.models")
    skill_mod = pytest.importorskip("octopus_cognition.metacontrol.skill")
    gate = gate_mod.Wave0MetacontrolGate()
    report = skill_mod.SkillReport(
        score=0.4,
        lower_bound=0.25,
        samples=80,
        eligible=True,
        reason="skill_confirmed",
        calibration_error=0.05,
    )
    result = gate.evaluate(report, mode=models.HomeostaticMode.WOULD_LOCKDOWN, energy_ratio=0.8, evidence_age_s=4.0, calibration_error=0.05)
    assert result.would_decide.value == "block"
    assert result.executable is False
    enforced = gate.enforced(report, mode=models.HomeostaticMode.WOULD_LOCKDOWN, energy_ratio=0.8, evidence_age_s=4.0, calibration_error=0.05)
    assert enforced.would_decide.value == "block"
    assert enforced.reason == "shadow_would_block:homeostatic_would_lockdown"
    assert enforced.executable is False


def test_evaluate_shadow_exit_does_not_arm() -> None:
    script = Path(__file__).resolve().parents[1] / "scripts" / "evaluate_shadow_exit.py"
    source = script.read_text(encoding="utf-8")
    assert "execute_enabled=True" not in source
    assert "shadow=False" not in source
    assert "ARMED.json" not in source
    assert "execute_enabled" in source  # reports the live false value, does not flip it


def test_service_does_not_import_http_app() -> None:
    source = (SRC / "service.py").read_text(encoding="utf-8")
    assert "http_app" not in source
    assert "uvicorn" not in source
    assert "ChaosGenerator" not in source
