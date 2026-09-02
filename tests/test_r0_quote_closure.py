"""Quote-loop closure (110A, generation-only) — scope split of the original #110.

The original #110 carried a send path (capability_token.verified_send →
lead_outbound_transport.send) under a "dependency restoration" title. This
suite pins the 110A contract: quote modules generate drafts only; the send
authorization primitive lives in a separate, honestly-titled PR (110B).
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
    "lead_email_writer",
]


def test_quote_modules_import() -> None:
    for name in QUOTE_MODULES:
        __import__(name)


def test_send_path_modules_are_absent_from_this_pr() -> None:
    assert not (AGENTS / "capability_token.py").exists()
    assert not (AGENTS / "lead_outbound_transport.py").exists()


def test_quote_modules_never_import_the_send_path() -> None:
    for name in QUOTE_MODULES:
        source = (AGENTS / f"{name}.py").read_text(encoding="utf-8")
        assert "import capability_token" not in source, name
        assert "import lead_outbound_transport" not in source, name
        assert "verified_send" not in source, name


def test_quote_refuses_non_dry_offline() -> None:
    import quote_engine
    out = quote_engine.quote("lead:x", {}, dry=False)
    assert out.get("error") == "send-path-removed: generation-only module"


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
