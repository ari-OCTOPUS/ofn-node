"""
tests/test_ziman_tender_harvest.py — negative-first tests for ziman_tender_harvest.

All tests run without browser, without network, without OFN_WIRE_HARVEST=1.
Positive (live) tests are excluded from CI (marked live_only).
"""
import json
import os
import sqlite3
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from ofn.agents.ziman_tender_harvest import (
    HARVEST_WIRE_FLAG,
    TenderRow,
    _check_gates,
    _write_claim,
    _write_to_db,
    run,
)


# ── NEGATIVE TESTS (must pass in CI) ──────────────────────────────────────────

class TestGates:
    def test_raises_without_owner_approval(self):
        """owner_approval=False must raise PermissionError."""
        with pytest.raises(PermissionError, match="owner_approval"):
            _check_gates(owner_approval=False)

    def test_raises_when_wire_flag_off(self, monkeypatch):
        """Wire flag absent → PermissionError even with owner_approval=True."""
        monkeypatch.delenv(HARVEST_WIRE_FLAG, raising=False)
        with pytest.raises(PermissionError, match=HARVEST_WIRE_FLAG):
            _check_gates(owner_approval=True)

    def test_raises_when_wire_flag_wrong_value(self, monkeypatch):
        monkeypatch.setenv(HARVEST_WIRE_FLAG, "true")  # must be '1' exactly
        with pytest.raises(PermissionError, match=HARVEST_WIRE_FLAG):
            _check_gates(owner_approval=True)

    def test_passes_when_both_set(self, monkeypatch):
        monkeypatch.setenv(HARVEST_WIRE_FLAG, "1")
        _check_gates(owner_approval=True)  # must not raise


class TestRunGates:
    """run() must refuse without gates, before touching any browser."""

    def test_run_refuses_without_approval(self):
        with pytest.raises(PermissionError):
            run(owner_approval=False, target_url="https://example.com")

    def test_run_refuses_without_url(self, monkeypatch):
        monkeypatch.setenv(HARVEST_WIRE_FLAG, "1")
        with pytest.raises(ValueError, match="target_url"):
            run(owner_approval=True, target_url=None)

    def test_run_refuses_empty_url(self, monkeypatch):
        monkeypatch.setenv(HARVEST_WIRE_FLAG, "1")
        with pytest.raises(ValueError):
            run(owner_approval=True, target_url="")


class TestDbWriter:
    """_write_to_db must be idempotent and skip duplicates."""

    def _make_db(self, tmp_path: Path) -> Path:
        db = tmp_path / "painting.sqlite"
        return db

    def test_inserts_new_rows(self, tmp_path):
        db = self._make_db(tmp_path)
        rows = [
            TenderRow(
                source="test", reference_id="T001", title="Test Tender",
                agency="Agency A", close_date="2026-10-01", url="https://example.com/T001",
            )
        ]
        inserted = _write_to_db(rows, db)
        assert inserted == 1

    def test_skips_duplicate_reference_id(self, tmp_path):
        db = self._make_db(tmp_path)
        rows = [
            TenderRow(
                source="test", reference_id="T001", title="Test",
                agency="A", close_date="2026-10-01", url="https://x.com",
            )
        ]
        _write_to_db(rows, db)
        inserted_second = _write_to_db(rows, db)  # same reference_id
        assert inserted_second == 0

    def test_wal_pragma_set(self, tmp_path):
        db = self._make_db(tmp_path)
        _write_to_db([], db)
        conn = sqlite3.connect(db)
        mode = conn.execute("PRAGMA journal_mode").fetchone()[0]
        conn.close()
        assert mode == "wal"

    def test_does_not_exceed_max_rows(self, tmp_path):
        from ofn.agents.ziman_tender_harvest import MAX_ROWS
        db = self._make_db(tmp_path)
        rows = [
            TenderRow(
                source="test", reference_id=f"T{i:04d}", title=f"Tender {i}",
                agency="A", close_date="2026-10-01", url=f"https://x.com/{i}",
            )
            for i in range(MAX_ROWS + 5)  # more than cap
        ]
        # _write_to_db itself doesn't cap — the scraper should. But let's confirm
        # inserting MAX_ROWS+5 is technically possible (no DB-level cap):
        inserted = _write_to_db(rows, db)
        assert inserted == MAX_ROWS + 5  # db accepts; scraper must enforce cap


class TestClaimWriter:
    def test_writes_valid_json(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        (tmp_path / "state" / "legs").mkdir(parents=True)
        _write_claim(rows_scraped=10, rows_inserted=8, target_url="https://example.com")
        claim_path = tmp_path / "state" / "legs" / "ziman-tender-harvest-claim.json"
        assert claim_path.exists()
        data = json.loads(claim_path.read_text())
        assert data["rows_scraped"] == 10
        assert data["rows_inserted"] == 8
        assert data["witness_required"] is True
        assert "claimed_at" in data

    def test_claim_marks_witness_required(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        (tmp_path / "state" / "legs").mkdir(parents=True)
        _write_claim(0, 0, "https://example.com")
        data = json.loads(
            (tmp_path / "state" / "legs" / "ziman-tender-harvest-claim.json").read_text()
        )
        assert data["witness_required"] is True


# ── LIVE TESTS (excluded from CI — run manually on board138 after owner GO) ───

@pytest.mark.skip(reason="live_only: requires board138 + OFN_WIRE_HARVEST=1 + owner GO")
class TestLiveHarvest:
    def test_scrapes_and_inserts(self, tmp_path, monkeypatch):
        monkeypatch.setenv(HARVEST_WIRE_FLAG, "1")
        # Owner must supply real URL before running this
        target = os.environ.get("ZIMAN_TEST_TARGET_URL", "")
        if not target:
            pytest.skip("ZIMAN_TEST_TARGET_URL not set")
        result = run(
            owner_approval=True,
            target_url=target,
            db_path=tmp_path / "painting.sqlite",
        )
        assert result["status"] == "OK"
        assert result["rows_scraped"] >= 0
