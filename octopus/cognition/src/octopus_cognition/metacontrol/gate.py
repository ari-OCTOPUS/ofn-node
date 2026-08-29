from __future__ import annotations

from dataclasses import dataclass, replace
from enum import StrEnum

from octopus_cognition.homeostasis.models import HomeostaticMode, interpret_mode
from octopus_cognition.metacontrol.skill import SkillReport

WAVE0_PROFILE = "WAVE0_OBSERVE_ONLY"
_FORBIDDEN_SWITCHES = frozenset({"shadow", "enforce", "execute", "execute_enabled", "executable"})


class WouldDecide(StrEnum):
    PLAN = "plan"
    REFLEX = "reflex"
    BLOCK = "block"


class ActionKind(StrEnum):
    NONE = "NONE"


class ExecutedKind(StrEnum):
    NONE = "none"


class EnforcedKind(StrEnum):
    REFLEX = "reflex"


@dataclass(frozen=True)
class GateResult:
    would_decide: WouldDecide
    would_reason: str
    would_rollout_depth: int
    executed: ExecutedKind
    executable: bool
    action: ActionKind
    profile: str
    kind: EnforcedKind | None = None
    reason: str | None = None

    def to_dict(self) -> dict[str, object]:
        return {
            "would_decide": self.would_decide.value,
            "would_reason": self.would_reason,
            "would_rollout_depth": self.would_rollout_depth,
            "executed": self.executed.value,
            "executable": False,
            "action": self.action.value,
            "profile": self.profile,
            "kind": None if self.kind is None else self.kind.value,
            "reason": self.reason or self.would_reason,
        }


@dataclass(frozen=True)
class MetaDecision:
    recommendation: str
    depth: int
    executable: bool
    reason: str


def _reject_enforcement_kwargs(kwargs: dict) -> None:
    bad = _FORBIDDEN_SWITCHES.intersection(kwargs)
    if bad:
        raise TypeError("wave0_gate_has_no_enforcement_switch")


class Wave0MetacontrolGate:
    """WAVE0 observe-only gate. No shadow/enforce/execute constructor switch.

    advisory()/evaluate() expose hypothetical would_decide including BLOCK.
    enforced() always stays executable=False, action=NONE, kind=REFLEX.
    BLOCK never becomes host 503 / process stop.
    """

    PROFILE = WAVE0_PROFILE

    def __init__(self) -> None:
        return

    def evaluate(
        self,
        report: SkillReport,
        *,
        mode: HomeostaticMode | str = HomeostaticMode.NORMAL,
        energy_ratio: float = 1.0,
        evidence_age_s: float = 0.0,
        calibration_error: float | None = None,
        readiness_profile: str = WAVE0_PROFILE,
    ) -> GateResult:
        del readiness_profile
        homeostatic_mode = interpret_mode(mode)
        if homeostatic_mode == HomeostaticMode.WOULD_LOCKDOWN:
            return self._freeze(WouldDecide.BLOCK, "homeostatic_would_lockdown", 0)
        if homeostatic_mode == HomeostaticMode.CONSERVE:
            return self._freeze(WouldDecide.REFLEX, "energy_conservation", 0)

        if evidence_age_s > 30:
            return self._freeze(WouldDecide.REFLEX, "stale_evidence", 0)
        if report.samples < 50:
            return self._freeze(WouldDecide.REFLEX, "insufficient_skill_evidence", 0)
        if not report.eligible:
            return self._freeze(WouldDecide.REFLEX, report.reason, 0)
        if calibration_error is None:
            return self._freeze(WouldDecide.REFLEX, "calibration_unknown", 0)
        if calibration_error > 0.20:
            return self._freeze(WouldDecide.REFLEX, "poor_calibration", 0)
        if energy_ratio < 0.25:
            return self._freeze(WouldDecide.REFLEX, "homeostatic_budget", 0)
        if report.lower_bound is None:
            return self._freeze(WouldDecide.REFLEX, "insufficient_skill_evidence", 0)

        if report.lower_bound < 0.20:
            depth = 2
        elif report.lower_bound < 0.50:
            depth = 4
        else:
            depth = 6
        return self._freeze(WouldDecide.PLAN, "denied_observe_only", depth)

    def advisory(self, report: SkillReport, **kwargs) -> GateResult:
        _reject_enforcement_kwargs(kwargs)
        return self.evaluate(report, **kwargs)

    def enforced(self, report: SkillReport, **kwargs) -> GateResult:
        _reject_enforcement_kwargs(kwargs)
        result = self.evaluate(report, **kwargs)
        return replace(
            result,
            kind=EnforcedKind.REFLEX,
            executable=False,
            action=ActionKind.NONE,
            executed=ExecutedKind.NONE,
            reason=f"shadow_would_{result.would_decide.value}:{result.would_reason}",
        )

    @staticmethod
    def _freeze(decision: WouldDecide, reason: str, depth: int) -> GateResult:
        return GateResult(
            would_decide=decision,
            would_reason=reason,
            would_rollout_depth=depth,
            executed=ExecutedKind.NONE,
            executable=False,
            action=ActionKind.NONE,
            profile=WAVE0_PROFILE,
            kind=None,
            reason=reason,
        )


def evaluate_planning(
    report: SkillReport,
    energy_ratio: float,
    evidence_age_s: float,
    calibration_error: float | None,
    readiness_profile: str,
) -> MetaDecision:
    """Legacy advisory mapping used by existing WAVE0 tests. Never executes."""
    if evidence_age_s > 30:
        return MetaDecision("DENY", 0, False, "stale_evidence")

    if report.samples < 50:
        return MetaDecision("DENY", 0, False, "insufficient_skill_evidence")

    if not report.eligible:
        return MetaDecision("DENY", 0, False, report.reason)

    if calibration_error is None:
        return MetaDecision("DENY", 0, False, "calibration_unknown")

    if calibration_error > 0.20:
        return MetaDecision("DENY", 0, False, "poor_calibration")

    if energy_ratio < 0.25:
        return MetaDecision("DENY", 0, False, "homeostatic_budget")

    if report.lower_bound is None:
        return MetaDecision("DENY", 0, False, "insufficient_skill_evidence")

    if report.lower_bound < 0.20:
        depth = 2
    elif report.lower_bound < 0.50:
        depth = 4
    else:
        depth = 6

    if readiness_profile == WAVE0_PROFILE:
        return MetaDecision(
            recommendation="PLAN_RECOMMENDED",
            depth=depth,
            executable=False,
            reason="denied_observe_only",
        )

    return MetaDecision("PLAN_ALLOWED", depth, False, "denied_observe_only")
