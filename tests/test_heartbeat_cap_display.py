"""Heartbeat cap display must render the LIVE lead cap (debt closed 2026-09-03).

The pulse line used to hardcode '/10' — with an OCTOPUS_LEAD_DAILY_SEND_CAP
override the number lied in the owner's own glass. Now it reads the worker's
live cap; a cap of 0 or below renders as unlimited (∞)."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

AGENTS = Path(__file__).resolve().parents[1] / "ofn" / "agents"
sys.path.insert(0, str(AGENTS))
sys.path.insert(0, str(AGENTS.parent / "budget"))


def _pulse_line(extra_env: dict[str, str]) -> str:
    env = dict(os.environ, **extra_env)
    proc = subprocess.run(
        [sys.executable, str(AGENTS / "heartbeat.py")],
        capture_output=True,
        text=True,
        timeout=60,
        cwd=str(AGENTS),
        env=env,
    )
    assert proc.returncode == 0, proc.stderr[-400:]
    return json.loads(proc.stdout)["line"]


def test_pulse_renders_env_cap_not_hardcoded_ten() -> None:
    line = _pulse_line({"OCTOPUS_LEAD_DAILY_SEND_CAP": "7"})
    assert "/7 " in line
    assert "/10" not in line


def test_pulse_renders_unlimited_cap_as_infinity() -> None:
    line = _pulse_line({"OCTOPUS_LEAD_DAILY_SEND_CAP": "0"})
    assert "/∞ " in line
