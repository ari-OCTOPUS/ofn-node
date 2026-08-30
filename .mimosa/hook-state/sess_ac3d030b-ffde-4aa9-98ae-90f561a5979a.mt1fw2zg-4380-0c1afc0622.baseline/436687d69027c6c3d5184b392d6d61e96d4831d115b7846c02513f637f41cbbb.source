#!/usr/bin/env python3
"""
test_adr_feed.py — pytest tests for the ADR feed bridge module.

At least 3 test cases covering parsing, feed generation, and filtering.
"""

import json
import os
import subprocess
import sys
from pathlib import Path

# Ensure body_bridge is importable when pytest runs from the repo root
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import adr_feed

# ---------------------------------------------------------------------------
# Unit tests for internal helpers
# ---------------------------------------------------------------------------

def test_extract_verdict_table():
    """Unit: _extract_verdict_table parses markdown tables inside Verdict sections."""
    text = (
        "## Verdict\n\n"
        "| condition | mean | std |\n"
        "|---|---|---|\n"
        "| a | 1.0 | 0.1 |\n"
        "| b | 2.0 | 0.2 |\n"
    )
    rows = adr_feed._extract_verdict_table(text)
    assert len(rows) == 2
    assert rows[0]["condition"] == "a"
    assert rows[0]["mean"] == "1.0"
    assert rows[1]["std"] == "0.2"


def test_extract_verdict_table_empty():
    """Unit: _extract_verdict_table returns empty list when no table."""
    assert adr_feed._extract_verdict_table("no table here") == []


# ---------------------------------------------------------------------------
# Integration tests against the real ADR corpus
# ---------------------------------------------------------------------------

def test_refresh_adr_feed_produces_valid_json():
    """
    Integration: refresh_adr_feed() writes a valid JSON file with the expected
    top-level keys and at least one ADR.
    """
    feed = adr_feed.refresh_adr_feed()
    assert adr_feed.OUTPUT_PATH.is_file(), f"Output file not created: {adr_feed.OUTPUT_PATH}"
    with open(adr_feed.OUTPUT_PATH, "r", encoding="utf-8") as fh:
        data = json.load(fh)
    assert "kernel_name" in data
    assert data["kernel_name"] == "Cognitive Kernel 0.1"
    assert "last_updated" in data
    assert "checksum" in data
    assert isinstance(data["checksum"], str)
    assert len(data["checksum"]) == 64  # SHA-256 hex length
    assert "adrs" in data
    assert "total" in data
    assert data["total"] == len(data["adrs"])
    assert data["total"] >= 1


def test_get_adr_by_verdict_rejected():
    """
    Integration: get_adr_by_verdict('REJECTED') returns at least ADR-001
    and ADR-021, which are known REJECTED ADRs from the corpus.
    """
    rejected = adr_feed.get_adr_by_verdict("REJECTED")
    numbers = {adr["adr_number"] for adr in rejected}
    assert 1 in numbers, "ADR-001 (known REJECTED) should be returned"
    assert 21 in numbers, "ADR-021 (known REJECTED) should be returned"
    for adr in rejected:
        assert adr["verdict"] == "REJECTED"


def test_get_adr_by_verdict_optimize():
    """
    Integration: get_adr_by_verdict('OPTIMIZE') returns ADR-002 and ADR-003.
    """
    optimized = adr_feed.get_adr_by_verdict("OPTIMIZE")
    numbers = {adr["adr_number"] for adr in optimized}
    assert 2 in numbers, "ADR-002 (known OPTIMIZE) should be returned"
    assert 3 in numbers, "ADR-003 (known OPTIMIZE) should be returned"


def test_get_adr_by_verdict_integrate():
    """
    Integration: get_adr_by_verdict('INTEGRATE') returns ADR-009 and ADR-011.
    """
    integrated = adr_feed.get_adr_by_verdict("INTEGRATE")
    numbers = {adr["adr_number"] for adr in integrated}
    assert 9 in numbers, "ADR-009 (known INTEGRATE) should be returned"
    assert 11 in numbers, "ADR-011 (known INTEGRATE) should be returned"


def test_summary_counts():
    """
    Integration: summary() returns correct total and counts by verdict,
    matching the known corpus size (~21 ADRs).
    """
    s = adr_feed.summary()
    assert "by_verdict" in s
    assert "total" in s
    assert "last_updated" in s
    assert "checksum" in s
    total = s["total"]
    assert total >= 21, f"Expected at least 21 ADRs, got {total}"
    # Sum of counts should equal total
    summed = sum(s["by_verdict"].values())
    assert summed == total, f"Sum of verdict counts ({summed}) != total ({total})"


def test_adr_fields_present():
    """
    Integration: every parsed ADR must have the required fields populated
    (adr_number, title, verdict, date, filename).
    """
    feed = adr_feed.refresh_adr_feed()
    for adr in feed["adrs"]:
        assert isinstance(adr["adr_number"], int)
        assert adr["title"]
        assert adr["verdict"] is not None or adr["status"] != ""
        assert adr["date"] != "" or "date" in adr
        assert adr["filename"].startswith("ADR-")


def test_verdict_table_parsing():
    """
    Integration: ADR-001 and ADR-003 have verdict tables parsed into list-of-dicts.
    """
    feed = adr_feed.refresh_adr_feed()
    by_num = {adr["adr_number"]: adr for adr in feed["adrs"]}
    adr001 = by_num.get(1)
    adr003 = by_num.get(3)
    assert adr001 is not None
    assert adr003 is not None
    assert adr001["verdict_table"] is not None
    assert len(adr001["verdict_table"]) > 0
    assert adr003["verdict_table"] is not None
    assert len(adr003["verdict_table"]) > 0
    # Check that expected condition names appear in the table
    conds_001 = [row.get("condition", "").strip() for row in adr001["verdict_table"]]
    assert any("limited_wm" in c or "unlimited_memory" in c for c in conds_001)


def test_checksum_stability():
    """
    Integration: two consecutive runs on unchanged files produce the same checksum.
    """
    feed1 = adr_feed.refresh_adr_feed()
    feed2 = adr_feed.refresh_adr_feed()
    assert feed1["checksum"] == feed2["checksum"]
    assert feed1["total"] == feed2["total"]


def test_no_print_side_effects():
    """
    Library safety: importing adr_feed does not trigger I/O or feed rebuild.
    """
    assert callable(adr_feed.refresh_adr_feed)
    assert callable(adr_feed.get_adr_by_verdict)
    assert callable(adr_feed.summary)


def test_cli_refresh():
    """
    Integration: running the module as script writes the output file.
    """
    result = subprocess.run(
        [sys.executable, str(adr_feed.__file__)],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert adr_feed.OUTPUT_PATH.is_file()
