from __future__ import annotations

import inspect

import pytest

from octopus_cognition.homeostasis.models import HomeostaticMode
from octopus_cognition.metacontrol.gate import (
    ActionKind,
    EnforcedKind,
    ExecutedKind,
    Wave0MetacontrolGate,
    WouldDecide,
    evaluate_planning,
)
from octopus_cognition.metacontrol.skill import SkillReport


def _report(**kwargs) -> SkillReport:
    base = dict(
        score=None,
        lower_bound=None,
        samples=0,
        eligible=False,
        reason="insufficient_samples",
        calibration_error=None,
    )
    base.update(kwargs)
    return SkillReport(**base)


def test_wave0_denies_before_fifty_outcomes():
    decision = evaluate_planning(
        _report(),
        energy_ratio=0.9,
        evidence_age_s=4.0,
        calibration_error=None,
        readiness_profile="WAVE0_OBSERVE_ONLY",
    )
    assert decision.recommendation == "DENY"
    assert decision.executable is False
    assert decision.reason == "insufficient_skill_evidence"


def test_positive_skill_still_not_executable_in_wave0():
    decision = evaluate_planning(
        _report(
            score=0.4,
            lower_bound=0.25,
            samples=80,
            eligible=True,
            reason="skill_confirmed",
            calibration_error=0.05,
        ),
        energy_ratio=0.8,
        evidence_age_s=5.0,
        calibration_error=0.05,
        readiness_profile="WAVE0_OBSERVE_ONLY",
    )
    assert decision.recommendation == "PLAN_RECOMMENDED"
    assert decision.executable is False
    assert decision.reason == "denied_observe_only"
    assert decision.depth == 4


def test_stale_evidence_denies():
    decision = evaluate_planning(
        _report(samples=80, eligible=True, reason="skill_confirmed"),
        energy_ratio=0.8,
        evidence_age_s=45.0,
        calibration_error=0.05,
        readiness_profile="WAVE0_OBSERVE_ONLY",
    )
    assert decision.reason == "stale_evidence"
    assert decision.executable is False


def test_would_block_survives_for_dashboard():
    gate = Wave0MetacontrolGate()
    skilled = _report(
        score=0.8,
        lower_bound=0.6,
        samples=80,
        eligible=True,
        reason="skill_confirmed",
        calibration_error=0.04,
    )
    advisory = gate.advisory(
        skilled,
        mode=HomeostaticMode.WOULD_LOCKDOWN,
        energy_ratio=0.9,
        evidence_age_s=4.0,
        calibration_error=0.04,
    )
    assert advisory.would_decide is WouldDecide.BLOCK
    assert advisory.would_reason == "homeostatic_would_lockdown"
    assert advisory.executed is ExecutedKind.NONE
    assert advisory.executable is False
    assert advisory.action is ActionKind.NONE
    enforced = gate.enforced(
        skilled,
        mode=HomeostaticMode.WOULD_LOCKDOWN,
        energy_ratio=0.9,
        evidence_age_s=4.0,
        calibration_error=0.04,
    )
    assert enforced.would_decide is WouldDecide.BLOCK
    assert enforced.kind is EnforcedKind.REFLEX
    assert enforced.executable is False
    assert enforced.action is ActionKind.NONE
    assert enforced.executed is ExecutedKind.NONE
    assert enforced.reason == "shadow_would_block:homeostatic_would_lockdown"
    mapped = gate.evaluate(skilled, mode="protect", energy_ratio=0.9, evidence_age_s=4.0, calibration_error=0.04)
    assert mapped.would_decide is WouldDecide.BLOCK


def test_wave0_class_has_no_enforcement_switch():
    params = [name for name in inspect.signature(Wave0MetacontrolGate.__init__).parameters if name != "self"]
    assert params == []
    source = inspect.getsource(Wave0MetacontrolGate)
    assert "shadow=False" not in source
    assert "enforce=True" not in source
    assert "execute=True" not in source
    with pytest.raises(TypeError):
        Wave0MetacontrolGate(shadow=False)  # type: ignore[call-arg]
    gate = Wave0MetacontrolGate()
    with pytest.raises(TypeError, match="wave0_gate_has_no_enforcement_switch"):
        gate.enforced(_report(), shadow=False)
    with pytest.raises(TypeError, match="wave0_gate_has_no_enforcement_switch"):
        gate.advisory(_report(), execute=True)
    result = gate.enforced(_report(), mode=HomeostaticMode.NORMAL, energy_ratio=0.9, evidence_age_s=1.0)
    assert result.executable is False
    assert result.action is ActionKind.NONE
    assert result.kind is EnforcedKind.REFLEX
