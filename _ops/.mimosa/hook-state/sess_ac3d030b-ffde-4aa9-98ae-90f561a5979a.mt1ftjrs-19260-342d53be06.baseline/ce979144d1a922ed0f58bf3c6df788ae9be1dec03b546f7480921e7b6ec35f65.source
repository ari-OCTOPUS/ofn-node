"""test_close_kernel_integrity_20260816 — ERRORHUNT ۵ تازه‌سازی digest.

SENSITIVITY-LADDER.md و GEOMETRY.md باید با manifest جور باشند.
ثبت در run_all نشده (WORKLOCK).
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "03 - Projects" / "research-spec-compiler" / "body_bridge"))

import manifest_generator as mg  # noqa: E402


def test_ladder_and_geometry_match_manifest():
    result = mg.validate_integrity()
    assert result["manifest_exists"] is True
    details = result["details"]
    for name in ("SENSITIVITY-LADDER.md", "GEOMETRY.md"):
        row = details[name]
        assert row["ok"] is True, (name, row)
    assert result["valid"] is True, result
