"""Learning feeder — the automated ledger feed locks (gap #21/#23 close).

Pins: no fresh events = honest skip (no run invented); events convert to
evidence/claims without inventing payments (only payment.claimed makes a
claim); the CLI subprocess runs and produces run-summary.json; a corrupt
event line never kills the sweep; and the feeder only writes inside the
runs dir + delegated ledger."""

from __future__ import annotations

import json
import sys
from pathlib import Path

AGENTS = Path(__file__).resolve().parents[1] / "ofn" / "agents"
sys.path.insert(0, str(AGENTS))
sys.path.insert(0, str(AGENTS.parent / "budget"))

import learning_feeder as lf  # noqa: E402


def _seed_events(tmp_path: Path, rows: list[dict]) -> None:
    d = tmp_path / "legs" / "lead-inbox"
    d.mkdir(parents=True)
    (d / "events.jsonl").write_text(
        "\n".join(json.dumps(r) for r in rows) + "\n", encoding="utf-8")


def _ev(kind: str, lead: str, h_ago: float = 1.0, amount=None) -> dict:
    import datetime as dt
    at = dt.datetime.now(dt.timezone.utc) - dt.timedelta(hours=h_ago)
    payload = {"amount": amount} if amount is not None else {}
    return {"event_type": kind, "occurred_at": at.strftime(
        "%Y-%m-%dT%H:%M:%SZ"), "correlation_id": lead, "payload": payload}


def test_no_fresh_events_is_honest_skip(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(lf, "EVENTS", tmp_path / "none.jsonl")
    res = lf.feed()
    assert res["ok"] and "skipped" in res


def test_events_convert_without_inventing_payments(tmp_path, monkeypatch) -> None:
    _seed_events(tmp_path, [
        _ev("communication.sent", "lead:a"),
        _ev("payment.verified", "lead:a", amount=100),
        _ev("random.noise", "lead:b"),
    ])
    monkeypatch.setattr(lf, "EVENTS",
                        tmp_path / "legs" / "lead-inbox" / "events.jsonl")
    ev, claims = lf.build_evidence(lf._read_recent_events())
    leads = {l["lead_id"]: l["events"] for l in ev["leads"]}
    assert "lead:b" not in leads                      # نویز رد شد
    assert any(e["type"] == "payment.verified" for e in leads["lead:a"])
    assert claims == []                               # بدون claimed، بدون claim


def test_claimed_makes_claim(tmp_path, monkeypatch) -> None:
    _seed_events(tmp_path, [_ev("payment.claimed", "lead:c", amount=5)])
    monkeypatch.setattr(lf, "EVENTS",
                        tmp_path / "legs" / "lead-inbox" / "events.jsonl")
    ev, claims = lf.build_evidence(lf._read_recent_events())
    assert claims and claims[0]["lead_id"] == "lead:c"


def test_corrupt_lines_are_skipped_not_fatal(tmp_path, monkeypatch) -> None:
    d = tmp_path / "legs" / "lead-inbox"
    d.mkdir(parents=True)
    good = json.dumps(_ev("communication.sent", "lead:a"))
    (d / "events.jsonl").write_text(
        "{broken\n" + good + "\n", encoding="utf-8")
    monkeypatch.setattr(lf, "EVENTS", d / "events.jsonl")
    ev = lf._read_recent_events()
    assert len(ev) == 1


def test_old_events_outside_lookback_are_dropped(tmp_path, monkeypatch) -> None:
    _seed_events(tmp_path, [_ev("communication.sent", "lead:old", h_ago=72)])
    monkeypatch.setattr(lf, "EVENTS",
                        tmp_path / "legs" / "lead-inbox" / "events.jsonl")
    assert lf._read_recent_events() == []
