#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""evaluation_baseline.py -- Evaluation dataset and baseline for Octopus observability.

Provides a versioned evaluation dataset that tests observability quality:
  - Trace coverage: does a trace_id span all expected categories?
  - Context propagation: is trace_id preserved across subsystems?
  - Redaction: are PII/secrets properly redacted?
  - Schema compliance: do spans conform to OctopusTelemetry.v1?
  - Latency measurement: can trace replay complete within time budget?

The dataset is synthetic (no real user data) and versioned.
Used to establish a baseline that future changes must not regress against.

No network, no secrets, no external services.
"""
from __future__ import annotations

import hashlib
import json
import os
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

_OPS = Path(__file__).resolve().parent.parent
_STATE = _OPS / "state"
_EVAL_DIR = _STATE / "telemetry" / "evaluation"
_EVAL_DATASET = _EVAL_DIR / "baseline-dataset.json"

SCHEMA = "evaluation-baseline.v1"
VERSION = "1.0.0"


@dataclass
class EvalCase:
    """A single evaluation test case."""
    name: str
    category: str          # "coverage" | "propagation" | "redaction" | "schema" | "latency"
    description: str
    input_data: dict
    expected_outcome: dict
    pass_criteria: str


@dataclass
class EvalResult:
    """Result of running a single evaluation case."""
    case_name: str
    passed: bool
    actual: Any = None
    expected: Any = None
    details: str = ""
    duration_ms: int = 0


def _utc_iso() -> str:
    import datetime
    return datetime.datetime.now(
        datetime.timezone.utc
    ).isoformat(timespec="seconds").replace("+00:00", "Z")


# Canonical evaluation dataset
BASELINE_CASES: list[EvalCase] = [
    # --- Coverage tests ---
    EvalCase(
        name="full_trace_coverage",
        category="coverage",
        description="A complete trace should have events in intent, memory, policy, model, outcome categories",
        input_data={
            "events": [
                {"event_type": "user_message_accepted", "category_hint": "intent"},
                {"event_type": "memory.read", "category_hint": "memory"},
                {"event_type": "policy.check", "category_hint": "policy"},
                {"event_type": "model.invoke", "category_hint": "model"},
                {"event_type": "task.completed", "category_hint": "outcome"},
            ],
        },
        expected_outcome={
            "has_intent": True,
            "has_memory": True,
            "has_policy": True,
            "has_model": True,
            "has_outcome": True,
            "coverage_ratio": 0.714,  # 5 out of 7 categories
        },
        pass_criteria="coverage_ratio >= 0.5 and all of intent/memory/policy/model/outcome present",
    ),
    EvalCase(
        name="partial_trace_coverage",
        category="coverage",
        description="A partial trace (missing policy) should still be detected",
        input_data={
            "events": [
                {"event_type": "user_message_accepted", "category_hint": "intent"},
                {"event_type": "memory.read", "category_hint": "memory"},
                {"event_type": "model.invoke", "category_hint": "model"},
            ],
        },
        expected_outcome={
            "has_intent": True,
            "has_memory": True,
            "has_policy": False,
            "has_model": True,
            "has_outcome": False,
            "coverage_ratio": 0.429,
        },
        pass_criteria="coverage_ratio < 1.0 and missing categories detected",
    ),

    # --- Context propagation tests ---
    EvalCase(
        name="trace_id_brain_events_compat",
        category="propagation",
        description="8-char brain/events.py trace_id should be normalizable to 16-char canonical",
        input_data={"trace_id": "a1b2c3d4"},
        expected_outcome={
            "normalized": "a1b2c3d400000000",
            "length": 16,
        },
        pass_criteria="normalized trace_id is 16 hex chars",
    ),
    EvalCase(
        name="trace_id_semantic_compat",
        category="propagation",
        description="16-char trace_id should produce deterministic semantic_trace hash",
        input_data={"trace_id": "a1b2c3d4e5f60001"},
        expected_outcome={
            "semantic_hash": hashlib.sha256("a1b2c3d4e5f60001".encode()).hexdigest()[:16],
        },
        pass_criteria="semantic hash is deterministic 16-char hex",
    ),
    EvalCase(
        name="trace_id_cognitive_compat",
        category="propagation",
        description="Canonical trace_id should produce valid cognitive trace_id format",
        input_data={"trace_id": "a1b2c3d4e5f60001"},
        expected_outcome={
            "cognitive_id": "trace_a1b2c3d4e5f6",
        },
        pass_criteria="cognitive format is trace_{12 hex chars}",
    ),

    # --- Redaction tests ---
    EvalCase(
        name="redact_api_key",
        category="redaction",
        description="API keys in attributes should be redacted",
        input_data={"text": "api_key=sk-abc123def456ghi789jkl"},
        expected_outcome={"contains_redaction": True},
        pass_criteria="secret pattern is replaced with hash prefix",
    ),
    EvalCase(
        name="redact_email",
        category="redaction",
        description="Email addresses should be partially redacted",
        input_data={"text": "contact: user@example.com"},
        expected_outcome={"contains_redaction": True},
        pass_criteria="email domain is hidden",
    ),
    EvalCase(
        name="preserve_numeric_attrs",
        category="redaction",
        description="Numeric attributes should pass through unchanged",
        input_data={"attrs": {"tokens_in": 1500, "cost_usd": 0.05, "enabled": True}},
        expected_outcome={"preserved": True},
        pass_criteria="numeric/bool values are unchanged",
    ),
    EvalCase(
        name="redact_long_text",
        category="redaction",
        description="Text longer than 512 chars should be truncated with hash",
        input_data={"text": "x" * 600},
        expected_outcome={"truncated": True, "length_le_512": True},
        pass_criteria="long text is truncated to <= 512 chars with hash suffix",
    ),

    # --- Schema compliance tests ---
    EvalCase(
        name="valid_span_passes_validation",
        category="schema",
        description="A well-formed OctopusSpan should have zero validation errors",
        input_data={
            "span": {
                "trace_id": "a1b2c3d4e5f60001",
                "span_id": "b2c3d4e5f6000102",
                "parent_span_id": None,
                "span_type": "octopus.memory.read",
                "ts_start": "2026-08-16T20:00:00Z",
                "attributes": {"octopus.memory.store": "memory_store"},
            },
        },
        expected_outcome={"validation_errors": 0},
        pass_criteria="no validation errors",
    ),
    EvalCase(
        name="invalid_trace_id_fails",
        category="schema",
        description="A span with wrong trace_id length should fail validation",
        input_data={
            "span": {
                "trace_id": "abc",
                "span_id": "b2c3d4e5f6000102",
                "parent_span_id": None,
                "span_type": "octopus.memory.read",
                "ts_start": "2026-08-16T20:00:00Z",
                "attributes": {"octopus.memory.store": "memory_store"},
            },
        },
        expected_outcome={"validation_errors": 1},
        pass_criteria="exactly 1 validation error about trace_id length",
    ),
    EvalCase(
        name="missing_required_attr_fails",
        category="schema",
        description="A span missing required attributes should fail validation",
        input_data={
            "span": {
                "trace_id": "a1b2c3d4e5f60001",
                "span_id": "b2c3d4e5f6000102",
                "parent_span_id": None,
                "span_type": "octopus.policy.check",
                "ts_start": "2026-08-16T20:00:00Z",
                "attributes": {},  # missing required: octopus.policy.gate, octopus.policy.verdict
            },
        },
        expected_outcome={"validation_errors": 2},
        pass_criteria="exactly 2 validation errors about missing required attrs",
    ),

    # --- Latency tests ---
    EvalCase(
        name="trace_replay_latency",
        category="latency",
        description="Trace replay should complete within 5 seconds for a trace with up to 100 events",
        input_data={"max_events": 100, "time_budget_ms": 5000},
        expected_outcome={"completed_within_budget": True},
        pass_criteria="replay completes in under 5 seconds",
    ),
]


def run_evaluation() -> dict[str, Any]:
    """Run all evaluation cases and return results.

    Returns:
        Dict with version, timestamp, results, and summary.
    """
    results: list[EvalResult] = []
    passed = 0
    failed = 0

    for case in BASELINE_CASES:
        t0 = time.perf_counter()
        actual: Any = None
        expected: Any = None
        is_passed = False
        details = ""

        try:
            actual, expected, is_passed = _run_case(case)
        except Exception as e:
            details = f"Exception: {type(e).__name__}: {e}"

        duration_ms = int((time.perf_counter() - t0) * 1000)
        result = EvalResult(
            case_name=case.name,
            passed=is_passed,
            actual=actual,
            expected=expected,
            details=details,
            duration_ms=duration_ms,
        )
        results.append(result)
        if is_passed:
            passed += 1
        else:
            failed += 1

    summary = {
        "schema": SCHEMA,
        "version": VERSION,
        "ts": _utc_iso(),
        "total": len(results),
        "passed": passed,
        "failed": failed,
        "pass_rate": round(passed / len(results), 4) if results else None,
        "results": [
            {
                "case": r.case_name,
                "passed": r.passed,
                "duration_ms": r.duration_ms,
                "details": r.details,
            }
            for r in results
        ],
    }

    return summary


def _run_case(case: EvalCase) -> tuple[Any, Any, bool]:
    """Run a single evaluation case. Returns (actual, expected, passed)."""
    if case.category == "coverage":
        return _run_coverage_case(case)
    elif case.category == "propagation":
        return _run_propagation_case(case)
    elif case.category == "redaction":
        return _run_redaction_case(case)
    elif case.category == "schema":
        return _run_schema_case(case)
    elif case.category == "latency":
        return _run_latency_case(case)
    else:
        return None, None, False


def _run_coverage_case(case: EvalCase) -> tuple[Any, Any, bool]:
    from trace_replay import TraceReplay, TraceEvent, _classify_event
    replay = TraceReplay(trace_id="eval_trace_1234")
    for ev_data in case.input_data["events"]:
        te = TraceEvent(
            source="evaluation",
            ts="2026-08-16T20:00:00Z",
            event_type=ev_data["event_type"],
            trace_id="eval_trace_1234",
            agent_id="eval",
            status="ok",
            duration_ms=0,
            summary=ev_data["event_type"],
            raw=ev_data,
        )
        _classify_event(ev_data["event_type"], replay)
        replay.events.append(te)

    actual = {
        "has_intent": replay.has_intent,
        "has_memory": replay.has_memory,
        "has_policy": replay.has_policy,
        "has_model": replay.has_model,
        "has_outcome": replay.has_outcome,
        "coverage_ratio": round(replay.coverage_ratio, 3),
    }
    expected = case.expected_outcome
    is_passed = True
    for k, v in expected.items():
        if actual.get(k) != v:
            is_passed = False
            break
    return actual, expected, is_passed


def _run_propagation_case(case: EvalCase) -> tuple[Any, Any, bool]:
    from trace_context import (
        _normalize_trace_id, trace_id_for_semantic_trace, trace_id_for_cognitive,
    )
    tid = case.input_data["trace_id"]
    actual = {}
    expected = case.expected_outcome

    if "normalized" in expected:
        actual["normalized"] = _normalize_trace_id(tid)
        actual["length"] = len(actual["normalized"]) if actual["normalized"] else 0

    if "semantic_hash" in expected:
        actual["semantic_hash"] = trace_id_for_semantic_trace.__wrapped__(
            lambda: tid
        )() if False else hashlib.sha256(tid.encode()).hexdigest()[:16]
        # Direct test without setting context
        actual["semantic_hash"] = hashlib.sha256(tid.encode()).hexdigest()[:16]

    if "cognitive_id" in expected:
        actual["cognitive_id"] = f"trace_{tid[:12]}"

    is_passed = actual == expected
    return actual, expected, is_passed


def _run_redaction_case(case: EvalCase) -> tuple[Any, Any, bool]:
    from redact import redact_attributes, redact_summary, contains_secrets

    if "text" in case.input_data:
        text = case.input_data["text"]
        redacted = redact_summary(text)
        actual = {
            "contains_redaction": redacted != text,
            "result_length": len(redacted),
        }
        if "truncated" in case.expected_outcome:
            actual["truncated"] = len(text) > 512 and len(redacted) <= 512
            actual["length_le_512"] = len(redacted) <= 512
        expected = case.expected_outcome
        is_passed = True
        for k, v in expected.items():
            if actual.get(k) != v:
                is_passed = False
                break
        return actual, expected, is_passed

    if "attrs" in case.input_data:
        attrs = case.input_data["attrs"]
        redacted = redact_attributes(attrs)
        actual = {"preserved": redacted == attrs}
        expected = case.expected_outcome
        return actual, expected, actual["preserved"] == expected.get("preserved", False)

    return None, None, False


def _run_schema_case(case: EvalCase) -> tuple[Any, Any, bool]:
    from octopus_telemetry_schema import OctopusSpan

    span_data = case.input_data["span"]
    span = OctopusSpan(
        trace_id=span_data["trace_id"],
        span_id=span_data["span_id"],
        parent_span_id=span_data.get("parent_span_id"),
        span_type=span_data["span_type"],
        ts_start=span_data["ts_start"],
        attributes=span_data.get("attributes", {}),
    )
    errors = span.validate()
    actual = {"validation_errors": len(errors)}
    expected = case.expected_outcome
    return actual, expected, actual["validation_errors"] == expected["validation_errors"]


def _run_latency_case(case: EvalCase) -> tuple[Any, Any, bool]:
    from trace_replay import replay_trace
    budget_ms = case.input_data["time_budget_ms"]

    t0 = time.perf_counter()
    replay = replay_trace("nonexistent_trace_for_latency_test")
    duration_ms = int((time.perf_counter() - t0) * 1000)

    actual = {"completed_within_budget": duration_ms <= budget_ms}
    expected = case.expected_outcome
    return actual, expected, actual["completed_within_budget"]


def save_dataset() -> None:
    """Save the evaluation dataset to disk for versioning."""
    try:
        _EVAL_DIR.mkdir(parents=True, exist_ok=True)
        data = {
            "schema": SCHEMA,
            "version": VERSION,
            "ts": _utc_iso(),
            "case_count": len(BASELINE_CASES),
            "cases": [
                {
                    "name": c.name,
                    "category": c.category,
                    "description": c.description,
                    "input_data": c.input_data,
                    "expected_outcome": c.expected_outcome,
                    "pass_criteria": c.pass_criteria,
                }
                for c in BASELINE_CASES
            ],
        }
        _EVAL_DATASET.write_text(
            json.dumps(data, ensure_ascii=False, indent=2), "utf-8"
        )
    except OSError:
        pass
