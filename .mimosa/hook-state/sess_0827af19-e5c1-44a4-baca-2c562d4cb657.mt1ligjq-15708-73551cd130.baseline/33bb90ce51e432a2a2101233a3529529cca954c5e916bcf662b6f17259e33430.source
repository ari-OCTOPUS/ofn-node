"""Tests for verdict_stream.py."""
import csv
import json
import tempfile
from pathlib import Path

import pytest

import sys
sys.path.insert(0, str(Path("F:/backup/03 - Projects/research-spec-compiler/body_bridge").resolve()))

import verdict_stream as vs


@pytest.fixture
def temp_env(monkeypatch):
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        out_dir = root / "output"
        out_dir.mkdir()
        ledger = root / "CLAIMS_LEDGER.csv"
        cursor = out_dir / ".verdict_cursor"
        jsonl = out_dir / "verdict_stream.jsonl"

        monkeypatch.setattr(vs, "OUTPUT_DIR", out_dir)
        monkeypatch.setattr(vs, "CLAIMS_LEDGER", ledger)
        monkeypatch.setattr(vs, "CURSOR_FILE", cursor)
        monkeypatch.setattr(vs, "STREAM_FILE", jsonl)
        if hasattr(vs, "_MODULE_DIR"):
            monkeypatch.setattr(vs, "_MODULE_DIR", out_dir.parent)
        if hasattr(vs, "_KERNEL_ROOT"):
            monkeypatch.setattr(vs, "_KERNEL_ROOT", root)

        yield root, out_dir, ledger, cursor, jsonl


def _write_ledger(path: Path, rows: list[dict]):
    fieldnames = ["claim_id", "claim", "c_level", "verdict", "primary_metric", "primary_value", "evidence_tag", "source", "spec", "seed_family", "caveats"]
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({k: row.get(k, "") for k in fieldnames})


class TestVerdictStream:
    def test_refresh_empty_ledger(self, temp_env):
        root, out_dir, ledger, cursor, jsonl = temp_env
        _write_ledger(ledger, [])
        stream = vs.VerdictStream()
        new = stream.refresh()
        assert new == []

    def test_refresh_detects_new_rows(self, temp_env):
        root, out_dir, ledger, cursor, jsonl = temp_env
        _write_ledger(ledger, [
            {"claim_id": "ADR-001", "claim": "Test claim", "c_level": "C0", "verdict": "INTEGRATE", "primary_value": "0.85", "evidence_tag": "FACT", "caveats": ""},
        ])
        stream = vs.VerdictStream()
        new = stream.refresh()
        assert len(new) == 1
        assert new[0]["claim_id"] == "ADR-001"
        assert new[0]["owner_action_required"] is False
        assert jsonl.exists()

    def test_refresh_does_not_duplicate(self, temp_env):
        root, out_dir, ledger, cursor, jsonl = temp_env
        _write_ledger(ledger, [
            {"claim_id": "ADR-001", "claim": "Test", "c_level": "C0", "verdict": "OPTIMIZE", "primary_value": "0.60", "evidence_tag": "FACT", "caveats": ""},
        ])
        stream = vs.VerdictStream()
        stream.refresh()
        # Second refresh with same data should find nothing new
        new2 = stream.refresh()
        assert new2 == []

    def test_high_priority_items(self, temp_env):
        root, out_dir, ledger, cursor, jsonl = temp_env
        _write_ledger(ledger, [
            {"claim_id": "ADR-001", "claim": "Good", "c_level": "C0", "verdict": "INTEGRATE", "primary_value": "0.80", "evidence_tag": "FACT", "caveats": ""},
            {"claim_id": "ADR-002", "claim": "Bad", "c_level": "C0", "verdict": "REJECTED", "primary_value": "0.20", "evidence_tag": "FACT", "caveats": ""},
        ])
        stream = vs.VerdictStream()
        stream.refresh()
        high = stream.high_priority_items()
        assert len(high) == 1
        assert high[0]["claim_id"] == "ADR-002"

    def test_notify_digest_persian(self, temp_env):
        root, out_dir, ledger, cursor, jsonl = temp_env
        _write_ledger(ledger, [
            {"claim_id": "ADR-001", "claim": "Good", "c_level": "C0", "verdict": "INTEGRATE", "primary_value": "0.80", "evidence_tag": "FACT", "caveats": ""},
        ])
        digest = vs.notify_digest()
        # After refresh there may be prior state, but digest should contain Persian text
        assert isinstance(digest, str)
        assert "verdict" in digest or "هیچ" in digest

    def test_owner_action_required_c4(self, temp_env):
        root, out_dir, ledger, cursor, jsonl = temp_env
        _write_ledger(ledger, [
            {"claim_id": "ADR-003", "claim": "C4 claim", "c_level": "C4", "verdict": "OPTIMIZE", "primary_value": "0.60", "evidence_tag": "EST", "caveats": "C4-level assertion"},
        ])
        stream = vs.VerdictStream()
        new = stream.refresh()
        assert new[0]["owner_action_required"] is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
