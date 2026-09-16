#!/usr/bin/env python3
"""Tests for neural_apply_evidence.py -- seven-day neural APPLY evidence aggregator.

Hermetic, stdlib-only, no network, no live-state writes.
Runs standalone (python test_neural_apply_evidence.py) or via pytest.
"""
import json
import os
import subprocess
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from io import StringIO

# Ensure module is importable
HERE = Path(__file__).resolve().parent          # _ops/tests
OPS = HERE.parent                               # _ops
TEL = OPS / "telemetry"
if str(TEL) not in sys.path:
    sys.path.insert(0, str(TEL))

import neural_apply_evidence as N


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _ts(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def _pain_line(
    event_id: str,
    ts: datetime,
    action: str = "protective_halt",
    executable: bool = True,
    effect: str = "internal",
) -> str:
    return json.dumps({
        "event_id": event_id,
        "ts": _ts(ts),
        "action": action,
        "executable": executable,
        "effect": effect,
    })


def _incident_line(incident_id: str, ts: datetime) -> str:
    return json.dumps({"incident_id": incident_id, "ts": _ts(ts)})


def _write_jsonl(tmp: Path, lines: list[str]) -> Path:
    tmp.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return tmp


def _write_json(tmp: Path, obj: dict) -> Path:
    tmp.write_text(json.dumps(obj), encoding="utf-8")
    return tmp


# Helper for ledger JSON with coverage spanning the typical _make_pain window
# [2026-08-03T12:00:00Z, 2026-08-10T12:00:00Z]
def _ledger_json_with_coverage(tmp: Path, integrity: bool,
                                cs: str = "2026-08-03T00:00:00Z",
                                ce: str = "2026-08-11T00:00:00Z") -> Path:
    return _write_json(tmp, {
        "integrity": integrity,
        "coverage_start": cs,
        "coverage_end": ce,
    })


class _TempDirMixin:
    """Mixin providing a temp directory for test files."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp(prefix="nae_test_")

    def _tmp(self, name: str) -> Path:
        return Path(self.tmpdir) / name


# ---------------------------------------------------------------------------
# Timestamp parsing
# ---------------------------------------------------------------------------

class TestParseUtc(unittest.TestCase):

    def test_iso_z(self):
        dt = N._parse_utc("2026-08-01T12:00:00Z")
        self.assertEqual(dt.year, 2026)
        self.assertEqual(dt.month, 8)
        self.assertEqual(dt.day, 1)
        self.assertEqual(dt.hour, 12)
        self.assertEqual(dt.tzinfo, timezone.utc)

    def test_iso_offset(self):
        dt = N._parse_utc("2026-08-01T12:00:00+00:00")
        self.assertIsNotNone(dt)
        self.assertEqual(dt.tzinfo, timezone.utc)

    def test_iso_no_tz(self):
        dt = N._parse_utc("2026-08-01T12:00:00")
        self.assertIsNotNone(dt)
        self.assertEqual(dt.tzinfo, timezone.utc)

    def test_iso_microseconds(self):
        dt = N._parse_utc("2026-08-01T12:00:00.123456Z")
        self.assertIsNotNone(dt)
        self.assertEqual(dt.microsecond, 123456)

    def test_epoch(self):
        dt = N._parse_utc("1722542400")
        self.assertIsNotNone(dt)
        self.assertEqual(dt.tzinfo, timezone.utc)

    def test_epoch_float(self):
        dt = N._parse_utc("1722542400.5")
        self.assertIsNotNone(dt)
        self.assertEqual(dt.tzinfo, timezone.utc)

    def test_empty(self):
        self.assertIsNone(N._parse_utc(""))
        self.assertIsNone(N._parse_utc("  "))

    def test_garbage(self):
        self.assertIsNone(N._parse_utc("not-a-date"))

    def test_space_format(self):
        dt = N._parse_utc("2026-08-01 12:00:00")
        self.assertIsNotNone(dt)
        self.assertEqual(dt.tzinfo, timezone.utc)

    # Audit 8: non-zero ISO offsets
    def test_nonzero_offset_positive(self):
        """+05:30 offset converts to UTC correctly."""
        dt = N._parse_utc("2026-08-01T17:30:00+05:30")
        self.assertIsNotNone(dt)
        self.assertEqual(dt.hour, 12)  # 17:30 - 5:30 = 12:00 UTC
        self.assertEqual(dt.day, 1)
        self.assertEqual(dt.tzinfo, timezone.utc)

    def test_nonzero_offset_negative(self):
        """-03:00 offset converts to UTC correctly."""
        dt = N._parse_utc("2026-08-01T09:00:00-03:00")
        self.assertIsNotNone(dt)
        self.assertEqual(dt.hour, 12)  # 09:00 + 3:00 = 12:00 UTC
        self.assertEqual(dt.day, 1)
        self.assertEqual(dt.tzinfo, timezone.utc)

    def test_offset_date_rollover_positive(self):
        """+14:00 offset can roll the UTC date back a day."""
        dt = N._parse_utc("2026-08-02T02:00:00+14:00")
        self.assertIsNotNone(dt)
        self.assertEqual(dt.day, 1)   # 02:00 - 14:00 = prev day 12:00 UTC
        self.assertEqual(dt.hour, 12)
        self.assertEqual(dt.tzinfo, timezone.utc)

    def test_offset_date_rollover_negative(self):
        """-11:00 offset: 02:00 local + 11:00 = 13:00 UTC same day."""
        dt = N._parse_utc("2026-08-01T02:00:00-11:00")
        self.assertIsNotNone(dt)
        self.assertEqual(dt.day, 1)   # 02:00 + 11:00 = 13:00 UTC, same day
        self.assertEqual(dt.hour, 13)
        self.assertEqual(dt.tzinfo, timezone.utc)


# ---------------------------------------------------------------------------
# JSONL loading
# ---------------------------------------------------------------------------

class TestLoadJsonl(unittest.TestCase):

    def test_missing_file(self):
        recs = N._load_jsonl(Path("/nonexistent/path.jsonl"))
        self.assertEqual(recs, [])

    def test_valid_lines(self):
        p = Path(tempfile.mktemp(suffix=".jsonl"))
        _write_jsonl(p, [
            json.dumps({"a": 1}),
            json.dumps({"b": 2}),
        ])
        try:
            recs = N._load_jsonl(p)
            self.assertEqual(len(recs), 2)
            self.assertEqual(recs[0]["a"], 1)
        finally:
            p.unlink()

    def test_malformed_line(self):
        p = Path(tempfile.mktemp(suffix=".jsonl"))
        _write_jsonl(p, [
            json.dumps({"a": 1}),
            "THIS IS NOT JSON",
            json.dumps({"b": 2}),
        ])
        try:
            recs = N._load_jsonl(p)
            self.assertEqual(len(recs), 3)
            self.assertTrue(recs[1].get("_parse_error"))
            self.assertEqual(recs[1]["_line"], 2)
        finally:
            p.unlink()

    def test_blank_lines_skipped(self):
        p = Path(tempfile.mktemp(suffix=".jsonl"))
        p.write_text('\n{"a":1}\n\n', encoding="utf-8")
        try:
            recs = N._load_jsonl(p)
            self.assertEqual(len(recs), 1)
        finally:
            p.unlink()


# ---------------------------------------------------------------------------
# JSON / JSONL loading
# ---------------------------------------------------------------------------

class TestLoadJsonOrJsonl(unittest.TestCase):

    def test_missing(self):
        self.assertIsNone(N._load_json_or_jsonl(Path("/nonexistent")))

    def test_json_dict(self):
        p = Path(tempfile.mktemp(suffix=".json"))
        _write_json(p, {"integrity": True})
        try:
            data = N._load_json_or_jsonl(p)
            self.assertIsInstance(data, dict)
            self.assertTrue(data["integrity"])
        finally:
            p.unlink()

    def test_jsonl(self):
        p = Path(tempfile.mktemp(suffix=".jsonl"))
        _write_jsonl(p, [
            json.dumps({"integrity": True}),
            json.dumps({"integrity": False}),
        ])
        try:
            data = N._load_json_or_jsonl(p)
            self.assertIsInstance(data, list)
            self.assertEqual(len(data), 2)
        finally:
            p.unlink()


# ---------------------------------------------------------------------------
# Record extraction
# ---------------------------------------------------------------------------

class TestExtraction(unittest.TestCase):

    def test_action_map(self):
        self.assertEqual(N._extract_action({"action": "protective_halt"}), "protective_halt")
        self.assertEqual(N._extract_action({"action": "halt"}), "protective_halt")
        self.assertEqual(N._extract_action({"action": "throttle"}), "throttle")
        self.assertEqual(N._extract_action({"action": "proposal_only"}), "proposal_only")
        self.assertEqual(N._extract_action({"action": "proposal-only"}), "proposal_only")
        self.assertEqual(N._extract_action({"action": "bogus"}), "unknown")
        self.assertEqual(N._extract_action({}), "unknown")

    def test_effect_map(self):
        self.assertEqual(N._extract_effect({"effect": "internal"}), "internal")
        self.assertEqual(N._extract_effect({"effect": "external"}), "external")
        self.assertEqual(N._extract_effect({"effect": "forbidden"}), "forbidden")
        self.assertEqual(N._extract_effect({"effect": "bogus"}), "unknown")
        self.assertEqual(N._extract_effect({}), "unknown")

    def test_executable_bool(self):
        self.assertTrue(N._extract_executable({"executable": True}))
        self.assertFalse(N._extract_executable({"executable": False}))
        self.assertTrue(N._extract_executable({"executable": "true"}))
        self.assertTrue(N._extract_executable({"executable": "1"}))
        self.assertFalse(N._extract_executable({"executable": "0"}))
        self.assertFalse(N._extract_executable({}))

    def test_pain_record_ok(self):
        now = datetime(2026, 8, 1, 12, 0, 0, tzinfo=timezone.utc)
        rec = {
            "event_id": "e1",
            "ts": "2026-08-01T12:00:00Z",
            "action": "protective_halt",
            "executable": True,
            "effect": "internal",
        }
        pr = N._to_pain_record(rec)
        self.assertIsNotNone(pr)
        self.assertEqual(pr.event_id, "e1")
        self.assertEqual(pr.action, "protective_halt")
        self.assertTrue(pr.executable)

    def test_pain_record_malformed(self):
        rec = {"_parse_error": True, "_line": 1, "_raw": "bad"}
        self.assertIsNone(N._to_pain_record(rec))

    def test_pain_record_no_ts(self):
        self.assertIsNone(N._to_pain_record({"event_id": "e1"}))

    def test_incident_record_ok(self):
        rec = {"incident_id": "i1", "ts": "2026-08-01T12:00:00Z"}
        ir = N._to_incident_record(rec)
        self.assertIsNotNone(ir)
        self.assertEqual(ir.incident_id, "i1")

    def test_incident_record_malformed(self):
        self.assertIsNone(
            N._to_incident_record({"_parse_error": True, "_line": 1, "_raw": "x"})
        )

    def test_dedup_key(self):
        r1 = {"event_id": "abc", "ts": "2026-08-01T00:00:00Z"}
        r2 = {"event_id": "abc", "ts": "2026-08-01T00:00:00Z"}
        self.assertEqual(N._dedup_key(r1), N._dedup_key(r2))

    def test_dedup_key_fallback(self):
        r1 = {"foo": "bar"}
        r2 = {"foo": "bar"}
        self.assertEqual(N._dedup_key(r1), N._dedup_key(r2))

    # Audit 7: returned_action fallback
    def test_returned_action_fallback(self):
        """returned_action is used when action is absent/empty."""
        self.assertEqual(
            N._extract_action({"returned_action": "protective_halt"}),
            "protective_halt",
        )

    def test_returned_action_ignored_when_action_present(self):
        """action takes precedence over returned_action."""
        self.assertEqual(
            N._extract_action({"action": "throttle", "returned_action": "protective_halt"}),
            "throttle",
        )

    # Audit 7: effect defaults to "internal" for known local actions
    def test_effect_defaults_internal_for_known_action(self):
        """Known local action without effect field => effect='internal'."""
        rec = {
            "event_id": "e1",
            "ts": "2026-08-01T12:00:00Z",
            "action": "protective_halt",
            "executable": True,
            # no effect field
        }
        pr = N._to_pain_record(rec)
        self.assertIsNotNone(pr)
        self.assertEqual(pr.effect, "internal")

    def test_effect_defaults_internal_for_throttle(self):
        rec = {
            "event_id": "e2",
            "ts": "2026-08-01T12:00:00Z",
            "action": "throttle",
            "executable": True,
        }
        pr = N._to_pain_record(rec)
        self.assertIsNotNone(pr)
        self.assertEqual(pr.effect, "internal")

    def test_effect_defaults_internal_for_proposal_only(self):
        rec = {
            "event_id": "e3",
            "ts": "2026-08-01T12:00:00Z",
            "action": "proposal_only",
            "executable": False,
        }
        pr = N._to_pain_record(rec)
        self.assertIsNotNone(pr)
        self.assertEqual(pr.effect, "internal")

    def test_effect_unknown_remains_for_unknown_action(self):
        """Unknown action without effect => effect stays 'unknown'."""
        rec = {
            "event_id": "e4",
            "ts": "2026-08-01T12:00:00Z",
            "action": "bogus",
            "executable": True,
        }
        pr = N._to_pain_record(rec)
        self.assertIsNotNone(pr)
        self.assertEqual(pr.effect, "unknown")

    def test_explicit_effect_overrides_default(self):
        """Explicit effect='external' should not be overridden."""
        rec = {
            "event_id": "e5",
            "ts": "2026-08-01T12:00:00Z",
            "action": "protective_halt",
            "executable": True,
            "effect": "external",
        }
        pr = N._to_pain_record(rec)
        self.assertIsNotNone(pr)
        self.assertEqual(pr.effect, "external")


# ---------------------------------------------------------------------------
# Basic evaluate() -- empty / missing files
# ---------------------------------------------------------------------------

class TestEvaluateEmpty(_TempDirMixin, unittest.TestCase):

    def test_missing_pain_file(self):
        """Missing pain file => empty report, INSUFFICIENT_EVIDENCE."""
        r = N.evaluate(self._tmp("nonexistent.jsonl"))
        self.assertEqual(r.total_records_seen, 0)
        self.assertEqual(r.verdict, "INSUFFICIENT_EVIDENCE")

    def test_empty_pain_file(self):
        """Empty pain file => zero counters."""
        p = self._tmp("empty.jsonl")
        p.write_text("", encoding="utf-8")
        r = N.evaluate(p)
        self.assertEqual(r.total_records_seen, 0)
        self.assertEqual(r.executable_total, 0)
        self.assertIsNone(r.false_positive_rate)

    def test_only_malformed_lines(self):
        """Only malformed lines => unknown_malformed counted."""
        p = self._tmp("malformed.jsonl")
        p.write_text("not json\nalso not json\n", encoding="utf-8")
        r = N.evaluate(p)
        self.assertEqual(r.total_records_seen, 2)
        self.assertEqual(r.unique_ids, 2)
        self.assertEqual(r.unknown_malformed_count, 2)
        self.assertEqual(r.records_in_window, 0)


# ---------------------------------------------------------------------------
# Audit 2: bad as_of / window_days raise ValueError
# ---------------------------------------------------------------------------

class TestBadAsOf(_TempDirMixin, unittest.TestCase):

    def test_unparseable_as_of_raises(self):
        with self.assertRaises(ValueError) as ctx:
            N.evaluate(self._tmp("pain.jsonl"), as_of="not-a-date")
        self.assertIn("unparseable", str(ctx.exception))

    def test_zero_window_days_raises(self):
        with self.assertRaises(ValueError) as ctx:
            N.evaluate(self._tmp("pain.jsonl"), window_days=0)
        self.assertIn("positive", str(ctx.exception))

    def test_negative_window_days_raises(self):
        with self.assertRaises(ValueError) as ctx:
            N.evaluate(self._tmp("pain.jsonl"), window_days=-1)
        self.assertIn("positive", str(ctx.exception))


# ---------------------------------------------------------------------------
# Audit 3: complete_days
# ---------------------------------------------------------------------------

class TestCompleteDays(unittest.TestCase):

    def test_midnight_boundary(self):
        """When window_start and window_end are both at midnight, exactly
        window_days complete days."""
        days = N._compute_complete_days(
            datetime(2026, 8, 5, 0, 0, 0, tzinfo=timezone.utc),
            datetime(2026, 8, 12, 0, 0, 0, tzinfo=timezone.utc),
        )
        self.assertEqual(len(days), 7)
        self.assertEqual(days[0], "2026-08-05")
        self.assertEqual(days[-1], "2026-08-11")

    def test_non_midnight_window(self):
        """Partial first and last days excluded."""
        days = N._compute_complete_days(
            datetime(2026, 8, 5, 12, 0, 0, tzinfo=timezone.utc),
            datetime(2026, 8, 12, 12, 0, 0, tzinfo=timezone.utc),
        )
        self.assertEqual(len(days), 6)  # Aug 6-11
        self.assertEqual(days[0], "2026-08-06")
        self.assertEqual(days[-1], "2026-08-11")

    def test_single_day_window(self):
        days = N._compute_complete_days(
            datetime(2026, 8, 5, 0, 0, 0, tzinfo=timezone.utc),
            datetime(2026, 8, 6, 0, 0, 0, tzinfo=timezone.utc),
        )
        self.assertEqual(len(days), 1)
        self.assertEqual(days[0], "2026-08-05")

    def test_sub_day_window(self):
        days = N._compute_complete_days(
            datetime(2026, 8, 5, 12, 0, 0, tzinfo=timezone.utc),
            datetime(2026, 8, 5, 18, 0, 0, tzinfo=timezone.utc),
        )
        self.assertEqual(len(days), 0)

    def test_report_complete_days_field(self):
        r = N.EvidenceReport()
        self.assertEqual(r.complete_days, 0)


# ---------------------------------------------------------------------------
# Counters
# ---------------------------------------------------------------------------

class TestRawCounters(_TempDirMixin, unittest.TestCase):
    """Test raw counter classification."""

    def _make_report(self, lines: list[str], as_of: str) -> N.EvidenceReport:
        p = _write_jsonl(self._tmp("pain.jsonl"), lines)
        return N.evaluate(p, as_of=as_of)

    def test_executable_protective_halt(self):
        as_of = "2026-08-10T12:00:00Z"
        ts = datetime(2026, 8, 9, 12, 0, 0, tzinfo=timezone.utc)
        lines = [_pain_line("e1", ts, action="protective_halt", executable=True)]
        r = self._make_report(lines, as_of)
        self.assertEqual(r.executable_protective_halt_count, 1)
        self.assertEqual(r.executable_throttle_count, 0)
        self.assertEqual(r.proposal_only_count, 0)
        self.assertEqual(r.executable_total, 1)

    def test_executable_throttle(self):
        as_of = "2026-08-10T12:00:00Z"
        ts = datetime(2026, 8, 9, 12, 0, 0, tzinfo=timezone.utc)
        lines = [_pain_line("e1", ts, action="throttle", executable=True)]
        r = self._make_report(lines, as_of)
        self.assertEqual(r.executable_throttle_count, 1)
        self.assertEqual(r.executable_total, 1)

    def test_proposal_only(self):
        as_of = "2026-08-10T12:00:00Z"
        ts = datetime(2026, 8, 9, 12, 0, 0, tzinfo=timezone.utc)
        lines = [_pain_line("e1", ts, action="proposal_only", executable=False)]
        r = self._make_report(lines, as_of)
        self.assertEqual(r.proposal_only_count, 1)
        self.assertEqual(r.executable_total, 0)

    def test_forbidden_effect(self):
        as_of = "2026-08-10T12:00:00Z"
        ts = datetime(2026, 8, 9, 12, 0, 0, tzinfo=timezone.utc)
        lines = [_pain_line("e1", ts, action="protective_halt", executable=True, effect="forbidden")]
        r = self._make_report(lines, as_of)
        self.assertEqual(r.forbidden_or_external_count, 1)

    def test_external_effect(self):
        as_of = "2026-08-10T12:00:00Z"
        ts = datetime(2026, 8, 9, 12, 0, 0, tzinfo=timezone.utc)
        lines = [_pain_line("e1", ts, action="protective_halt", executable=True, effect="external")]
        r = self._make_report(lines, as_of)
        self.assertEqual(r.forbidden_or_external_count, 1)

    # Audit 9: unknown action executables counted in executable_total but NOT
    # in unknown_malformed_count
    def test_unknown_action_executable_counted(self):
        as_of = "2026-08-10T12:00:00Z"
        ts = datetime(2026, 8, 9, 12, 0, 0, tzinfo=timezone.utc)
        lines = [_pain_line("e1", ts, action="bogus", executable=True)]
        r = self._make_report(lines, as_of)
        self.assertEqual(r.executable_total, 1)
        self.assertEqual(r.unknown_malformed_count, 0)


# ---------------------------------------------------------------------------
# Window filtering
# ---------------------------------------------------------------------------

class TestWindowFiltering(_TempDirMixin, unittest.TestCase):

    def test_in_window(self):
        as_of = "2026-08-10T00:00:00Z"
        ts = datetime(2026, 8, 9, 0, 0, 0, tzinfo=timezone.utc)  # day 6
        p = _write_jsonl(self._tmp("pain.jsonl"), [
            _pain_line("e1", ts, action="protective_halt"),
        ])
        r = N.evaluate(p, as_of=as_of)
        self.assertEqual(r.records_in_window, 1)
        self.assertEqual(r.records_out_of_window, 0)

    def test_out_of_window_early(self):
        as_of = "2026-08-10T00:00:00Z"
        ts = datetime(2026, 8, 2, 23, 59, 59, tzinfo=timezone.utc)  # just before window start
        p = _write_jsonl(self._tmp("pain.jsonl"), [
            _pain_line("e1", ts, action="protective_halt"),
        ])
        r = N.evaluate(p, as_of=as_of)
        self.assertEqual(r.records_in_window, 0)
        self.assertEqual(r.records_out_of_window, 1)

    def test_exact_boundary_start(self):
        """Record exactly at window start => in window (>=)."""
        as_of = "2026-08-10T00:00:00Z"
        # window start = 2026-08-03T00:00:00Z
        ts = datetime(2026, 8, 3, 0, 0, 0, tzinfo=timezone.utc)
        p = _write_jsonl(self._tmp("pain.jsonl"), [
            _pain_line("e1", ts, action="protective_halt"),
        ])
        r = N.evaluate(p, as_of=as_of)
        self.assertEqual(r.records_in_window, 1)

    def test_exact_boundary_end(self):
        """Record exactly at window end => in window (<=)."""
        as_of = "2026-08-10T00:00:00Z"
        ts = datetime(2026, 8, 10, 0, 0, 0, tzinfo=timezone.utc)
        p = _write_jsonl(self._tmp("pain.jsonl"), [
            _pain_line("e1", ts, action="protective_halt"),
        ])
        r = N.evaluate(p, as_of=as_of)
        self.assertEqual(r.records_in_window, 1)

    def test_after_window(self):
        as_of = "2026-08-10T00:00:00Z"
        ts = datetime(2026, 8, 10, 0, 0, 1, tzinfo=timezone.utc)
        p = _write_jsonl(self._tmp("pain.jsonl"), [
            _pain_line("e1", ts, action="protective_halt"),
        ])
        r = N.evaluate(p, as_of=as_of)
        self.assertEqual(r.records_in_window, 0)
        self.assertEqual(r.records_out_of_window, 1)


# ---------------------------------------------------------------------------
# De-duplication
# ---------------------------------------------------------------------------

class TestDedup(_TempDirMixin, unittest.TestCase):

    def test_duplicates_counted_once(self):
        as_of = "2026-08-10T12:00:00Z"
        ts = datetime(2026, 8, 9, 12, 0, 0, tzinfo=timezone.utc)
        lines = [
            _pain_line("e1", ts, action="protective_halt"),
            _pain_line("e1", ts, action="protective_halt"),  # duplicate
        ]
        p = _write_jsonl(self._tmp("pain.jsonl"), lines)
        r = N.evaluate(p, as_of=as_of)
        self.assertEqual(r.total_records_seen, 2)
        self.assertEqual(r.unique_ids, 1)
        self.assertEqual(r.duplicate_count, 1)
        self.assertEqual(r.executable_protective_halt_count, 1)

    # Audit 1: subprocess test for sha256 cross-process stability
    def test_sha256_cross_process(self):
        """SHA-256 dedup keys are deterministic across processes."""
        code = (
            "import json, sys; sys.path.insert(0, %r); "
            "import neural_apply_evidence as N; "
            "rec = {'foo': 'bar'}; "
            "print(N._dedup_key(rec))"
        ) % str(TEL)
        result = subprocess.run(
            [sys.executable, "-c", code],
            capture_output=True, text=True, timeout=10,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        cross_process_key = result.stdout.strip()
        same_process_key = N._dedup_key({"foo": "bar"})
        self.assertEqual(cross_process_key, same_process_key)
        self.assertTrue(cross_process_key.startswith("_sha256:"))

    def test_sha256_format(self):
        """Fallback dedup key uses _sha256: prefix."""
        key = N._dedup_key({"x": 1, "y": 2})
        self.assertTrue(key.startswith("_sha256:"))
        # sha256 hex is 64 chars
        self.assertEqual(len(key.split(":", 1)[1]), 64)


# ---------------------------------------------------------------------------
# False-positive rate
# ---------------------------------------------------------------------------

class TestFalsePositiveRate(_TempDirMixin, unittest.TestCase):

    def test_no_incidents_all_fp(self):
        """Audit 6: No incident file => FP unknown (not 1.0)."""
        as_of = "2026-08-10T12:00:00Z"
        base = datetime(2026, 8, 9, 12, 0, 0, tzinfo=timezone.utc)
        pain_lines = [
            _pain_line("e1", base, action="protective_halt", executable=True),
            _pain_line("e2", base + timedelta(minutes=1), action="throttle", executable=True),
        ]
        p = _write_jsonl(self._tmp("pain.jsonl"), pain_lines)
        # No incident file
        r = N.evaluate(p, as_of=as_of)
        self.assertIsNone(r.false_positive_rate)
        self.assertIn("incident source", r.false_positive_rate_reason.lower())
        self.assertEqual(r.executable_total, 2)

    def test_empty_incident_file_all_fp(self):
        """Empty incident file (valid) => all executables are false positives."""
        as_of = "2026-08-10T12:00:00Z"
        base = datetime(2026, 8, 9, 12, 0, 0, tzinfo=timezone.utc)
        pain_lines = [
            _pain_line("e1", base, action="protective_halt", executable=True),
            _pain_line("e2", base + timedelta(minutes=1), action="throttle", executable=True),
        ]
        p = _write_jsonl(self._tmp("pain.jsonl"), pain_lines)
        inc = _write_jsonl(self._tmp("inc.jsonl"), [])  # empty => valid
        r = N.evaluate(p, incident_path=inc, as_of=as_of)
        self.assertTrue(r.incident_source_valid)
        self.assertIsNotNone(r.false_positive_rate)
        self.assertAlmostEqual(r.false_positive_rate, 1.0)
        self.assertEqual(r.executable_total, 2)

    def test_all_incidents_zero_fp(self):
        """Every executable has a matching incident within +1h."""
        as_of = "2026-08-10T12:00:00Z"
        base = datetime(2026, 8, 9, 12, 0, 0, tzinfo=timezone.utc)
        pain_lines = [
            _pain_line("e1", base, action="protective_halt", executable=True),
        ]
        inc_lines = [
            _incident_line("i1", base + timedelta(minutes=30)),
        ]
        p = _write_jsonl(self._tmp("pain.jsonl"), pain_lines)
        inc = _write_jsonl(self._tmp("inc.jsonl"), inc_lines)
        r = N.evaluate(p, incident_path=inc, as_of=as_of)
        self.assertIsNotNone(r.false_positive_rate)
        self.assertAlmostEqual(r.false_positive_rate, 0.0)

    def test_fp_unknown_no_executables(self):
        """Zero executables + valid incident source => fp rate None."""
        as_of = "2026-08-10T12:00:00Z"
        base = datetime(2026, 8, 9, 12, 0, 0, tzinfo=timezone.utc)
        pain_lines = [
            _pain_line("e1", base, action="proposal_only", executable=False),
        ]
        p = _write_jsonl(self._tmp("pain.jsonl"), pain_lines)
        inc = _write_jsonl(self._tmp("inc.jsonl"), [])
        r = N.evaluate(p, incident_path=inc, as_of=as_of)
        self.assertIsNone(r.false_positive_rate)
        self.assertIn("zero", r.false_positive_rate_reason)

    def test_incident_exactly_one_hour_after(self):
        """Incident at exactly +1h should match (<=)."""
        as_of = "2026-08-10T12:00:00Z"
        base = datetime(2026, 8, 9, 12, 0, 0, tzinfo=timezone.utc)
        pain_lines = [
            _pain_line("e1", base, action="protective_halt", executable=True),
        ]
        # Incident exactly at base + 1h
        inc_lines = [
            _incident_line("i1", base + timedelta(hours=1)),
        ]
        p = _write_jsonl(self._tmp("pain.jsonl"), pain_lines)
        inc = _write_jsonl(self._tmp("inc.jsonl"), inc_lines)
        r = N.evaluate(p, incident_path=inc, as_of=as_of)
        # Incident at exactly +1h => should count as matched (<=)
        self.assertAlmostEqual(r.false_positive_rate, 0.0)

    def test_incident_just_after_one_hour(self):
        """Incident at +1h + 1s => not matched."""
        as_of = "2026-08-10T12:00:00Z"
        base = datetime(2026, 8, 9, 12, 0, 0, tzinfo=timezone.utc)
        pain_lines = [
            _pain_line("e1", base, action="protective_halt", executable=True),
        ]
        inc_lines = [
            _incident_line("i1", base + timedelta(hours=1, seconds=1)),
        ]
        p = _write_jsonl(self._tmp("pain.jsonl"), pain_lines)
        inc = _write_jsonl(self._tmp("inc.jsonl"), inc_lines)
        r = N.evaluate(p, incident_path=inc, as_of=as_of)
        self.assertAlmostEqual(r.false_positive_rate, 1.0)

    def test_incident_before_executable(self):
        """Incident before executable should NOT prevent FP classification."""
        as_of = "2026-08-10T12:00:00Z"
        base = datetime(2026, 8, 9, 12, 0, 0, tzinfo=timezone.utc)
        pain_lines = [
            _pain_line("e1", base, action="protective_halt", executable=True),
        ]
        inc_lines = [
            _incident_line("i1", base - timedelta(minutes=30)),
        ]
        p = _write_jsonl(self._tmp("pain.jsonl"), pain_lines)
        inc = _write_jsonl(self._tmp("inc.jsonl"), inc_lines)
        r = N.evaluate(p, incident_path=inc, as_of=as_of)
        # Incident is BEFORE the executable => not in the +1h window
        self.assertAlmostEqual(r.false_positive_rate, 1.0)


# ---------------------------------------------------------------------------
# Incident-miss rate
# ---------------------------------------------------------------------------

class TestIncidentMissRate(_TempDirMixin, unittest.TestCase):

    def test_miss_zero_prior_pain(self):
        """Incident with no prior executable pain => miss."""
        as_of = "2026-08-10T12:00:00Z"
        base = datetime(2026, 8, 9, 12, 0, 0, tzinfo=timezone.utc)
        pain_lines = []  # no pain
        inc_lines = [_incident_line("i1", base)]
        p = _write_jsonl(self._tmp("pain.jsonl"), pain_lines)
        inc = _write_jsonl(self._tmp("inc.jsonl"), inc_lines)
        r = N.evaluate(p, incident_path=inc, as_of=as_of)
        self.assertIsNotNone(r.incident_miss_rate)
        self.assertAlmostEqual(r.incident_miss_rate, 1.0)

    def test_no_miss_with_prior_pain(self):
        """Incident with prior executable pain within 1h => no miss."""
        as_of = "2026-08-10T12:00:00Z"
        base = datetime(2026, 8, 9, 12, 0, 0, tzinfo=timezone.utc)
        pain_lines = [
            _pain_line("e1", base - timedelta(minutes=30), action="protective_halt", executable=True),
        ]
        inc_lines = [_incident_line("i1", base)]
        p = _write_jsonl(self._tmp("pain.jsonl"), pain_lines)
        inc = _write_jsonl(self._tmp("inc.jsonl"), inc_lines)
        r = N.evaluate(p, incident_path=inc, as_of=as_of)
        self.assertIsNotNone(r.incident_miss_rate)
        self.assertAlmostEqual(r.incident_miss_rate, 0.0)

    def test_miss_rate_no_incidents(self):
        """No incidents => miss rate None/UNKNOWN."""
        as_of = "2026-08-10T12:00:00Z"
        base = datetime(2026, 8, 9, 12, 0, 0, tzinfo=timezone.utc)
        pain_lines = [
            _pain_line("e1", base, action="protective_halt"),
        ]
        p = _write_jsonl(self._tmp("pain.jsonl"), pain_lines)
        inc = _write_jsonl(self._tmp("inc.jsonl"), [])
        r = N.evaluate(p, incident_path=inc, as_of=as_of)
        self.assertIsNone(r.incident_miss_rate)
        self.assertIn("no incidents", r.incident_miss_rate_reason)

    def test_incident_exactly_one_hour_prior(self):
        """Prior executable pain at exactly -1h should match (>=)."""
        as_of = "2026-08-10T12:00:00Z"
        base = datetime(2026, 8, 9, 12, 0, 0, tzinfo=timezone.utc)
        # Pain at exactly base - 1h
        pain_lines = [
            _pain_line("e1", base - timedelta(hours=1), action="protective_halt", executable=True),
        ]
        inc_lines = [_incident_line("i1", base)]
        p = _write_jsonl(self._tmp("pain.jsonl"), pain_lines)
        inc = _write_jsonl(self._tmp("inc.jsonl"), inc_lines)
        r = N.evaluate(p, incident_path=inc, as_of=as_of)
        # Pain at exactly -1h => should count (>=)
        self.assertAlmostEqual(r.incident_miss_rate, 0.0)

    def test_incident_just_over_one_hour_prior(self):
        """Prior pain at -1h - 1s => miss."""
        as_of = "2026-08-10T12:00:00Z"
        base = datetime(2026, 8, 9, 12, 0, 0, tzinfo=timezone.utc)
        pain_lines = [
            _pain_line("e1", base - timedelta(hours=1, seconds=1), action="protective_halt", executable=True),
        ]
        inc_lines = [_incident_line("i1", base)]
        p = _write_jsonl(self._tmp("pain.jsonl"), pain_lines)
        inc = _write_jsonl(self._tmp("inc.jsonl"), inc_lines)
        r = N.evaluate(p, incident_path=inc, as_of=as_of)
        self.assertAlmostEqual(r.incident_miss_rate, 1.0)

    def test_proposal_only_does_not_prevent_miss(self):
        """Proposal-only pain events are NOT executable, so they don't prevent miss."""
        as_of = "2026-08-10T12:00:00Z"
        base = datetime(2026, 8, 9, 12, 0, 0, tzinfo=timezone.utc)
        pain_lines = [
            _pain_line("e1", base - timedelta(minutes=30), action="proposal_only", executable=False),
        ]
        inc_lines = [_incident_line("i1", base)]
        p = _write_jsonl(self._tmp("pain.jsonl"), pain_lines)
        inc = _write_jsonl(self._tmp("inc.jsonl"), inc_lines)
        r = N.evaluate(p, incident_path=inc, as_of=as_of)
        self.assertAlmostEqual(r.incident_miss_rate, 1.0)


# ---------------------------------------------------------------------------
# Audit 5: Incident source validity
# ---------------------------------------------------------------------------

class TestIncidentSourceValidity(_TempDirMixin, unittest.TestCase):

    def test_no_incident_path(self):
        as_of = "2026-08-10T12:00:00Z"
        base = datetime(2026, 8, 9, 12, 0, 0, tzinfo=timezone.utc)
        p = _write_jsonl(self._tmp("pain.jsonl"), [
            _pain_line("e1", base, action="protective_halt"),
        ])
        r = N.evaluate(p, as_of=as_of)
        self.assertFalse(r.incident_source_valid)

    def test_empty_incident_valid(self):
        """Empty incident file => valid."""
        as_of = "2026-08-10T12:00:00Z"
        base = datetime(2026, 8, 9, 12, 0, 0, tzinfo=timezone.utc)
        p = _write_jsonl(self._tmp("pain.jsonl"), [
            _pain_line("e1", base, action="protective_halt"),
        ])
        inc = _write_jsonl(self._tmp("inc.jsonl"), [])
        r = N.evaluate(p, incident_path=inc, as_of=as_of)
        self.assertTrue(r.incident_source_valid)

    def test_valid_incident_records(self):
        as_of = "2026-08-10T12:00:00Z"
        base = datetime(2026, 8, 9, 12, 0, 0, tzinfo=timezone.utc)
        p = _write_jsonl(self._tmp("pain.jsonl"), [
            _pain_line("e1", base, action="protective_halt"),
        ])
        inc = _write_jsonl(self._tmp("inc.jsonl"), [
            _incident_line("i1", base + timedelta(minutes=10)),
        ])
        r = N.evaluate(p, incident_path=inc, as_of=as_of)
        self.assertTrue(r.incident_source_valid)

    def test_all_malformed_incident_invalid(self):
        """All-malformed incident file => invalid."""
        as_of = "2026-08-10T12:00:00Z"
        base = datetime(2026, 8, 9, 12, 0, 0, tzinfo=timezone.utc)
        p = _write_jsonl(self._tmp("pain.jsonl"), [
            _pain_line("e1", base, action="protective_halt"),
        ])
        inc = _write_jsonl(self._tmp("inc.jsonl"), ["not json", "also bad"])
        r = N.evaluate(p, incident_path=inc, as_of=as_of)
        self.assertFalse(r.incident_source_valid)
        self.assertIsNone(r.false_positive_rate)
        self.assertIn("incident source", r.false_positive_rate_reason.lower())

    def test_missing_incident_file(self):
        """Non-existent incident file path => invalid."""
        as_of = "2026-08-10T12:00:00Z"
        base = datetime(2026, 8, 9, 12, 0, 0, tzinfo=timezone.utc)
        p = _write_jsonl(self._tmp("pain.jsonl"), [
            _pain_line("e1", base, action="protective_halt"),
        ])
        r = N.evaluate(p, incident_path=self._tmp("nonexistent_inc.jsonl"), as_of=as_of)
        self.assertFalse(r.incident_source_valid)


# ---------------------------------------------------------------------------
# Ledger integrity (Audit 4: coverage, per-day JSONL)
# ---------------------------------------------------------------------------

class TestLedgerIntegrity(_TempDirMixin, unittest.TestCase):

    def _make_pain(self, as_of="2026-08-10T12:00:00Z"):
        base = datetime(2026, 8, 9, 12, 0, 0, tzinfo=timezone.utc)
        p = _write_jsonl(self._tmp("pain.jsonl"), [
            _pain_line("e1", base, action="protective_halt"),
        ])
        return p

    def test_no_ledger_path(self):
        r = N.evaluate(self._make_pain(), as_of="2026-08-10T12:00:00Z")
        self.assertIsNone(r.ledger_integrity)
        self.assertIn("no ledger path", r.ledger_integrity_reason)

    def test_ledger_json_true(self):
        ledger = _ledger_json_with_coverage(self._tmp("ledger.json"), True)
        r = N.evaluate(self._make_pain(), as_of="2026-08-10T12:00:00Z", ledger_path=ledger)
        self.assertTrue(r.ledger_integrity)
        self.assertTrue(r.ledger_source_valid)

    def test_ledger_json_false(self):
        ledger = _ledger_json_with_coverage(self._tmp("ledger.json"), False)
        r = N.evaluate(self._make_pain(), as_of="2026-08-10T12:00:00Z", ledger_path=ledger)
        self.assertFalse(r.ledger_integrity)

    def test_ledger_json_missing_field(self):
        ledger = _write_json(self._tmp("ledger.json"), {"foo": "bar"})
        r = N.evaluate(self._make_pain(), as_of="2026-08-10T12:00:00Z", ledger_path=ledger)
        self.assertIsNone(r.ledger_integrity)
        self.assertIn("missing or non-boolean", r.ledger_integrity_reason)

    def test_ledger_json_non_boolean(self):
        ledger = _write_json(self._tmp("ledger.json"), {"integrity": "yes"})
        r = N.evaluate(self._make_pain(), as_of="2026-08-10T12:00:00Z", ledger_path=ledger)
        self.assertIsNone(r.ledger_integrity)

    def test_ledger_missing_file(self):
        r = N.evaluate(self._make_pain(), as_of="2026-08-10T12:00:00Z", ledger_path=self._tmp("nonexistent.json"))
        self.assertIsNone(r.ledger_integrity)
        self.assertIn("missing or unreadable", r.ledger_integrity_reason)

    def test_ledger_jsonl_per_day_all_true(self):
        """Audit 4: JSONL with timestamped entries, all true => True."""
        # window: [2026-08-03T12:00:00Z, 2026-08-10T12:00:00Z]
        # complete days: Aug 4-9
        ledger_lines = []
        for day in range(4, 10):  # Aug 4-9
            ledger_lines.append(json.dumps({
                "ts": f"2026-08-{day:02d}T12:00:00Z",
                "integrity": True,
            }))
        ledger = _write_jsonl(self._tmp("ledger.jsonl"), ledger_lines)
        r = N.evaluate(self._make_pain(), as_of="2026-08-10T12:00:00Z", ledger_path=ledger)
        self.assertTrue(r.ledger_integrity)

    def test_ledger_jsonl_per_day_false_detected(self):
        """Audit 4: JSONL with one false day => False."""
        ledger_lines = []
        for day in range(4, 10):
            integrity = (day != 6)  # Aug 6 is False
            ledger_lines.append(json.dumps({
                "ts": f"2026-08-{day:02d}T12:00:00Z",
                "integrity": integrity,
            }))
        ledger = _write_jsonl(self._tmp("ledger.jsonl"), ledger_lines)
        r = N.evaluate(self._make_pain(), as_of="2026-08-10T12:00:00Z", ledger_path=ledger)
        self.assertFalse(r.ledger_integrity)
        self.assertIn("false", r.ledger_integrity_reason.lower())

    def test_ledger_jsonl_per_day_missing_day(self):
        """Audit 4: JSONL missing a complete day => None."""
        ledger_lines = []
        for day in [4, 5, 7, 8, 9]:  # missing Aug 6
            ledger_lines.append(json.dumps({
                "ts": f"2026-08-{day:02d}T12:00:00Z",
                "integrity": True,
            }))
        ledger = _write_jsonl(self._tmp("ledger.jsonl"), ledger_lines)
        r = N.evaluate(self._make_pain(), as_of="2026-08-10T12:00:00Z", ledger_path=ledger)
        self.assertIsNone(r.ledger_integrity)
        self.assertIn("incomplete", r.ledger_integrity_reason.lower())

    def test_ledger_jsonl_all_malformed(self):
        ledger = _write_jsonl(self._tmp("ledger.jsonl"), ["bad", "data"])
        r = N.evaluate(self._make_pain(), as_of="2026-08-10T12:00:00Z", ledger_path=ledger)
        self.assertIsNone(r.ledger_integrity)
        self.assertIn("no valid", r.ledger_integrity_reason)

    def test_ledger_alternate_field_names(self):
        for field in ("ledger_integrity", "valid", "passed"):
            ledger = _write_json(self._tmp("ledger.json"), {
                field: True,
                "coverage_start": "2026-08-03T00:00:00Z",
                "coverage_end": "2026-08-11T00:00:00Z",
            })
            r = N.evaluate(self._make_pain(), as_of="2026-08-10T12:00:00Z", ledger_path=ledger)
            self.assertTrue(r.ledger_integrity, f"field={field}")

    def test_ledger_json_coverage_too_narrow(self):
        """Audit 4: Coverage doesn't span full window => None."""
        ledger = _write_json(self._tmp("ledger.json"), {
            "integrity": True,
            "coverage_start": "2026-08-05T00:00:00Z",  # too late
            "coverage_end": "2026-08-11T00:00:00Z",
        })
        r = N.evaluate(self._make_pain(), as_of="2026-08-10T12:00:00Z", ledger_path=ledger)
        self.assertIsNone(r.ledger_integrity)
        self.assertIn("coverage", r.ledger_integrity_reason.lower())

    def test_ledger_json_no_coverage_fields(self):
        """Audit 4: JSON with integrity but no coverage => None."""
        ledger = _write_json(self._tmp("ledger.json"), {"integrity": True})
        r = N.evaluate(self._make_pain(), as_of="2026-08-10T12:00:00Z", ledger_path=ledger)
        self.assertIsNone(r.ledger_integrity)
        self.assertIn("coverage", r.ledger_integrity_reason.lower())


# ---------------------------------------------------------------------------
# Verdicts
# ---------------------------------------------------------------------------

class TestVerdictRollbackRequired(_TempDirMixin, unittest.TestCase):

    def test_forbidden_effect_triggers_rollback(self):
        as_of = "2026-08-10T12:00:00Z"
        base = datetime(2026, 8, 9, 12, 0, 0, tzinfo=timezone.utc)
        p = _write_jsonl(self._tmp("pain.jsonl"), [
            _pain_line("e1", base, action="protective_halt", executable=True, effect="forbidden"),
        ])
        r = N.evaluate(p, as_of=as_of)
        self.assertEqual(r.verdict, "ROLLBACK_REQUIRED")
        self.assertTrue(any("forbidden" in reason.lower() for reason in r.verdict_reasons))

    def test_external_effect_triggers_rollback(self):
        as_of = "2026-08-10T12:00:00Z"
        base = datetime(2026, 8, 9, 12, 0, 0, tzinfo=timezone.utc)
        p = _write_jsonl(self._tmp("pain.jsonl"), [
            _pain_line("e1", base, action="protective_halt", executable=True, effect="external"),
        ])
        r = N.evaluate(p, as_of=as_of)
        self.assertEqual(r.verdict, "ROLLBACK_REQUIRED")

    def test_ledger_false_triggers_rollback(self):
        as_of = "2026-08-10T12:00:00Z"
        base = datetime(2026, 8, 9, 12, 0, 0, tzinfo=timezone.utc)
        p = _write_jsonl(self._tmp("pain.jsonl"), [
            _pain_line("e1", base, action="protective_halt", executable=True),
        ])
        ledger = _ledger_json_with_coverage(self._tmp("ledger.json"), False)
        r = N.evaluate(p, ledger_path=ledger, as_of=as_of)
        self.assertEqual(r.verdict, "ROLLBACK_REQUIRED")
        self.assertTrue(any("ledger" in reason.lower() for reason in r.verdict_reasons))

    def test_fp_rate_two_consecutive_days_triggers_rollback(self):
        """fp_rate > 0.5 on two consecutive UTC days => ROLLBACK_REQUIRED.
        Audit 6: needs valid incident source (empty file)."""
        as_of = "2026-08-10T00:00:00Z"
        # Day 1: 2026-08-08, Day 2: 2026-08-09 (consecutive)
        day1 = datetime(2026, 8, 8, 12, 0, 0, tzinfo=timezone.utc)
        day2 = datetime(2026, 8, 9, 12, 0, 0, tzinfo=timezone.utc)
        # Empty incident file => valid, no incidents => every executable is a false positive
        pain_lines = [
            _pain_line("e1", day1, action="protective_halt", executable=True),
            _pain_line("e2", day2, action="protective_halt", executable=True),
        ]
        p = _write_jsonl(self._tmp("pain.jsonl"), pain_lines)
        inc = _write_jsonl(self._tmp("inc.jsonl"), [])
        r = N.evaluate(p, incident_path=inc, as_of=as_of)
        self.assertEqual(r.verdict, "ROLLBACK_REQUIRED")
        self.assertTrue(
            any("consecutive" in reason.lower() for reason in r.verdict_reasons),
            f"Expected consecutive-day reason, got: {r.verdict_reasons}",
        )

    def test_fp_rate_one_day_no_rollback(self):
        """fp_rate > 0.5 on one day only => not rollback for this rule."""
        as_of = "2026-08-10T00:00:00Z"
        day1 = datetime(2026, 8, 8, 12, 0, 0, tzinfo=timezone.utc)
        pain_lines = [
            _pain_line("e1", day1, action="protective_halt", executable=True),
        ]
        p = _write_jsonl(self._tmp("pain.jsonl"), pain_lines)
        inc = _write_jsonl(self._tmp("inc.jsonl"), [])
        r = N.evaluate(p, incident_path=inc, as_of=as_of)
        # Should NOT be ROLLBACK_REQUIRED (no forbidden, ledger unknown,
        # and only 1 day with high FP, not 2 consecutive)
        self.assertNotEqual(r.verdict, "ROLLBACK_REQUIRED")

    def test_fp_rate_non_consecutive_days(self):
        """fp_rate > 0.5 on non-consecutive days => not rollback for this rule."""
        as_of = "2026-08-10T00:00:00Z"
        day1 = datetime(2026, 8, 6, 12, 0, 0, tzinfo=timezone.utc)
        day2 = datetime(2026, 8, 8, 12, 0, 0, tzinfo=timezone.utc)  # skip day 7
        pain_lines = [
            _pain_line("e1", day1, action="protective_halt", executable=True),
            _pain_line("e2", day2, action="protective_halt", executable=True),
        ]
        p = _write_jsonl(self._tmp("pain.jsonl"), pain_lines)
        inc = _write_jsonl(self._tmp("inc.jsonl"), [])
        r = N.evaluate(p, incident_path=inc, as_of=as_of)
        self.assertNotEqual(r.verdict, "ROLLBACK_REQUIRED")


class TestVerdictKeepArmed(_TempDirMixin, unittest.TestCase):
    """KEEP_ARMED requires >= 7 complete days, fp < 0.3, miss < 0.2,
    ledger true, zero forbidden."""

    def test_keep_armed_full(self):
        """Construct a scenario meeting all KEEP_ARMED criteria."""
        as_of = "2026-08-12T00:00:00Z"  # window: Aug 5 - Aug 12
        # Create 7 days of data, each with executable events + matching incidents
        pain_lines = []
        inc_lines = []
        for day_offset in range(7):
            day = datetime(2026, 8, 5 + day_offset, 12, 0, 0, tzinfo=timezone.utc)
            eid = f"e{day_offset}"
            iid = f"i{day_offset}"
            pain_lines.append(_pain_line(eid, day, action="protective_halt", executable=True, effect="internal"))
            inc_lines.append(_incident_line(iid, day + timedelta(minutes=10)))

        p = _write_jsonl(self._tmp("pain.jsonl"), pain_lines)
        inc = _write_jsonl(self._tmp("inc.jsonl"), inc_lines)
        ledger = _write_json(self._tmp("ledger.json"), {
            "integrity": True,
            "coverage_start": "2026-08-05T00:00:00Z",
            "coverage_end": "2026-08-12T00:00:00Z",
        })

        r = N.evaluate(p, incident_path=inc, ledger_path=ledger, as_of=as_of)
        self.assertEqual(r.verdict, "KEEP_ARMED", f"Got {r.verdict}: {r.verdict_reasons}")
        self.assertAlmostEqual(r.false_positive_rate, 0.0)
        self.assertAlmostEqual(r.incident_miss_rate, 0.0)
        self.assertEqual(r.complete_days, 7)

    def test_keep_armed_missing_7_days(self):
        """Non-midnight as_of => < 7 complete days => INSUFFICIENT_EVIDENCE."""
        as_of = "2026-08-10T12:00:00Z"
        # complete_days = 6 (Aug 4-9), not 7
        pain_lines = []
        inc_lines = []
        for d in range(6):
            day = datetime(2026, 8, 4 + d, 12, 0, 0, tzinfo=timezone.utc)
            pain_lines.append(_pain_line(f"e{d}", day, action="protective_halt"))
            inc_lines.append(_incident_line(f"i{d}", day + timedelta(minutes=10)))
        p = _write_jsonl(self._tmp("pain.jsonl"), pain_lines)
        inc = _write_jsonl(self._tmp("inc.jsonl"), inc_lines)
        ledger = _ledger_json_with_coverage(self._tmp("ledger.json"), True)
        r = N.evaluate(p, incident_path=inc, ledger_path=ledger, as_of=as_of)
        self.assertEqual(r.verdict, "INSUFFICIENT_EVIDENCE")
        self.assertTrue(
            any("complete" in reason.lower() for reason in r.verdict_reasons),
            f"Expected complete-day reason, got: {r.verdict_reasons}",
        )

    def test_keep_armed_no_incident_source(self):
        """Audit 6: No incident source => FP/miss UNKNOWN => INSUFFICIENT."""
        as_of = "2026-08-12T00:00:00Z"
        pain_lines = []
        for d in range(7):
            day = datetime(2026, 8, 5 + d, 12, 0, 0, tzinfo=timezone.utc)
            pain_lines.append(_pain_line(f"e{d}", day, action="protective_halt"))
        p = _write_jsonl(self._tmp("pain.jsonl"), pain_lines)
        ledger = _write_json(self._tmp("ledger.json"), {
            "integrity": True,
            "coverage_start": "2026-08-05T00:00:00Z",
            "coverage_end": "2026-08-12T00:00:00Z",
        })
        r = N.evaluate(p, ledger_path=ledger, as_of=as_of)
        # No incident source => FP=UNKNOWN, miss=UNKNOWN => INSUFFICIENT_EVIDENCE
        self.assertEqual(r.verdict, "INSUFFICIENT_EVIDENCE")

    def test_keep_armed_fp_too_high(self):
        """FP rate >= 0.3 => INSUFFICIENT_EVIDENCE."""
        as_of = "2026-08-12T00:00:00Z"
        pain_lines = []
        inc_lines = []
        for d in range(7):
            day = datetime(2026, 8, 5 + d, 12, 0, 0, tzinfo=timezone.utc)
            # 10 events, only 6 have incidents => fp = 4/10 = 0.4
            for i in range(10):
                pain_lines.append(_pain_line(f"e{d}_{i}", day + timedelta(minutes=i), action="protective_halt"))
            for i in range(6):
                inc_lines.append(_incident_line(f"i{d}_{i}", day + timedelta(minutes=i) + timedelta(seconds=30)))
        p = _write_jsonl(self._tmp("pain.jsonl"), pain_lines)
        inc = _write_jsonl(self._tmp("inc.jsonl"), inc_lines)
        ledger = _write_json(self._tmp("ledger.json"), {
            "integrity": True,
            "coverage_start": "2026-08-05T00:00:00Z",
            "coverage_end": "2026-08-12T00:00:00Z",
        })
        r = N.evaluate(p, incident_path=inc, ledger_path=ledger, as_of=as_of)
        self.assertEqual(r.verdict, "INSUFFICIENT_EVIDENCE")
        # fp rate should be > 0.3
        self.assertIsNotNone(r.false_positive_rate)
        self.assertGreater(r.false_positive_rate, 0.3)

    def test_keep_armed_ledger_unknown(self):
        """Ledger unknown => INSUFFICIENT_EVIDENCE."""
        as_of = "2026-08-12T00:00:00Z"
        pain_lines = []
        inc_lines = []
        for d in range(7):
            day = datetime(2026, 8, 5 + d, 12, 0, 0, tzinfo=timezone.utc)
            pain_lines.append(_pain_line(f"e{d}", day, action="protective_halt"))
            inc_lines.append(_incident_line(f"i{d}", day + timedelta(minutes=10)))
        p = _write_jsonl(self._tmp("pain.jsonl"), pain_lines)
        inc = _write_jsonl(self._tmp("inc.jsonl"), inc_lines)
        # No ledger path
        r = N.evaluate(p, incident_path=inc, as_of=as_of)
        self.assertEqual(r.verdict, "INSUFFICIENT_EVIDENCE")

    def test_keep_armed_forbidden_prevents(self):
        """Any forbidden effect prevents KEEP_ARMED."""
        as_of = "2026-08-12T00:00:00Z"
        pain_lines = []
        inc_lines = []
        for d in range(6):
            day = datetime(2026, 8, 5 + d, 12, 0, 0, tzinfo=timezone.utc)
            pain_lines.append(_pain_line(f"e{d}", day, action="protective_halt", effect="internal"))
            inc_lines.append(_incident_line(f"i{d}", day + timedelta(minutes=10)))
        # Add a forbidden one
        day6 = datetime(2026, 8, 11, 12, 0, 0, tzinfo=timezone.utc)
        pain_lines.append(_pain_line("e_forbidden", day6, action="protective_halt", effect="forbidden"))

        p = _write_jsonl(self._tmp("pain.jsonl"), pain_lines)
        inc = _write_jsonl(self._tmp("inc.jsonl"), inc_lines)
        ledger = _write_json(self._tmp("ledger.json"), {
            "integrity": True,
            "coverage_start": "2026-08-05T00:00:00Z",
            "coverage_end": "2026-08-12T00:00:00Z",
        })
        r = N.evaluate(p, incident_path=inc, ledger_path=ledger, as_of=as_of)
        self.assertEqual(r.verdict, "ROLLBACK_REQUIRED")


class TestVerdictInsufficient(_TempDirMixin, unittest.TestCase):

    def test_partial_days(self):
        """Non-midnight as_of + 3 days data => INSUFFICIENT_EVIDENCE."""
        as_of = "2026-08-10T12:00:00Z"
        pain_lines = [
            _pain_line("e0", datetime(2026, 8, 7, 12, 0, 0, tzinfo=timezone.utc)),
            _pain_line("e1", datetime(2026, 8, 8, 12, 0, 0, tzinfo=timezone.utc)),
            _pain_line("e2", datetime(2026, 8, 9, 12, 0, 0, tzinfo=timezone.utc)),
        ]
        # Provide matching incidents so FP rate stays low
        inc_lines = [
            _incident_line("i0", datetime(2026, 8, 7, 12, 10, 0, tzinfo=timezone.utc)),
            _incident_line("i1", datetime(2026, 8, 8, 12, 10, 0, tzinfo=timezone.utc)),
            _incident_line("i2", datetime(2026, 8, 9, 12, 10, 0, tzinfo=timezone.utc)),
        ]
        p = _write_jsonl(self._tmp("pain.jsonl"), pain_lines)
        inc = _write_jsonl(self._tmp("inc.jsonl"), inc_lines)
        # Ledger without coverage => None => INSUFFICIENT
        ledger = _write_json(self._tmp("ledger.json"), {"integrity": True})
        r = N.evaluate(p, incident_path=inc, ledger_path=ledger, as_of=as_of)
        self.assertEqual(r.verdict, "INSUFFICIENT_EVIDENCE")
        self.assertEqual(r.days_with_data, 3)


# ---------------------------------------------------------------------------
# Daily FP rate tracking
# ---------------------------------------------------------------------------

class TestDailyFPRate(_TempDirMixin, unittest.TestCase):

    def test_daily_fp_rate_populated(self):
        as_of = "2026-08-10T00:00:00Z"
        day1 = datetime(2026, 8, 8, 12, 0, 0, tzinfo=timezone.utc)
        day2 = datetime(2026, 8, 9, 12, 0, 0, tzinfo=timezone.utc)
        pain_lines = [
            _pain_line("e1", day1, action="protective_halt", executable=True),
            _pain_line("e2", day2, action="protective_halt", executable=True),
        ]
        p = _write_jsonl(self._tmp("pain.jsonl"), pain_lines)
        # Empty incident file (valid, no incidents)
        inc = _write_jsonl(self._tmp("inc.jsonl"), [])
        r = N.evaluate(p, incident_path=inc, as_of=as_of)
        self.assertIn("2026-08-08", r.daily_fp_rate)
        self.assertIn("2026-08-09", r.daily_fp_rate)
        # No incidents => all fp
        self.assertAlmostEqual(r.daily_fp_rate["2026-08-08"], 1.0)
        self.assertAlmostEqual(r.daily_fp_rate["2026-08-09"], 1.0)

    def test_days_with_complete_fp_tracking(self):
        as_of = "2026-08-10T00:00:00Z"
        day1 = datetime(2026, 8, 8, 12, 0, 0, tzinfo=timezone.utc)
        day2 = datetime(2026, 8, 9, 12, 0, 0, tzinfo=timezone.utc)
        pain_lines = [
            _pain_line("e1", day1, action="protective_halt", executable=True),
            # Day 2: only proposal-only (no executable)
            _pain_line("e2", day2, action="proposal_only", executable=False),
        ]
        p = _write_jsonl(self._tmp("pain.jsonl"), pain_lines)
        inc = _write_jsonl(self._tmp("inc.jsonl"), [])
        r = N.evaluate(p, incident_path=inc, as_of=as_of)
        # Only day1 has executable events => 1 complete
        self.assertEqual(r.days_with_complete_fp_tracking, 1)


# ---------------------------------------------------------------------------
# Coverage metadata
# ---------------------------------------------------------------------------

class TestCoverageMetadata(_TempDirMixin, unittest.TestCase):

    def test_first_last_ts(self):
        as_of = "2026-08-10T12:00:00Z"
        t1 = datetime(2026, 8, 8, 10, 0, 0, tzinfo=timezone.utc)
        t2 = datetime(2026, 8, 9, 14, 0, 0, tzinfo=timezone.utc)
        pain_lines = [
            _pain_line("e2", t2, action="throttle"),
            _pain_line("e1", t1, action="protective_halt"),
        ]
        p = _write_jsonl(self._tmp("pain.jsonl"), pain_lines)
        r = N.evaluate(p, as_of=as_of)
        self.assertEqual(r.first_record_ts, t1.isoformat())
        self.assertEqual(r.last_record_ts, t2.isoformat())


# ---------------------------------------------------------------------------
# Timestamp robustness
# ---------------------------------------------------------------------------

class TestTimestampRobustness(_TempDirMixin, unittest.TestCase):

    def test_epoch_timestamps_in_pain(self):
        """Pain records with epoch timestamps parse correctly."""
        as_of = "2026-08-10T00:00:00Z"
        dt = datetime(2026, 8, 9, 12, 0, 0, tzinfo=timezone.utc)
        epoch = str(int(dt.timestamp()))
        p = _write_jsonl(self._tmp("pain.jsonl"), [
            json.dumps({"event_id": "e1", "ts": epoch, "action": "protective_halt", "executable": True, "effect": "internal"}),
        ])
        r = N.evaluate(p, as_of=as_of)
        self.assertEqual(r.records_in_window, 1)
        self.assertEqual(r.executable_protective_halt_count, 1)

    def test_microsecond_precision(self):
        """Records with microsecond timestamps are parsed."""
        as_of = "2026-08-10T00:00:00Z"
        line = json.dumps({
            "event_id": "e1",
            "ts": "2026-08-09T12:00:00.123Z",
            "action": "protective_halt",
            "executable": True,
            "effect": "internal",
        })
        p = _write_jsonl(self._tmp("pain.jsonl"), [line])
        r = N.evaluate(p, as_of=as_of)
        self.assertEqual(r.records_in_window, 1)

    def test_offset_timestamps_in_pain(self):
        """Audit 8: Pain records with non-zero ISO offsets parse correctly."""
        as_of = "2026-08-10T00:00:00Z"
        # 2026-08-09T12:00:00Z == 2026-08-09T17:30:00+05:30
        line = json.dumps({
            "event_id": "e1",
            "ts": "2026-08-09T17:30:00+05:30",
            "action": "protective_halt",
            "executable": True,
            "effect": "internal",
        })
        p = _write_jsonl(self._tmp("pain.jsonl"), [line])
        r = N.evaluate(p, as_of=as_of)
        self.assertEqual(r.records_in_window, 1)
        self.assertEqual(r.executable_protective_halt_count, 1)


# ---------------------------------------------------------------------------
# Formatting
# ---------------------------------------------------------------------------

class TestFormatting(_TempDirMixin, unittest.TestCase):

    def test_format_json(self):
        as_of = "2026-08-10T12:00:00Z"
        base = datetime(2026, 8, 9, 12, 0, 0, tzinfo=timezone.utc)
        p = _write_jsonl(self._tmp("pain.jsonl"), [
            _pain_line("e1", base, action="protective_halt"),
        ])
        r = N.evaluate(p, as_of=as_of)
        j = N._format_json(r)
        parsed = json.loads(j)
        self.assertEqual(parsed["verdict"], "INSUFFICIENT_EVIDENCE")
        self.assertIn("executable_protective_halt_count", parsed)
        # Audit 3: complete_days field present
        self.assertIn("complete_days", parsed)

    def test_format_markdown(self):
        as_of = "2026-08-10T12:00:00Z"
        base = datetime(2026, 8, 9, 12, 0, 0, tzinfo=timezone.utc)
        p = _write_jsonl(self._tmp("pain.jsonl"), [
            _pain_line("e1", base, action="protective_halt"),
        ])
        r = N.evaluate(p, as_of=as_of)
        md = N._format_markdown(r)
        self.assertIn("# Neural APPLY Evidence Report", md)
        self.assertIn("INSUFFICIENT_EVIDENCE", md)
        self.assertIn("## Raw Counters", md)
        # Audit 3: complete_days in markdown
        self.assertIn("complete_days", md)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

class TestCLI(_TempDirMixin, unittest.TestCase):

    def test_cli_json_stdout(self):
        as_of = "2026-08-10T12:00:00Z"
        base = datetime(2026, 8, 9, 12, 0, 0, tzinfo=timezone.utc)
        p = _write_jsonl(self._tmp("pain.jsonl"), [
            _pain_line("e1", base, action="protective_halt"),
        ])
        old_stdout = sys.stdout
        sys.stdout = buf = StringIO()
        try:
            N.main(["--pain", str(p), "--as-of", as_of, "--format", "json"])
        finally:
            sys.stdout = old_stdout
        output = buf.getvalue()
        parsed = json.loads(output)
        self.assertEqual(parsed["verdict"], "INSUFFICIENT_EVIDENCE")

    def test_cli_out_file(self):
        as_of = "2026-08-10T12:00:00Z"
        base = datetime(2026, 8, 9, 12, 0, 0, tzinfo=timezone.utc)
        p = _write_jsonl(self._tmp("pain.jsonl"), [
            _pain_line("e1", base, action="protective_halt"),
        ])
        out_path = self._tmp("report.json")
        N.main(["--pain", str(p), "--as-of", as_of, "--format", "json", "--out", str(out_path)])
        self.assertTrue(out_path.exists())
        data = json.loads(out_path.read_text(encoding="utf-8"))
        self.assertIn("verdict", data)

    def test_cli_markdown_out(self):
        as_of = "2026-08-10T12:00:00Z"
        base = datetime(2026, 8, 9, 12, 0, 0, tzinfo=timezone.utc)
        p = _write_jsonl(self._tmp("pain.jsonl"), [
            _pain_line("e1", base, action="protective_halt"),
        ])
        out_path = self._tmp("report.md")
        N.main(["--pain", str(p), "--as-of", as_of, "--format", "markdown", "--out", str(out_path)])
        self.assertTrue(out_path.exists())
        md = out_path.read_text(encoding="utf-8")
        self.assertIn("# Neural APPLY Evidence Report", md)


# ---------------------------------------------------------------------------
# Deterministic ordering
# ---------------------------------------------------------------------------

class TestDeterministicOrdering(_TempDirMixin, unittest.TestCase):

    def test_records_sorted_by_ts_id(self):
        as_of = "2026-08-10T12:00:00Z"
        base = datetime(2026, 8, 9, 12, 0, 0, tzinfo=timezone.utc)
        # Insert in reverse order
        pain_lines = [
            _pain_line("e3", base + timedelta(minutes=20), action="protective_halt"),
            _pain_line("e1", base, action="protective_halt"),
            _pain_line("e2", base + timedelta(minutes=10), action="throttle"),
        ]
        p = _write_jsonl(self._tmp("pain.jsonl"), pain_lines)
        r = N.evaluate(p, as_of=as_of)
        # first should be e1, last should be e3
        self.assertEqual(r.first_record_ts, "2026-08-09T12:00:00+00:00")
        self.assertEqual(r.executable_protective_halt_count, 2)  # e1 and e3
        self.assertEqual(r.executable_throttle_count, 1)


# ---------------------------------------------------------------------------
# NaN / malformed handling (Audit 9: no double-counting)
# ---------------------------------------------------------------------------

class TestMalformedHandling(_TempDirMixin, unittest.TestCase):

    def test_nan_action_not_coerced(self):
        """A record with unrecognised action is valid (not malformed)."""
        as_of = "2026-08-10T12:00:00Z"
        base = datetime(2026, 8, 9, 12, 0, 0, tzinfo=timezone.utc)
        line = json.dumps({
            "event_id": "e_nan",
            "ts": _ts(base),
            "action": "NaN",
            "executable": True,
            "effect": "internal",
        })
        p = _write_jsonl(self._tmp("pain.jsonl"), [line])
        r = N.evaluate(p, as_of=as_of)
        # NaN action => "unknown" action but valid parse => NOT malformed
        self.assertEqual(r.unknown_malformed_count, 0)
        self.assertEqual(r.executable_total, 1)  # still counted as executable

    def test_malformed_lines_never_coerced(self):
        """Malformed JSON lines are counted separately, never zero."""
        as_of = "2026-08-10T12:00:00Z"
        base = datetime(2026, 8, 9, 12, 0, 0, tzinfo=timezone.utc)
        pain_lines = [
            _pain_line("e1", base, action="protective_halt", executable=True),
            "BROKEN LINE",
            '{"event_id": "e2", "ts": "not-a-date", "action": "halt"}',
        ]
        p = _write_jsonl(self._tmp("pain.jsonl"), pain_lines)
        r = N.evaluate(p, as_of=as_of)
        # e1 is valid, "BROKEN LINE" is malformed, e2 has bad timestamp => malformed
        self.assertEqual(r.unknown_malformed_count, 2)
        self.assertEqual(r.executable_protective_halt_count, 1)

    def test_unknown_action_non_executable_not_double_counted(self):
        """Audit 9: unknown-action non-executable records NOT counted in
        unknown_malformed_count."""
        as_of = "2026-08-10T12:00:00Z"
        base = datetime(2026, 8, 9, 12, 0, 0, tzinfo=timezone.utc)
        line = json.dumps({
            "event_id": "e_unk",
            "ts": _ts(base),
            "action": "bogus",
            "executable": False,
            "effect": "internal",
        })
        p = _write_jsonl(self._tmp("pain.jsonl"), [line])
        r = N.evaluate(p, as_of=as_of)
        self.assertEqual(r.unknown_malformed_count, 0)
        self.assertEqual(r.executable_total, 0)


# ---------------------------------------------------------------------------
# to_dict round-trip
# ---------------------------------------------------------------------------

class TestToDict(unittest.TestCase):

    def test_round_trip(self):
        r = N.EvidenceReport(
            window_days=7,
            verdict="INSUFFICIENT_EVIDENCE",
            verdict_reasons=["test"],
            complete_days=3,
        )
        d = r.to_dict()
        self.assertEqual(d["window_days"], 7)
        self.assertEqual(d["verdict"], "INSUFFICIENT_EVIDENCE")
        self.assertEqual(d["verdict_reasons"], ["test"])
        self.assertEqual(d["complete_days"], 3)


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

def _run_all() -> bool:
    """Run all tests; return True on success."""
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromModule(sys.modules[__name__])
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    return result.wasSuccessful()


if __name__ == "__main__":
    ok = _run_all()
    sys.exit(0 if ok else 1)
