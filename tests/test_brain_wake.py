"""Brain wake — the heart→brain link (P3 of HARMONY-MERGER, Round 28).

Pins: only wake-worthy events produce a wake; quiet periods are an honest
no-op; envelopes carry the proven cognitive_wake.v1 shape (hold_external,
may_authorize=false, wake_sha256, deadline); dedup via state file; and the
writer only touches mesh events/outbox + its own state file."""

from __future__ import annotations

import json
import sys
from pathlib import Path

AGENTS = Path(__file__).resolve().parents[1] / "ofn" / "agents"
sys.path.insert(0, str(AGENTS))
sys.path.insert(0, str(AGENTS.parent / "budget"))

import brain_wake as bw  # noqa: E402


def _seed(tmp_path: Path, rows: list[dict]) -> None:
    d = tmp_path / "legs" / "lead-inbox"
    d.mkdir(parents=True)
    (d / "events.jsonl").write_text(
        "\n".join(json.dumps(r) for r in rows) + "\n", encoding="utf-8")


def _ev(kind: str, lead: str, h_ago: float = 1.0) -> dict:
    import datetime as dt
    at = dt.datetime.now(dt.timezone.utc) - dt.timedelta(hours=h_ago)
    return {"event_type": kind, "occurred_at": at.strftime(
        "%Y-%m-%dT%H:%M:%SZ"), "correlation_id": lead}


def test_quiet_period_is_honest_noop(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(bw, "EVENTS", tmp_path / "none.jsonl")
    res = bw.cycle(state_dir=tmp_path)
    assert res["wake"] is False and "silence" in res["reason"]


def test_worthy_events_build_real_envelope(tmp_path, monkeypatch) -> None:
    _seed(tmp_path, [_ev("payment.verified", "ziman:1"),
                     _ev("lead.discovered", "painting:9")])
    monkeypatch.setattr(bw, "EVENTS",
                        tmp_path / "legs" / "lead-inbox" / "events.jsonl")
    monkeypatch.setattr(bw, "MESH_EVENTS", tmp_path / "mesh-events")
    monkeypatch.setattr(bw, "OUTBOX", tmp_path / "outbox")
    monkeypatch.setattr(bw, "STATE", tmp_path / "bw-state.json")
    res = bw.cycle(state_dir=tmp_path)
    assert res["wake"] is True
    out = json.loads((tmp_path / "outbox" / res["outbox_file"].split("/")[-1]
                      if False else res["outbox_file"].split("\\")[-1]
                      and Path(res["outbox_file"])).read_text(encoding="utf-8"))
    assert out["event_type"] == "cognitive_wake.v1"
    assert out["hold_external"] is True
    assert out["may_authorize"] is False
    assert "ziman" in out["businesses"] and "painting" in out["businesses"]
    assert len(out["wake_sha256"]) == 64


def test_noise_events_do_not_wake(tmp_path, monkeypatch) -> None:
    _seed(tmp_path, [_ev("random.noise", "lead:x")])
    monkeypatch.setattr(bw, "EVENTS",
                        tmp_path / "legs" / "lead-inbox" / "events.jsonl")
    monkeypatch.setattr(bw, "MESH_EVENTS", tmp_path / "me")
    monkeypatch.setattr(bw, "OUTBOX", tmp_path / "ob")
    monkeypatch.setattr(bw, "STATE", tmp_path / "st.json")
    res = bw.cycle(state_dir=tmp_path)
    assert res["wake"] is False


def test_state_dedup_prevents_double_wake(tmp_path, monkeypatch) -> None:
    _seed(tmp_path, [_ev("payment.verified", "ziman:1", h_ago=0.1)])
    monkeypatch.setattr(bw, "EVENTS",
                        tmp_path / "legs" / "lead-inbox" / "events.jsonl")
    monkeypatch.setattr(bw, "MESH_EVENTS", tmp_path / "me")
    monkeypatch.setattr(bw, "OUTBOX", tmp_path / "ob")
    monkeypatch.setattr(bw, "STATE", tmp_path / "st.json")
    r1 = bw.cycle(state_dir=tmp_path)
    assert r1["wake"] is True
    # state saved → second cycle over the same window must not re-wake
    r2 = bw.cycle(state_dir=tmp_path)
    assert r2["wake"] is False


def test_writer_touches_only_allowed_paths(tmp_path, monkeypatch) -> None:
    _seed(tmp_path, [_ev("payment.verified", "ziman:1")])
    monkeypatch.setattr(bw, "EVENTS",
                        tmp_path / "legs" / "lead-inbox" / "events.jsonl")
    monkeypatch.setattr(bw, "MESH_EVENTS", tmp_path / "me")
    monkeypatch.setattr(bw, "OUTBOX", tmp_path / "ob")
    monkeypatch.setattr(bw, "STATE", tmp_path / "st.json")
    bw.cycle(state_dir=tmp_path)
    src = Path(bw.__file__).read_text(encoding="utf-8")
    for banned in ("sendMessage", "urllib", "smtp", "os.remove"):
        assert banned not in src, banned
