"""Quote-loop closure — the four modules the priced-quote path needs.

PR #101 restored the spine agents but left quote_pipeline's lazy imports
(quote_engine & friends) unresolved. These tests pin the closure: the four
quote-path modules import cleanly, and quote_pipeline fails closed with
honest JSON (never a traceback) on a host without the live databases.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

AGENTS = Path(__file__).resolve().parents[1] / "ofn" / "agents"
sys.path.insert(0, str(AGENTS))
sys.path.insert(0, str(AGENTS.parent / "budget"))

QUOTE_MODULES = [
    "quote_engine",
    "quote_fingerprint",
    "capability_token",
    "lead_email_writer",
]


def test_quote_modules_import() -> None:
    for name in QUOTE_MODULES:
        __import__(name)


def test_quote_pipeline_fails_closed_offline() -> None:
    proc = subprocess.run(
        [sys.executable, str(AGENTS / "quote_pipeline.py")],
        capture_output=True,
        text=True,
        timeout=60,
        cwd=str(AGENTS),
    )
    # on a host without the live painting DB the pipeline must emit JSON,
    # not raise — unknown/absent is never green
    payload = json.loads(proc.stdout)
    assert "error" in payload
