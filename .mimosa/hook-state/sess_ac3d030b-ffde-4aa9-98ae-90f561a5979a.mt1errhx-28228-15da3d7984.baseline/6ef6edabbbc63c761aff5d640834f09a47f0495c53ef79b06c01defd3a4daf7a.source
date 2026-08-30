#!/usr/bin/env python3
"""structured_schemas.py — Typed schemas for plan/hypothesis/evidence/proposal (EQUIP G10).

All cognition components agree on these schemas. Typed, validated, no secrets.
Planner != Executor != Verifier — each has its own output schema.

Invariant: no schema field carries policy/goal/identity authority.
Every schema has: schema_version, id, ts, producer, trace_id.
"""
from __future__ import annotations

import time
import uuid
from enum import Enum
from typing import Any


SCHEMA_VERSION = "cognition-schemas.v1"


def _now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _id(prefix: str = "id") -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


def _trace() -> str:
    return f"trace_{uuid.uuid4().hex[:12]}"


# ── Task Classes ──────────────────────────────────────────────────────────────

class TaskClass(str, Enum):
    """Task classification for routing."""
    CODING = "coding"
    RETRIEVAL = "retrieval"
    CAUSAL_ANALYSIS = "causal_analysis"
    CLASSIFICATION = "classification"
    SUMMARIZATION = "summarization"
    RESEARCH = "research"
    ORCHESTRATION = "orchestration"
    PLANNING = "planning"
    UNKNOWN = "unknown"


class PrivacyLevel(str, Enum):
    """Privacy level for routing decisions."""
    PUBLIC = "public"
    INTERNAL = "internal"
    SENSITIVE = "sensitive"
    PRIVATE = "private"


class RoutingDecision(str, Enum):
    """Routing tier decision."""
    LOCAL = "local"
    SECONDARY = "secondary"
    PRIMARY = "primary"
    REJECTED = "rejected"


class ClaimStrength(str, Enum):
    """Strength of a causal or predictive claim."""
    CORRELATION = "correlation"
    PREDICTION = "prediction"
    CAUSAL = "causal"  # ADR-013 REJECTED — causal claims are never authority
    SPECULATIVE = "speculative"


# ── Structured Output Schemas ──────────────────────────────────────────────────

class StructuredOutput:
    """Base class for all structured cognition outputs."""

    schema_version: str = SCHEMA_VERSION

    @staticmethod
    def base(producer: str = "system", trace_id: str | None = None) -> dict[str, Any]:
        return {
            "schema_version": SCHEMA_VERSION,
            "id": _id(),
            "trace_id": trace_id or _trace(),
            "ts": _now(),
            "producer": producer,
        }


def make_plan(
    *,
    task_class: str | TaskClass = TaskClass.UNKNOWN,
    description: str = "",
    steps: list[dict[str, Any]] | None = None,
    estimated_cost_usd: float = 0.0,
    estimated_latency_ms: int = 0,
    risk_level: str = "low",
    routing: str | RoutingDecision = RoutingDecision.LOCAL,
    producer: str = "planner",
    trace_id: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Create a structured plan output (planner role).

    Steps are ordered, typed dicts with {description, action_type, target, risk}.
    Plan is proposal-only — does not authorize execution.
    """
    base = StructuredOutput.base(producer, trace_id)
    return {
        **base,
        "output_type": "plan",
        "task_class": str(task_class),
        "description": str(description)[:500],
        "steps": steps or [],
        "estimated_cost_usd": float(estimated_cost_usd),
        "estimated_latency_ms": int(estimated_latency_ms),
        "risk_level": str(risk_level),
        "routing": str(routing),
        "may_execute": False,  # planner != executor
        "metadata": metadata or {},
    }


def make_hypothesis(
    *,
    statement: str = "",
    claim_strength: str | ClaimStrength = ClaimStrength.SPECULATIVE,
    evidence_level: str = "E",  # A=strongest .. E=weakest
    falsification_condition: str = "",
    confidence: float = 0.0,
    producer: str = "hypothesis_engine",
    trace_id: str | None = None,
) -> dict[str, Any]:
    """Create a structured hypothesis output.

    Every hypothesis has a falsification condition and evidence level.
    ADR-013: causal claims are never treated as authority.
    """
    base = StructuredOutput.base(producer, trace_id)
    return {
        **base,
        "output_type": "hypothesis",
        "statement": str(statement)[:1000],
        "claim_strength": str(claim_strength.value if hasattr(claim_strength, "value") else claim_strength),
        "evidence_level": str(evidence_level),
        "falsification_condition": str(falsification_condition)[:500],
        "confidence": float(max(0.0, min(1.0, confidence))),
        "is_authority": False,  # hypothesis never governs policy
    }


def make_evidence(
    *,
    claim_id: str = "",
    observation: str = "",
    evidence_grade: str = "E",
    source_type: str = "probe",  # probe, test, runtime, owner
    source_ref: str = "",
    producer: str = "verifier",
    trace_id: str | None = None,
) -> dict[str, Any]:
    """Create a structured evidence record.

    Evidence grades: A (strongest) to E (weakest).
    Source types: probe (best), test, runtime, owner.
    """
    base = StructuredOutput.base(producer, trace_id)
    return {
        **base,
        "output_type": "evidence",
        "claim_id": str(claim_id),
        "observation": str(observation)[:500],
        "evidence_grade": str(evidence_grade),
        "source_type": str(source_type),
        "source_ref": str(source_ref)[:200],
    }


def make_proposal(
    *,
    action_type: str = "",
    description: str = "",
    target: str = "",
    approval_policy: str = "owner_required",  # owner_required, auto, propose
    confidence: float = 0.0,
    rollback_plan: str = "",
    producer: str = "executor",
    trace_id: str | None = None,
) -> dict[str, Any]:
    """Create a structured proposal output (executor role).

    Proposal-only — does not self-approve. Approval policy determines
    whether owner gate is needed.
    """
    base = StructuredOutput.base(producer, trace_id)
    return {
        **base,
        "output_type": "proposal",
        "action_type": str(action_type)[:100],
        "description": str(description)[:500],
        "target": str(target)[:200],
        "approval_policy": str(approval_policy),
        "confidence": float(max(0.0, min(1.0, confidence))),
        "rollback_plan": str(rollback_plan)[:500],
        "self_approved": False,  # executor != authorizer
    }


def make_verification_result(
    *,
    target_id: str = "",
    verdict: str = "UNVERIFIED",  # VERIFIED, REJECTED, INCONCLUSIVE, CONTAMINATED
    findings: list[str] | None = None,
    contamination_detected: bool = False,
    producer: str = "verifier",
    trace_id: str | None = None,
) -> dict[str, Any]:
    """Create a structured verification result (verifier role).

    Verifier must not use executor's context directly (MEA guard).
    contamination_detected = True means verifier context was tainted.
    """
    base = StructuredOutput.base(producer, trace_id)
    return {
        **base,
        "output_type": "verification_result",
        "target_id": str(target_id),
        "verdict": str(verdict),
        "findings": findings or [],
        "contamination_detected": bool(contamination_detected),
        "authority_level": "advisory",  # verifier is advisory, not authority
    }


def validate_structured_output(data: dict[str, Any]) -> dict[str, Any]:
    """Validate a structured output has required fields.

    Returns {valid: bool, errors: list[str]}.
    """
    errors: list[str] = []
    if not isinstance(data, dict):
        return {"valid": False, "errors": ["not_a_dict"]}

    required = ("schema_version", "id", "ts", "output_type")
    for f in required:
        if f not in data:
            errors.append(f"missing_{f}")

    # Validate confidence range if present
    if "confidence" in data:
        try:
            c = float(data["confidence"])
            if not (0.0 <= c <= 1.0):
                errors.append("confidence_out_of_range")
        except (TypeError, ValueError):
            errors.append("confidence_not_numeric")

    # Validate evidence grade if present
    valid_grades = ("A", "B", "C", "D", "E")
    if "evidence_grade" in data and str(data["evidence_grade"]) not in valid_grades:
        errors.append("invalid_evidence_grade")

    return {"valid": len(errors) == 0, "errors": errors}
