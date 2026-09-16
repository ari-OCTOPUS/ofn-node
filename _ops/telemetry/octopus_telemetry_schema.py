#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""octopus_telemetry_schema.py -- Versioned telemetry schema for Octopus observability.

Defines span types, attribute conventions, and schema metadata for the unified
Octopus telemetry system. All spans emitted by Octopus components conform to
this schema.

Schema: OctopusTelemetry.v1

Span categories:
  - intent:    User intent detection and classification
  - policy:    Policy gate decisions (NBB-CP, MemoryGate, etc.)
  - memory:    Memory read/write operations (episodic, semantic, hypothesis)
  - model:     LLM model calls (router decision, token usage, cost)
  - tool:      Tool invocations (MCP tools, internal tools)
  - approval:  Human approval workflow steps
  - outcome:   Final task/workflow outcome and decision_reason

Namespace: octopus.* (Octopus-internal)
Note: gen_ai.* namespace is reserved for the OTel GenAI semantic conventions
(which are Development status as of v1.42.0). Octopus uses its own namespace
for memory/policy/tool spans.

No raw chain-of-thought logging. decision_reason is an audit-friendly summary,
never the full CoT.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

SCHEMA_VERSION = "OctopusTelemetry.v1"


class SpanKind(str, Enum):
    """Span kind matching OTel conventions (INTERNAL for most Octopus spans)."""
    INTERNAL = "INTERNAL"
    CLIENT = "CLIENT"
    SERVER = "SERVER"
    PRODUCER = "PRODUCER"
    CONSUMER = "CONSUMER"


class SpanStatus(str, Enum):
    """Standard span status."""
    OK = "ok"
    ERROR = "error"
    UNSET = "unset"


@dataclass(frozen=True)
class SpanType:
    """Definition of an Octopus span type."""
    name: str
    category: str
    description: str
    required_attrs: tuple[str, ...] = ()
    optional_attrs: tuple[str, ...] = ()


# Canonical Octopus span type definitions
SPAN_TYPES: dict[str, SpanType] = {
    "octopus.intent.detected": SpanType(
        name="octopus.intent.detected",
        category="intent",
        description="User intent detected and classified",
        required_attrs=("octopus.intent.type",),
        optional_attrs=("octopus.intent.confidence", "octopus.language"),
    ),
    "octopus.policy.check": SpanType(
        name="octopus.policy.check",
        category="policy",
        description="Policy gate decision (NBB-CP, MemoryGate, sandbox, etc.)",
        required_attrs=("octopus.policy.gate", "octopus.policy.verdict"),
        optional_attrs=("octopus.policy.reason", "octopus.policy.evidence_level"),
    ),
    "octopus.memory.read": SpanType(
        name="octopus.memory.read",
        category="memory",
        description="Memory read operation",
        required_attrs=("octopus.memory.store",),
        optional_attrs=(
            "octopus.memory.source", "octopus.memory.rows_returned",
            "octopus.memory.read_ok",
        ),
    ),
    "octopus.memory.write": SpanType(
        name="octopus.memory.write",
        category="memory",
        description="Memory write operation",
        required_attrs=("octopus.memory.store",),
        optional_attrs=(
            "octopus.memory.source_class", "octopus.memory.admission_state",
            "octopus.memory.quarantined",
        ),
    ),
    "octopus.memory.readback": SpanType(
        name="octopus.memory.readback",
        category="memory",
        description="Read-back verification after write",
        required_attrs=("octopus.memory.hypothesis_id",),
        optional_attrs=("octopus.memory.readback_ok",),
    ),
    "octopus.model.invoke": SpanType(
        name="octopus.model.invoke",
        category="model",
        description="LLM model invocation",
        required_attrs=("octopus.model.provider",),
        optional_attrs=(
            "octopus.model.tokens_in", "octopus.model.tokens_out",
            "octopus.model.cost_usd", "octopus.model.status",
        ),
    ),
    "octopus.tool.call": SpanType(
        name="octopus.tool.call",
        category="tool",
        description="Tool invocation (MCP or internal)",
        required_attrs=("octopus.tool.name",),
        optional_attrs=(
            "octopus.tool.result_status", "octopus.tool.duration_ms",
        ),
    ),
    "octopus.approval.wait": SpanType(
        name="octopus.approval.wait",
        category="approval",
        description="Waiting for human approval",
        required_attrs=("octopus.approval.state",),
        optional_attrs=("octopus.approval.agent_id",),
    ),
    "octopus.outcome": SpanType(
        name="octopus.outcome",
        category="outcome",
        description="Task/workflow outcome with decision_reason",
        required_attrs=("octopus.outcome.status",),
        optional_attrs=(
            "octopus.outcome.decision_reason", "octopus.outcome.task_type",
        ),
    ),
}


@dataclass
class OctopusSpan:
    """An Octopus telemetry span conforming to OctopusTelemetry.v1.

    Fields:
        trace_id       -- Unified trace ID (16 hex chars, from trace_context)
        span_id        -- Unique span ID (16 hex chars)
        parent_span_id -- Parent span ID (None for root spans)
        span_type      -- Canonical span type name (key in SPAN_TYPES)
        ts_start       -- UTC ISO timestamp of span start
        ts_end         -- UTC ISO timestamp of span end
        duration_ms    -- Span duration in milliseconds
        status         -- Span status (ok/error/unset)
        attributes     -- Span attributes (must conform to SPAN_TYPES definition)
        error          -- Error message if status=error (max 200 chars)
        schema         -- Schema version (always SCHEMA_VERSION)
    """
    trace_id: str
    span_id: str
    parent_span_id: str | None
    span_type: str
    ts_start: str
    ts_end: str = ""
    duration_ms: int = 0
    status: str = SpanStatus.UNSET
    attributes: dict[str, Any] = field(default_factory=dict)
    error: str = ""

    @property
    def schema(self) -> str:
        return SCHEMA_VERSION

    def validate(self) -> list[str]:
        """Validate span against schema. Returns list of validation errors."""
        errors: list[str] = []
        if not self.trace_id or len(self.trace_id) != 16:
            errors.append(f"trace_id must be 16 hex chars, got: {self.trace_id!r}")
        if not self.span_id or len(self.span_id) != 16:
            errors.append(f"span_id must be 16 hex chars, got: {self.span_id!r}")
        st = SPAN_TYPES.get(self.span_type)
        if st is None:
            errors.append(f"unknown span_type: {self.span_type!r}")
        else:
            for attr in st.required_attrs:
                if attr not in self.attributes:
                    errors.append(f"missing required attr: {attr}")
        if self.status not in (s.value for s in SpanStatus):
            errors.append(f"invalid status: {self.status!r}")
        if self.error and len(self.error) > 200:
            errors.append(f"error exceeds 200 chars: {len(self.error)}")
        return errors

    def to_dict(self) -> dict:
        """Serialize span to dict for JSONL export."""
        return {
            "schema": SCHEMA_VERSION,
            "trace_id": self.trace_id,
            "span_id": self.span_id,
            "parent_span_id": self.parent_span_id,
            "span_type": self.span_type,
            "ts_start": self.ts_start,
            "ts_end": self.ts_end,
            "duration_ms": self.duration_ms,
            "status": self.status,
            "attributes": self.attributes,
            "error": self.error,
        }

    @classmethod
    def from_dict(cls, d: dict) -> OctopusSpan:
        """Deserialize span from dict."""
        return cls(
            trace_id=d.get("trace_id", ""),
            span_id=d.get("span_id", ""),
            parent_span_id=d.get("parent_span_id"),
            span_type=d.get("span_type", ""),
            ts_start=d.get("ts_start", ""),
            ts_end=d.get("ts_end", ""),
            duration_ms=d.get("duration_ms", 0),
            status=d.get("status", SpanStatus.UNSET),
            attributes=d.get("attributes", {}),
            error=d.get("error", ""),
        )


def validate_attributes(attrs: dict[str, Any]) -> list[str]:
    """Validate attribute values for export (no PII/secrets, bounded values)."""
    errors: list[str] = []
    # Check for high-cardinality string values
    for k, v in attrs.items():
        if isinstance(v, str) and len(v) > 512:
            errors.append(f"attribute {k!r} exceeds 512 chars ({len(v)})")
    return errors
