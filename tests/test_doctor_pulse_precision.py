"""GAP-018 — pulse precision: an empty inbox is QUIET, not DEAD.

Round-14 root-cause: events.jsonl only gains rows on real business events;
a clean inbox ages the last receipt while the writers (imap/quote/
scheduler) keep firing healthily — the doctor called that 'unhealthy'.
These locks pin the fix: fresh writers + stale events = HEALTHY·quiet;
stale events + NO fresh writer = UNHEALTHY (death, not quiet);
corrupt/absent sources stay UNKNOWN/UNPROBED — never a guessed green."""

from __future__ import annotations

import json
import sys
from pathlib import Path

AGENTS = Path(__file__).resolve().parents[1] / "ofn" / "agents"
sys.path.insert(0, str(AGENTS))
sys.path.insert(0, str(AGENTS.parent / "budget"))

import doctor  # noqa: E402


def _events(tmp_path: Path, occurred: str) -> Path:
    p = tmp_path / "events.jsonl"
    p.write_text(json.dumps({"occurred_at": occurred}) + "\n",
                 encoding="utf-8")
    return p


_STALE = "2026-09-01T00:00:00Z"   # قطعاً بیش از دو تیک


def test_stale_events_fresh_writers_is_healthy_quiet(tmp_path) -> None:
    p = _events(tmp_path, _STALE)
    ms = doctor.probe_pulse(
        events_path=p, now=1788500000.0,
        writer_ages_s={"octopus-imap": 900.0, "octopus-quote": 2500.0,
                       "octopus-scheduler": 1200.0})
    m = ms[0]
    assert m.verdict is doctor.Verdict.HEALTHY
    assert "quiet" in (m.detail or "") and "octopus-imap" in m.detail


def test_stale_events_no_fresh_writer_is_unhealthy_death(tmp_path) -> None:
    p = _events(tmp_path, _STALE)
    ms = doctor.probe_pulse(
        events_path=p, now=1788500000.0,
        writer_ages_s={"octopus-imap": 90000.0, "octopus-quote": None,
                       "octopus-scheduler": 700000.0})
    m = ms[0]
    assert m.verdict is doctor.Verdict.UNHEALTHY
    assert "death" in (m.detail or "")


def test_fresh_events_stay_healthy_unchanged(tmp_path) -> None:
    p = _events(tmp_path, "2026-09-03T00:00:00Z")
    ms = doctor.probe_pulse(events_path=p, now=1788393900.0)  # ۵ دقیقه بعد
    assert ms[0].verdict is doctor.Verdict.HEALTHY
    assert ms[0].detail is None  # سبزِ ساده، بدون برچسبِ quiet


def test_default_path_stale_uses_live_writer_probe(tmp_path, monkeypatch) -> None:
    """بدون writer_ages_s صریح، سنسور واقعی systemctl صدا زده می‌شود."""
    p = _events(tmp_path, _STALE)
    monkeypatch.setattr(doctor, "_pulse_writer_ages",
                        lambda now_monotonic=None: {
                            "octopus-imap": 600.0,
                            "octopus-quote": None,
                            "octopus-scheduler": None})
    ms = doctor.probe_pulse(events_path=p, now=1788500000.0)
    assert ms[0].verdict is doctor.Verdict.HEALTHY
    assert "quiet" in (ms[0].detail or "")


def test_corrupt_events_stay_unknown_fail_closed(tmp_path) -> None:
    (tmp_path / "events.jsonl").write_text("{broken\n", encoding="utf-8")
    ms = doctor.probe_pulse(events_path=tmp_path / "events.jsonl",
                            now=1788500000.0)
    assert ms[0].verdict is doctor.Verdict.UNKNOWN


def test_missing_events_stay_unprobed(tmp_path) -> None:
    ms = doctor.probe_pulse(events_path=tmp_path / "none.jsonl")
    assert ms[0].verdict is doctor.Verdict.UNPROBED
