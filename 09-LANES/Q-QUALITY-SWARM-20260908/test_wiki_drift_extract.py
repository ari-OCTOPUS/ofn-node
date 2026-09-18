"""Lane tests for wiki_drift_check extractors (no network)."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import wiki_drift_check as w  # noqa: E402


def test_extract_head_and_beat() -> None:
    sample = """
- **coherence:** 0.953
- **beat:** 65620
- **HEAD:** 74cc733
"""
    d = w.extract_current_truth(sample)
    assert d["wiki_head"] == "74cc733"
    assert d["wiki_beat"] == 65620


if __name__ == "__main__":
    test_extract_head_and_beat()
    print("PASS test_extract_head_and_beat")
