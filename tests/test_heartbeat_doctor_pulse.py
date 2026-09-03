"""Doctor pulse — heartbeat consumes the doctor report (gap #14 close).

The hourly owner line must carry the doctor's honest verdict: green when
healthy, verdict + first unhealthy names otherwise, an explicit stale tag
when the report outlives its cadence, and «بدون-گزارش» when absent or
corrupt — never a guessed green."""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

AGENTS = Path(__file__).resolve().parents[1] / "ofn" / "agents"
sys.path.insert(0, str(AGENTS))
sys.path.insert(0, str(AGENTS.parent / "budget"))

import heartbeat  # noqa: E402


def _report(tmp_path: Path, verdict: str, age_h: float,
            unhealthy=None) -> Path:
    import datetime as dt
    p = tmp_path / "report.json"
    gen = time.time() - age_h * 3600
    body = {
        "generated_at": dt.datetime.fromtimestamp(
            gen, tz=dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "verdict": verdict,
        "measurements": [
            {"name": n, "verdict": "unhealthy", "detail": "", "command": "c"}
            for n in (unhealthy or [])
        ],
        "unprobed": {"count": 0, "names": []},
        "unknown": {"count": 0, "names": []},
    }
    p.write_text(json.dumps(body), encoding="utf-8")
    return p


def test_healthy_report_says_green(tmp_path) -> None:
    p = _report(tmp_path, "healthy", 0.5)
    assert heartbeat._doctor_summary(p) == "دکتر:سبز"


def test_degraded_names_first_unhealthy(tmp_path) -> None:
    p = _report(tmp_path, "degraded", 0.5,
                unhealthy=["unit.octopus-x", "pulse.events"])
    out = heartbeat._doctor_summary(p)
    assert "degraded" in out and "unit.octopus-x" in out


def test_incomplete_reports_blind_count(tmp_path) -> None:
    p = _report(tmp_path, "incomplete", 0.5)
    body = json.loads(p.read_text(encoding="utf-8"))
    body["unknown"] = {"count": 3, "names": ["a", "b", "c"]}
    p.write_text(json.dumps(body), encoding="utf-8")
    out = heartbeat._doctor_summary(p)
    assert "incomplete" in out and "3 blind" in out


def test_stale_report_is_labeled_not_green(tmp_path) -> None:
    p = _report(tmp_path, "healthy", 9.0)
    assert "کهنه" in heartbeat._doctor_summary(p)


def test_absent_or_corrupt_report_is_never_green(tmp_path) -> None:
    assert heartbeat._doctor_summary(
        tmp_path / "none.json") == "دکتر:بدون-گزارش"
    p = tmp_path / "broken.json"
    p.write_text("{broken", encoding="utf-8")
    assert heartbeat._doctor_summary(p) == "دکتر:بدون-گزارش"
