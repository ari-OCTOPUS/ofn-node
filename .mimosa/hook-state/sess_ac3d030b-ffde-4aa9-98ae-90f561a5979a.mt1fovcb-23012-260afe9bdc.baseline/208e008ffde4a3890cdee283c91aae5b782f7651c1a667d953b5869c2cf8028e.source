"""test_close_tcb_model_listed_20260816 — C-033 digest-map.

core/model.py باید در CODE_TCB_FILES و trust-boundary.json باشد.
ثبت در run_all نشده (WORKLOCK).
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "4d_system"))

from brain.guardrails import CODE_TCB_FILES, check_trust_boundary  # noqa: E402


def test_core_model_in_tcb_files_and_manifest():
    assert "core/model.py" in CODE_TCB_FILES
    man = json.loads(
        (ROOT / "4d_system" / "config" / "trust-boundary.json").read_text(encoding="utf-8")
    )
    assert "core/model.py" in man["tcb"]["files"]
    tb = check_trust_boundary()
    assert tb["coverage_complete"] is True
    assert tb["digests_ok"] is True
    assert tb["signature"] == "valid", tb
