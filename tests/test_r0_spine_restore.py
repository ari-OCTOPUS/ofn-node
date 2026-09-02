"""R0 spine restore — smoke tests for the revenue-chain agents recovered from
the release/p0 lineage (owner order 2026-09-02, R0-CLOSE lane C).

These are restore-not-rewrite modules: we assert import health, offline
dry-run behaviour (fail-closed, JSON out, never a traceback), and the
presence of the entry points the board's systemd units expect.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

AGENTS = Path(__file__).resolve().parents[1] / "ofn" / "agents"
sys.path.insert(0, str(AGENTS))
sys.path.insert(0, str(AGENTS.parent / "budget"))

RESTORED = [
    "imap_listener",
    "quote_pipeline",
    "heartbeat",
    "memory_chain",
    "owner_notify",
    "mail_credentials",
    "consent_store",
    "opslib",
]


def test_all_spine_modules_import() -> None:
    for name in RESTORED:
        __import__(name)


def test_imap_listener_dry_run_is_graceful_json() -> None:
    proc = subprocess.run(
        [sys.executable, str(AGENTS / "imap_listener.py"), "--dry"],
        capture_output=True,
        text=True,
        timeout=60,
        cwd=str(AGENTS),
    )
    assert proc.returncode == 0, proc.stderr[-400:]
    payload = json.loads(proc.stdout)
    assert "scanned" in payload and "processed" in payload


def test_quote_pipeline_entrypoint_exists() -> None:
    assert (AGENTS / "quote_pipeline.py").is_file()
    assert (AGENTS / "heartbeat.py").is_file()
    assert (AGENTS.parent / "budget" / "opslib.py").is_file()
