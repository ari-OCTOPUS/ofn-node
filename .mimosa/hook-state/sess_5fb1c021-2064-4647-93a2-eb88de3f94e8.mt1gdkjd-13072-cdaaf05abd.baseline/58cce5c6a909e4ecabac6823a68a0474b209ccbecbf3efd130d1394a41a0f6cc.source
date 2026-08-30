#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_owner_cockpit_db.py — WP2 + WP3 تست‌های OTel + SQLite + audit chain."""
import json
import os
import sys
import tempfile
from pathlib import Path

import pytest

_HERE = Path(__file__).resolve().parent
_OPS = _HERE.parent
if str(_OPS) not in sys.path:
    sys.path.insert(0, str(_OPS))


@pytest.fixture
def armed_env(monkeypatch, tmp_path):
    """flagها را روشن و DB/traces path را به tmp_path منتقل کن."""
    monkeypatch.setenv("OCTOPUS_WIRE_OWNER_DB", "1")
    monkeypatch.setenv("OCTOPUS_WIRE_OTEL", "1")
    import owner_cockpit.db as db
    import owner_cockpit.otel_setup as otel
    monkeypatch.setattr(db, "DB_PATH", tmp_path / "test.db")
    monkeypatch.setattr(otel, "TRACES_FILE", tmp_path / "traces.jsonl")
    return tmp_path


class TestSpan:
    """WP2: OTel span."""

    def test_span_creates_and_finishes(self, armed_env):
        from owner_cockpit.otel_setup import start_span
        with start_span("test.call", model="fugu-ultra") as span:
            span.set_attr("input_tokens", 100)
        assert span.end_ms is not None
        assert span.status == "ok"

    def test_span_error_captured(self, armed_env):
        from owner_cockpit.otel_setup import start_span
        with pytest.raises(ValueError):
            with start_span("test.fail") as span:
                raise ValueError("test error")
        assert span.status == "error"
        assert "ValueError" in span.error

    def test_span_written_to_file(self, armed_env):
        from owner_cockpit.otel_setup import start_span, read_traces, TRACES_FILE
        with start_span("test.write", model="fugu") as s:
            s.set_attr("cost", 0.01)
        traces = read_traces(10)
        assert len(traces) >= 1
        last = traces[-1]
        assert last["name"] == "test.write"
        assert last["attributes"]["model"] == "fugu"


class TestProviderUsage:
    """WP3: provider_usage table."""

    def test_log_provider_usage(self, armed_env):
        from owner_cockpit.db import log_provider_usage, get_db
        rowid = log_provider_usage(
            model="fugu-ultra", task="classify", tier="primary",
            usage={"input_tokens": 100, "output_tokens": 50,
                   "total_tokens": 150, "total_cost_usd": 0.002},
            latency_ms=250, status="ok",
        )
        assert rowid is not None and rowid > 0
        conn = get_db()
        row = conn.execute("SELECT * FROM provider_usage WHERE id=?", (rowid,)).fetchone()
        conn.close()
        assert row["model"] == "fugu-ultra"
        assert row["input_tokens"] == 100
        assert row["cost_usd"] == 0.002

    def test_usage_flag_off_returns_none(self, monkeypatch):
        monkeypatch.delenv("OCTOPUS_WIRE_OWNER_DB", raising=False)
        from owner_cockpit.db import log_provider_usage
        assert log_provider_usage(model="x") is None


class TestAuditLedger:
    """WP3: audit_ledger hash-chained — tamper detection."""

    def test_chain_starts_empty(self, armed_env):
        from owner_cockpit.db import verify_chain
        valid, broken = verify_chain()
        assert valid and broken == 0

    def test_append_and_verify(self, armed_env):
        from owner_cockpit.db import audit_append, verify_chain
        h1 = audit_append("confirm", target="proposal-1", payload={"id": 1})
        h2 = audit_append("confirm", target="proposal-2", payload={"id": 2})
        assert h1 and h2
        valid, broken = verify_chain()
        assert valid, f"chain broken at {broken}"

    def test_tamper_detected(self, armed_env):
        from owner_cockpit.db import audit_append, verify_chain, get_db
        audit_append("confirm", target="p1", payload={"id": 1})
        audit_append("confirm", target="p2", payload={"id": 2})
        audit_append("confirm", target="p3", payload={"id": 3})

        # tamper: رکوردِ وسط را تغییر بده
        conn = get_db()
        conn.execute("UPDATE audit_ledger SET target='HACKED' WHERE id=2")
        conn.commit()
        conn.close()

        valid, broken = verify_chain()
        assert not valid
        assert broken == 2 or broken == 3  # tamper در id=2 کشف می‌شود


class TestOwnerSessions:
    """WP4: owner_sessions."""

    def test_create_and_verify(self, armed_env):
        from owner_cockpit.db import create_session, verify_session
        create_session("hash123", "owner-1", "2099-01-01T00:00:00Z")
        valid, owner = verify_session("hash123")
        assert valid
        assert owner == "owner-1"

    def test_expired_session_invalid(self, armed_env):
        from owner_cockpit.db import create_session, verify_session
        create_session("hash-exp", "owner-1", "2020-01-01T00:00:00Z")
        valid, _ = verify_session("hash-exp")
        assert not valid

    def test_revoked_session_invalid(self, armed_env):
        from owner_cockpit.db import create_session, verify_session, revoke_session
        create_session("hash-rev", "owner-1", "2099-01-01T00:00:00Z")
        revoke_session("hash-rev")
        valid, _ = verify_session("hash-rev")
        assert not valid

    def test_unknown_session_invalid(self, armed_env):
        from owner_cockpit.db import verify_session
        valid, _ = verify_session("nonexistent")
        assert not valid
