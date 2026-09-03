"""Heartbeat dependency restore — outbound_worker was a lazy-import closure miss
in PR #101 (top-level-only import scan). This pins the regression: heartbeat
must import and emit its honest JSON pulse even when nothing is armed."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

AGENTS = Path(__file__).resolve().parents[1] / "ofn" / "agents"
sys.path.insert(0, str(AGENTS))
sys.path.insert(0, str(AGENTS.parent / "budget"))


def test_outbound_worker_imports() -> None:
    import outbound_worker  # noqa: F401


def test_heartbeat_pulse_is_honest_json() -> None:
    proc = subprocess.run(
        [sys.executable, str(AGENTS / "heartbeat.py")],
        capture_output=True,
        text=True,
        timeout=60,
        cwd=str(AGENTS),
    )
    assert proc.returncode == 0, proc.stderr[-400:]
    payload = json.loads(proc.stdout)
    assert "line" in payload
    assert payload.get("tg", {}).get("ok") is False  # unarmed host must not claim a send
