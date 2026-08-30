#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_g6_observability.py -- EQUIP G6 Observability test suite.

Tests for the unified Octopus observability system:
  A. Telemetry Schema (OctopusTelemetry.v1)
  B. Trace Context Propagation
  C. PII/Secret Redaction
  D. Trace Replay
  E. Health Digest
  F. Alert Rules
  G. Evaluation Baseline
  H. Integration (E2E trace scenario)

All tests are self-contained with no network, no secrets, no external services.
Uses temp directories for file-based modules.
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch

# Ensure _ops/telemetry is on the path
_HERE = Path(__file__).resolve().parent
_OPS = _HERE.parent
_TELEMETRY = _OPS / "telemetry"

if str(_TELEMETRY) not in sys.path:
    sys.path.insert(0, str(_TELEMETRY))

if str(_OPS) not in sys.path:
    sys.path.insert(0, str(_OPS))

# Import modules for monkey-patching in tests
import alert_rules as alert_rules_mod
import evaluation_baseline as eval_baseline_mod


# =========================================================================
# Section A: Telemetry Schema
# =========================================================================

class TestTelemetrySchema(unittest.TestCase):
    """OctopusTelemetry.v1 schema validation."""

    def test_span_types_exist(self):
        """All defined span types should have entries in SPAN_TYPES."""
        from octopus_telemetry_schema import SPAN_TYPES
        expected_types = [
            "octopus.intent.detected",
            "octopus.policy.check",
            "octopus.memory.read",
            "octopus.memory.write",
            "octopus.memory.readback",
            "octopus.model.invoke",
            "octopus.tool.call",
            "octopus.approval.wait",
            "octopus.outcome",
        ]
        for t in expected_types:
            self.assertIn(t, SPAN_TYPES)

    def test_valid_span_zero_errors(self):
        """A well-formed span should validate with zero errors."""
        from octopus_telemetry_schema import OctopusSpan
        span = OctopusSpan(
            trace_id="a1b2c3d4e5f60001",
            span_id="b2c3d4e5f6000102",
            parent_span_id=None,
            span_type="octopus.memory.read",
            ts_start="2026-08-16T20:00:00Z",
            attributes={"octopus.memory.store": "memory_store"},
        )
        errors = span.validate()
        self.assertEqual(errors, [])

    def test_invalid_trace_id_short(self):
        """Short trace_id should fail validation."""
        from octopus_telemetry_schema import OctopusSpan
        span = OctopusSpan(
            trace_id="abc",
            span_id="b2c3d4e5f6000102",
            parent_span_id=None,
            span_type="octopus.memory.read",
            ts_start="2026-08-16T20:00:00Z",
            attributes={"octopus.memory.store": "memory_store"},
        )
        errors = span.validate()
        self.assertTrue(any("trace_id" in e for e in errors))

    def test_missing_required_attr(self):
        """Span with missing required attr should fail validation."""
        from octopus_telemetry_schema import OctopusSpan
        span = OctopusSpan(
            trace_id="a1b2c3d4e5f60001",
            span_id="b2c3d4e5f6000102",
            parent_span_id=None,
            span_type="octopus.policy.check",
            ts_start="2026-08-16T20:00:00Z",
            attributes={},  # missing required: octopus.policy.gate, octopus.policy.verdict
        )
        errors = span.validate()
        self.assertTrue(len(errors) >= 2)

    def test_unknown_span_type(self):
        """Unknown span type should fail validation."""
        from octopus_telemetry_schema import OctopusSpan
        span = OctopusSpan(
            trace_id="a1b2c3d4e5f60001",
            span_id="b2c3d4e5f6000102",
            parent_span_id=None,
            span_type="nonexistent.span",
            ts_start="2026-08-16T20:00:00Z",
            attributes={},
        )
        errors = span.validate()
        self.assertTrue(any("unknown span_type" in e for e in errors))

    def test_span_serialization_roundtrip(self):
        """Span should survive dict serialization and deserialization."""
        from octopus_telemetry_schema import OctopusSpan
        span = OctopusSpan(
            trace_id="a1b2c3d4e5f60001",
            span_id="b2c3d4e5f6000102",
            parent_span_id=None,
            span_type="octopus.model.invoke",
            ts_start="2026-08-16T20:00:00Z",
            ts_end="2026-08-16T20:00:05Z",
            duration_ms=5000,
            status="ok",
            attributes={"octopus.model.provider": "deepseek", "octopus.model.tokens_in": 1000},
        )
        d = span.to_dict()
        restored = OctopusSpan.from_dict(d)
        self.assertEqual(restored.trace_id, span.trace_id)
        self.assertEqual(restored.span_type, span.span_type)
        self.assertEqual(restored.attributes, span.attributes)

    def test_error_field_max_200_chars(self):
        """Error field longer than 200 chars should fail validation."""
        from octopus_telemetry_schema import OctopusSpan
        span = OctopusSpan(
            trace_id="a1b2c3d4e5f60001",
            span_id="b2c3d4e5f6000102",
            parent_span_id=None,
            span_type="octopus.memory.read",
            ts_start="2026-08-16T20:00:00Z",
            attributes={"octopus.memory.store": "memory_store"},
            error="x" * 201,
        )
        errors = span.validate()
        self.assertTrue(any("200 chars" in e for e in errors))

    def test_validate_attributes_long_string(self):
        """Attribute values over 512 chars should be flagged."""
        from octopus_telemetry_schema import validate_attributes
        errors = validate_attributes({"key": "x" * 513})
        self.assertTrue(any("512" in e for e in errors))

    def test_validate_attributes_ok(self):
        """Normal attributes should pass validation."""
        from octopus_telemetry_schema import validate_attributes
        errors = validate_attributes({"key": "value", "num": 42, "flag": True})
        self.assertEqual(errors, [])


# =========================================================================
# Section B: Trace Context Propagation
# =========================================================================

class TestTraceContext(unittest.TestCase):
    """Unified trace context propagation."""

    def test_mint_trace_id_length(self):
        """Minted trace ID should be 16 hex chars."""
        from trace_context import mint_trace_id
        tid = mint_trace_id()
        self.assertEqual(len(tid), 16)
        self.assertTrue(all(c in "0123456789abcdef" for c in tid))

    def test_mint_unique(self):
        """Two minted trace IDs should be different."""
        from trace_context import mint_trace_id
        self.assertNotEqual(mint_trace_id(), mint_trace_id())

    def test_normalize_16_char(self):
        """16-char hex should pass through unchanged."""
        from trace_context import _normalize_trace_id
        self.assertEqual(_normalize_trace_id("a1b2c3d4e5f60001"), "a1b2c3d4e5f60001")

    def test_normalize_8_char_padding(self):
        """8-char hex should be padded to 16 chars."""
        from trace_context import _normalize_trace_id
        result = _normalize_trace_id("a1b2c3d4")
        self.assertEqual(len(result), 16)
        self.assertTrue(result.startswith("a1b2c3d4"))
        self.assertTrue(result.endswith("00000000"))

    def test_normalize_too_short(self):
        """Trace ID shorter than 8 chars should return None."""
        from trace_context import _normalize_trace_id
        self.assertIsNone(_normalize_trace_id("abc"))

    def test_normalize_none_empty(self):
        """None or empty string should return None."""
        from trace_context import _normalize_trace_id
        self.assertIsNone(_normalize_trace_id(None))
        self.assertIsNone(_normalize_trace_id(""))

    def test_contextvar_set_get_clear(self):
        """ContextVar set/get/clear should work correctly."""
        from trace_context import set_trace_id, get_trace_id, clear_trace_id
        clear_trace_id()
        self.assertIsNone(get_trace_id())
        set_trace_id("a1b2c3d4e5f60001")
        self.assertEqual(get_trace_id(), "a1b2c3d4e5f60001")
        clear_trace_id()
        self.assertIsNone(get_trace_id())

    def test_env_var_fallback(self):
        """get_trace_id should fall back to env var."""
        from trace_context import clear_trace_id, get_trace_id
        clear_trace_id()
        with patch.dict(os.environ, {"OCTOPUS_TRACE_ID": "env1234567890ab"}):
            self.assertEqual(get_trace_id(), "env1234567890ab")

    def test_brain_events_compat(self):
        """trace_id_for_brain_events should return 8-char format (first 8 of canonical)."""
        from trace_context import set_trace_id, trace_id_for_brain_events, clear_trace_id
        set_trace_id("a1b2c3d4e5f60001")
        result = trace_id_for_brain_events()
        self.assertEqual(len(result), 8)
        self.assertEqual(result, "a1b2c3d4")
        clear_trace_id()

    def test_cognitive_compat(self):
        """trace_id_for_cognitive should return trace_{12 hex chars}."""
        from trace_context import set_trace_id, trace_id_for_cognitive, clear_trace_id
        set_trace_id("a1b2c3d4e5f60001")
        self.assertEqual(trace_id_for_cognitive(), "trace_a1b2c3d4e5f6")
        clear_trace_id()

    def test_semantic_compat_deterministic(self):
        """trace_id_for_semantic_trace should be deterministic."""
        from trace_context import set_trace_id, trace_id_for_semantic_trace, clear_trace_id
        set_trace_id("a1b2c3d4e5f60001")
        h1 = trace_id_for_semantic_trace()
        h2 = trace_id_for_semantic_trace()
        self.assertEqual(h1, h2)
        self.assertEqual(len(h1), 16)
        clear_trace_id()


# =========================================================================
# Section C: PII/Secret Redaction
# =========================================================================

class TestRedaction(unittest.TestCase):
    """PII and secret redaction."""

    def test_redact_api_key(self):
        """API key patterns should be redacted."""
        from redact import redact_summary, contains_secrets
        text = "api_key=<REDACTED-OPENAI-KEY>"
        redacted = redact_summary(text)
        self.assertNotEqual(text, redacted)
        self.assertFalse(contains_secrets(redacted))

    def test_redact_openai_key(self):
        """OpenAI-style sk- keys should be redacted."""
        from redact import redact_summary, contains_secrets
        text = "key: <REDACTED-OPENAI-KEY>"
        redacted = redact_summary(text)
        self.assertNotEqual(text, redacted)

    def test_redact_github_token(self):
        """GitHub ghp_ tokens should be redacted."""
        from redact import redact_summary, contains_secrets
        text = "token: <REDACTED-GITHUB-TOKEN>"
        redacted = redact_summary(text)
        self.assertNotEqual(text, redacted)

    def test_redact_email(self):
        """Email addresses should be partially redacted."""
        from redact import redact_summary
        text = "contact: user@example.com"
        redacted = redact_summary(text)
        self.assertNotIn("@example.com", redacted)

    def test_redact_phone(self):
        """Phone numbers should be redacted."""
        from redact import redact_summary
        text = "call +989123456789"
        redacted = redact_summary(text)
        self.assertNotIn("989123456789", redacted)

    def test_preserve_numeric_attrs(self):
        """Numeric attributes should pass through unchanged."""
        from redact import redact_attributes
        attrs = {"tokens_in": 1500, "cost_usd": 0.05, "enabled": True}
        self.assertEqual(redact_attributes(attrs), attrs)

    def test_redact_long_string(self):
        """Text over 512 chars should be truncated."""
        from redact import redact_summary
        text = "x" * 600
        redacted = redact_summary(text)
        self.assertLessEqual(len(redacted), 512)

    def test_empty_string_passes(self):
        """Empty string should pass through unchanged."""
        from redact import redact_summary
        self.assertEqual(redact_summary(""), "")

    def test_contains_secrets_false(self):
        """Normal text should not trigger secret detection."""
        from redact import contains_secrets
        self.assertFalse(contains_secrets("hello world"))

    def test_redact_list_of_strings(self):
        """Lists with string items should be redacted."""
        from redact import redact_attributes
        attrs = {"items": ["secret=sk-abc123def", "normal text"]}
        redacted = redact_attributes(attrs)
        self.assertNotEqual(redacted["items"][0], attrs["items"][0])
        self.assertEqual(redacted["items"][1], attrs["items"][1])


# =========================================================================
# Section D: Trace Replay
# =========================================================================

class TestTraceReplay(unittest.TestCase):
    """Unified trace replay."""

    def test_replay_empty_trace(self):
        """Replay of nonexistent trace should return empty result."""
        from trace_replay import replay_trace
        replay = replay_trace("nonexistent_id_xyz", include_brain_events=False,
                              include_otel_traces=False, include_semantic_trace=False,
                              include_cognitive=False)
        self.assertEqual(replay.event_count, 0)
        self.assertEqual(replay.coverage_ratio, 0.0)

    def test_replay_with_sources_queried(self):
        """Replay should report which sources were queried."""
        from trace_replay import replay_trace
        replay = replay_trace("test1234", include_brain_events=True,
                              include_otel_traces=True, include_semantic_trace=True,
                              include_cognitive=True)
        self.assertIn("brain_events", replay.sources_queried)
        self.assertIn("otel_traces", replay.sources_queried)
        self.assertIn("semantic_trace", replay.sources_queried)
        self.assertIn("cognitive_stream", replay.sources_queried)

    def test_digest_format(self):
        """Trace replay digest should have expected structure."""
        from trace_replay import replay_trace
        replay = replay_trace("test1234", include_brain_events=False,
                              include_otel_traces=False, include_semantic_trace=False,
                              include_cognitive=False)
        digest = replay.to_digest()
        self.assertIn("trace_id", digest)
        self.assertIn("event_count", digest)
        self.assertIn("coverage_ratio", digest)
        self.assertIn("has_intent", digest)
        self.assertIn("has_policy", digest)
        self.assertIn("has_memory", digest)

    def test_event_chronological_order(self):
        """Events should be sorted by timestamp."""
        from trace_replay import TraceReplay, TraceEvent
        replay = TraceReplay(trace_id="test1234")
        replay.events = [
            TraceEvent(source="test", ts="2026-08-16T20:05:00Z", event_type="e3",
                       trace_id="t", agent_id="a", status="ok", duration_ms=0, summary="3", raw={}),
            TraceEvent(source="test", ts="2026-08-16T20:00:00Z", event_type="e1",
                       trace_id="t", agent_id="a", status="ok", duration_ms=0, summary="1", raw={}),
            TraceEvent(source="test", ts="2026-08-16T20:03:00Z", event_type="e2",
                       trace_id="t", agent_id="a", status="ok", duration_ms=0, summary="2", raw={}),
        ]
        replay.events.sort(key=lambda e: e.ts)
        self.assertEqual(replay.events[0].event_type, "e1")
        self.assertEqual(replay.events[1].event_type, "e2")
        self.assertEqual(replay.events[2].event_type, "e3")


# =========================================================================
# Section E: Health Digest
# =========================================================================

class TestHealthDigest(unittest.TestCase):
    """Health digest production."""

    def test_produce_digest_structure(self):
        """Digest should have expected top-level keys."""
        from health_digest import produce_digest
        digest = produce_digest(write=False)
        self.assertIn("schema", digest)
        self.assertEqual(digest["schema"], "health-digest.v1")
        self.assertIn("ts", digest)
        self.assertIn("safety", digest)
        self.assertIn("memory", digest)
        self.assertIn("workflow", digest)
        self.assertIn("telemetry_systems", digest)

    def test_safety_has_status(self):
        """Safety section should have a status field."""
        from health_digest import produce_digest
        digest = produce_digest(write=False)
        self.assertIn("status", digest["safety"])
        self.assertIn(digest["safety"]["status"], ("green", "amber", "red"))

    def test_memory_has_ratios(self):
        """Memory section should have ratio fields."""
        from health_digest import produce_digest
        digest = produce_digest(write=False)
        self.assertIn("read_before_decision_ratio", digest["memory"])
        self.assertIn("readback_success_ratio", digest["memory"])
        self.assertIn("phase_zero_targets", digest["memory"])

    def test_workflow_has_rates(self):
        """Workflow section should have success_rate."""
        from health_digest import produce_digest
        digest = produce_digest(write=False)
        self.assertIn("success_rate", digest["workflow"])

    def test_telemetry_systems_keys(self):
        """Telemetry systems should have expected subsystems."""
        from health_digest import produce_digest
        digest = produce_digest(write=False)
        for key in ("semantic_trace", "otel_traces", "cognitive_runs", "budget_telemetry"):
            self.assertIn(key, digest["telemetry_systems"])


# =========================================================================
# Section F: Alert Rules
# =========================================================================

class TestAlertRules(unittest.TestCase):
    """Alert rule evaluation."""

    def test_alert_file_writable(self):
        """Alerts should be appendable to a temp file."""
        from alert_rules import _append_alert, read_alerts
        with tempfile.TemporaryDirectory() as td:
            alert_path = Path(td) / "alerts.jsonl"
            original_path = alert_rules_mod._ALERTS_FILE
            alert_rules_mod._ALERTS_FILE = alert_path

            try:
                _append_alert({
                    "schema": "alert.v1",
                    "ts": "2026-08-16T20:00:00Z",
                    "rule": "test_alert",
                    "severity": "INFO",
                    "message": "test alert",
                })
                alerts = read_alerts()
                self.assertEqual(len(alerts), 1)
                self.assertEqual(alerts[0]["rule"], "test_alert")
            finally:
                alert_rules_mod._ALERTS_FILE = original_path

    def test_check_kill_switch_no_file(self):
        """If no kill switch file exists, no alert should fire."""
        from alert_rules import check_kill_switch
        with tempfile.TemporaryDirectory() as td:
            original_ks = alert_rules_mod._KILL_SWITCH
            alert_rules_mod._KILL_SWITCH = Path(td) / "nonexistent"
            try:
                result = check_kill_switch()
                self.assertIsNone(result)
            finally:
                alert_rules_mod._KILL_SWITCH = original_ks

    def test_check_kill_switch_active(self):
        """If kill switch file exists, CRITICAL alert should fire."""
        from alert_rules import check_kill_switch
        with tempfile.TemporaryDirectory() as td:
            original_ks = alert_rules_mod._KILL_SWITCH
            ks = Path(td) / "kill.switch"
            ks.write_text("ACTIVATED", "utf-8")
            alert_rules_mod._KILL_SWITCH = ks
            try:
                result = check_kill_switch()
                self.assertIsNotNone(result)
                self.assertEqual(result["severity"], "CRITICAL")
                self.assertEqual(result["rule"], "kill_switch_active")
            finally:
                alert_rules_mod._KILL_SWITCH = original_ks

    def test_identity_health_regression(self):
        """SOG rho below threshold should trigger WARNING."""
        from alert_rules import check_identity_health_regression
        result = check_identity_health_regression(sog_delta=0.3, rho_threshold=0.5)
        self.assertIsNotNone(result)
        self.assertEqual(result["severity"], "WARNING")

    def test_identity_health_ok(self):
        """SOG rho above threshold should NOT trigger alert."""
        from alert_rules import check_identity_health_regression
        result = check_identity_health_regression(sog_delta=0.8, rho_threshold=0.5)
        self.assertIsNone(result)

    def test_identity_health_none(self):
        """None SOG should NOT trigger alert."""
        from alert_rules import check_identity_health_regression
        result = check_identity_health_regression(sog_delta=None)
        self.assertIsNone(result)


# =========================================================================
# Section G: Evaluation Baseline
# =========================================================================

class TestEvaluationBaseline(unittest.TestCase):
    """Evaluation dataset and baseline execution."""

    def test_dataset_exists(self):
        """Evaluation dataset should have cases."""
        from evaluation_baseline import BASELINE_CASES
        self.assertGreater(len(BASELINE_CASES), 0)

    def test_all_categories_covered(self):
        """Dataset should cover all major categories."""
        from evaluation_baseline import BASELINE_CASES
        categories = set(c.category for c in BASELINE_CASES)
        for cat in ("coverage", "propagation", "redaction", "schema", "latency"):
            self.assertIn(cat, categories)

    def test_full_evaluation_runs(self):
        """Running full evaluation should produce a summary dict."""
        from evaluation_baseline import run_evaluation
        summary = run_evaluation()
        self.assertIn("schema", summary)
        self.assertIn("total", summary)
        self.assertIn("passed", summary)
        self.assertIn("failed", summary)
        self.assertIn("pass_rate", summary)
        self.assertEqual(summary["total"], summary["passed"] + summary["failed"])

    def test_pass_rate_high(self):
        """Evaluation pass rate should be >= 80%."""
        from evaluation_baseline import run_evaluation
        summary = run_evaluation()
        self.assertGreaterEqual(summary["pass_rate"], 0.8,
                                f"Pass rate {summary['pass_rate']} below 80%: "
                                f"{summary['failed']} failures in {summary['results']}")

    def test_save_dataset(self):
        """Saving dataset should write JSON file."""
        from evaluation_baseline import save_dataset
        with tempfile.TemporaryDirectory() as td:
            original = eval_baseline_mod._EVAL_DATASET
            eval_baseline_mod._EVAL_DATASET = Path(td) / "dataset.json"
            try:
                save_dataset()
                self.assertTrue(eval_baseline_mod._EVAL_DATASET.exists())
                data = json.loads(eval_baseline_mod._EVAL_DATASET.read_text("utf-8"))
                self.assertGreater(data["case_count"], 0)
            finally:
                eval_baseline_mod._EVAL_DATASET = original


# =========================================================================
# Section H: Integration (E2E trace scenario)
# =========================================================================

class TestIntegrationE2E(unittest.TestCase):
    """End-to-end integration: unified trace from intent to outcome."""

    def test_e2e_trace_scenario(self):
        """Simulate a complete E2E trace and verify it can be replayed.

        Scenario: User intent -> policy check -> memory read -> model invoke
                  -> tool call -> approval -> outcome
        """
        from octopus_telemetry_schema import OctopusSpan, SPAN_TYPES
        from trace_context import mint_trace_id
        from redact import redact_attributes, contains_secrets
        from trace_replay import TraceReplay, TraceEvent, _classify_event

        # 1. Mint a unified trace ID
        trace_id = mint_trace_id()
        self.assertEqual(len(trace_id), 16)

        # 2. Build spans for each stage
        spans = [
            OctopusSpan(
                trace_id=trace_id,
                span_id="s1aaaaaaaaaaaaa1",
                parent_span_id=None,
                span_type="octopus.intent.detected",
                ts_start="2026-08-16T20:00:00Z",
                ts_end="2026-08-16T20:00:01Z",
                duration_ms=1000,
                status="ok",
                attributes={"octopus.intent.type": "research",
                            "octopus.intent.confidence": 0.85},
            ),
            OctopusSpan(
                trace_id=trace_id,
                span_id="s2aaaaaaaaaaaaa2",
                parent_span_id="s1aaaaaaaaaaaaa1",
                span_type="octopus.policy.check",
                ts_start="2026-08-16T20:00:01Z",
                ts_end="2026-08-16T20:00:01Z",
                duration_ms=50,
                status="ok",
                attributes={"octopus.policy.gate": "NBB-CP",
                            "octopus.policy.verdict": "allowed"},
            ),
            OctopusSpan(
                trace_id=trace_id,
                span_id="s3aaaaaaaaaaaaa3",
                parent_span_id="s1aaaaaaaaaaaaa1",
                span_type="octopus.memory.read",
                ts_start="2026-08-16T20:00:01Z",
                ts_end="2026-08-16T20:00:02Z",
                duration_ms=800,
                status="ok",
                attributes={"octopus.memory.store": "memory_store",
                            "octopus.memory.rows_returned": 3,
                            "octopus.memory.read_ok": True},
            ),
            OctopusSpan(
                trace_id=trace_id,
                span_id="s4aaaaaaaaaaaaa4",
                parent_span_id="s1aaaaaaaaaaaaa1",
                span_type="octopus.model.invoke",
                ts_start="2026-08-16T20:00:02Z",
                ts_end="2026-08-16T20:00:05Z",
                duration_ms=3000,
                status="ok",
                attributes={"octopus.model.provider": "deepseek",
                            "octopus.model.tokens_in": 500,
                            "octopus.model.tokens_out": 200,
                            "octopus.model.cost_usd": 0.002},
            ),
            OctopusSpan(
                trace_id=trace_id,
                span_id="s5aaaaaaaaaaaaa5",
                parent_span_id="s4aaaaaaaaaaaaa4",
                span_type="octopus.tool.call",
                ts_start="2026-08-16T20:00:05Z",
                ts_end="2026-08-16T20:00:06Z",
                duration_ms=1000,
                status="ok",
                attributes={"octopus.tool.name": "search_vault",
                            "octopus.tool.result_status": "ok",
                            "octopus.tool.duration_ms": 1000},
            ),
            OctopusSpan(
                trace_id=trace_id,
                span_id="s6aaaaaaaaaaaaa6",
                parent_span_id=None,
                span_type="octopus.outcome",
                ts_start="2026-08-16T20:00:06Z",
                ts_end="2026-08-16T20:00:06Z",
                duration_ms=0,
                status="ok",
                attributes={"octopus.outcome.status": "success",
                            "octopus.outcome.decision_reason": "Hypothesis confirmed with evidence from vault"},
            ),
        ]

        # 3. Validate all spans
        for span in spans:
            errors = span.validate()
            self.assertEqual(errors, [], f"Span {span.span_type} has errors: {errors}")

        # 4. Redact attributes before export
        for span in spans:
            redacted = redact_attributes(span.attributes)
            # No raw secrets should leak
            self.assertFalse(any(
                contains_secrets(str(v)) for v in redacted.values() if isinstance(v, str)
            ))
        # Check numeric attrs preserved on the model span specifically
        model_span = spans[3]  # octopus.model.invoke
        redacted_model = redact_attributes(model_span.attributes)
        self.assertEqual(redacted_model.get("octopus.model.tokens_in"), 500)
        self.assertEqual(redacted_model.get("octopus.model.cost_usd"), 0.002)

        # 5. Convert to replay events and verify coverage
        replay = TraceReplay(trace_id=trace_id)
        for span in spans:
            te = TraceEvent(
                source="integration_test",
                ts=span.ts_start,
                event_type=span.span_type,
                trace_id=trace_id,
                agent_id="integration",
                status=span.status,
                duration_ms=span.duration_ms,
                summary=f"{span.span_type}: {span.attributes}",
                raw=span.to_dict(),
            )
            replay.events.append(te)
            _classify_event(span.span_type, replay)

        # 6. Verify coverage
        self.assertTrue(replay.has_intent)
        self.assertTrue(replay.has_policy)
        self.assertTrue(replay.has_memory)
        self.assertTrue(replay.has_model)
        self.assertTrue(replay.has_tool)
        self.assertTrue(replay.has_outcome)
        self.assertGreaterEqual(replay.coverage_ratio, 0.85)

        # 7. Verify digest
        digest = replay.to_digest()
        self.assertEqual(digest["trace_id"], trace_id)
        self.assertEqual(digest["event_count"], 6)
        self.assertGreaterEqual(digest["coverage_ratio"], 0.85)

    def test_e2e_redact_in_export(self):
        """PII in decision_reason should be redacted before export."""
        from octopus_telemetry_schema import OctopusSpan
        from redact import redact_attributes

        span = OctopusSpan(
            trace_id="a1b2c3d4e5f60001",
            span_id="b2c3d4e5f6000102",
            parent_span_id=None,
            span_type="octopus.outcome",
            ts_start="2026-08-16T20:00:00Z",
            attributes={
                "octopus.outcome.status": "success",
                "octopus.outcome.decision_reason": "User email user@secret.com confirmed, token sk-12345abc used",
            },
        )
        redacted_attrs = redact_attributes(span.attributes)
        # Email should be partially hidden
        self.assertNotIn("@secret.com", redacted_attrs["octopus.outcome.decision_reason"])
        # Token should be redacted
        self.assertNotIn("sk-12345abc", redacted_attrs["octopus.outcome.decision_reason"])

    def test_span_serialization_to_jsonl(self):
        """Spans should be serializable to JSONL format."""
        from octopus_telemetry_schema import OctopusSpan
        import json

        span = OctopusSpan(
            trace_id="a1b2c3d4e5f60001",
            span_id="b2c3d4e5f6000102",
            parent_span_id=None,
            span_type="octopus.memory.read",
            ts_start="2026-08-16T20:00:00Z",
            attributes={"octopus.memory.store": "memory_store"},
        )
        line = json.dumps(span.to_dict(), ensure_ascii=False)
        self.assertIsInstance(line, str)
        self.assertIn("a1b2c3d4e5f60001", line)
        # Round-trip
        restored = OctopusSpan.from_dict(json.loads(line))
        self.assertEqual(restored.trace_id, span.trace_id)


# =========================================================================
# Main runner
# =========================================================================

if __name__ == "__main__":
    suite = unittest.TestLoader().loadTestsFromModule(sys.modules[__name__])
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    total = result.testsRun
    failures = len(result.failures)
    errors = len(result.errors)
    passed = total - failures - errors

    print(f"\n{'=' * 60}")
    print(f"test_g6_observability: {passed}/{total} passed "
          f"({failures} failures, {errors} errors)")
    print(f"{'=' * 60}")

    sys.exit(1 if (failures or errors) else 0)
