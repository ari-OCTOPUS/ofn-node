"""Atomic Doctor checks. Missing evidence is UNKNOWN, never PASS."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


SEVERITIES = ("blocking", "degrading", "informational")


@dataclass
class DoctorCheck:
    check_id: str
    category: str
    severity: str
    observed: Any
    expected: Any
    evidence_path: str | None
    read_only: bool = True
    passed: bool = False
    remediation_owner: str = "owner"
    remediation_type: str = "none"
    source_command: str | None = None
    source_digest: str | None = None
    reason: str | None = None
    extra: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.severity not in SEVERITIES:
            raise ValueError(f"invalid severity: {self.severity}")

    def as_v1(self) -> dict[str, Any]:
        return {
            "schema": "octopus.doctor-check.v1",
            "check_id": self.check_id,
            "category": self.category,
            "severity": self.severity,
            "observed": self.observed,
            "expected": self.expected,
            "evidence_path": self.evidence_path,
            "read_only": self.read_only,
            "passed": self.passed,
            "remediation_owner": self.remediation_owner,
            "remediation_type": self.remediation_type,
            "source_command": self.source_command,
            "source_digest": self.source_digest,
            "reason": self.reason,
            **self.extra,
        }


def doctor_status(checks: list[DoctorCheck]) -> str:
    if any(c.severity == "blocking" and not c.passed for c in checks):
        return "FAIL"
    if any(c.severity == "degrading" and not c.passed for c in checks):
        return "DEGRADED"
    if any(c.evidence_path is None for c in checks):
        return "UNKNOWN"
    return "PASS"


def require_key(metrics: dict[str, Any], key: str) -> DoctorCheck | None:
    """Missing is not healthy. Never default a numeric metric to 0.0."""
    if key not in metrics:
        return DoctorCheck(
            check_id="missing_metric",
            category="sensing",
            severity="blocking",
            observed="MISSING",
            expected=key,
            evidence_path=None,
            passed=False,
            reason="missing_not_healthy",
        )
    return None
