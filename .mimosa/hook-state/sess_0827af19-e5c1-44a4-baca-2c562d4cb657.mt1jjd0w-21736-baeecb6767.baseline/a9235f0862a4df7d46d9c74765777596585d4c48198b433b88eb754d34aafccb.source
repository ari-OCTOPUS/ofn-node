#!/usr/bin/env python3
"""test_cognitive_events.py — Typed Event Stream + Run ID + Run Store tests."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import harness  # noqa: E402

ENV = harness.setup("cognitive-events")
_OPS = harness.SELF_OPS

sys.path.insert(0, str(_OPS))
sys.path.insert(0, str(_OPS / "cognitive"))

import event_stream as es  # noqa: E402
import run_store as rs  # noqa: E402


def _fresh_store():
    """point store at isolated state dir."""
    rs.STATE_DIR = Path(ENV["ops"]) / "state"
    rs.RUNS_DIR = rs.STATE_DIR / "cognitive" / "runs"


def t_run_id_unique():
    ids = {es.mint_run_id() for _ in range(100)}
    assert len(ids) == 100, "run_id collision"


def t_start_run_creates_events():
    _fresh_store()
    r = es.start_run("سلام آزمایش")
    assert r["run_id"].startswith("run_")
    assert r["trace_id"].startswith("trace_")
    events = rs.list_events(r["run_id"])
    assert len(events) >= 2  # RUN_CREATED (create_run) + USER_MESSAGE_ACCEPTED (emit)
    assert events[0]["event_type"] == "RUN_CREATED"
    assert events[0]["sequence"] == 0
    assert events[1]["event_type"] == "USER_MESSAGE_ACCEPTED"
    assert events[1]["sequence"] == 1


def t_sequence_monotonic():
    _fresh_store()
    r = es.start_run("test")
    rid = r["run_id"]
    tid = r["trace_id"]
    for et in ("INTENT_DETECTED", "CONTEXT_RETRIEVED", "MODEL_STARTED"):
        seq = es.emit(rid, et, trace_id=tid, producer="test")
        assert seq > 0
    events = rs.list_events(rid)
    seqs = [e["sequence"] for e in events]
    assert seqs == sorted(seqs), "sequence not monotonic"
    assert len(seqs) == len(set(seqs)), "sequence duplicate"


def t_no_raw_text_persisted():
    _fresh_store()
    r = es.start_run("این متن محرمانه است")
    events = rs.list_events(r["run_id"])
    for e in events:
        payload_str = str(e.get("payload", {}))
        assert "متن محرمانه" not in payload_str, "raw text leaked!"
        assert e.get("redaction_applied") is True


def t_may_authorize_always_false():
    _fresh_store()
    r = es.start_run("test")
    events = rs.list_events(r["run_id"])
    for e in events:
        assert e.get("may_authorize") is False
        assert e.get("applied") is False


def t_complete_run_terminal():
    _fresh_store()
    r = es.start_run("test")
    rid = r["run_id"]
    es.complete_run(rid, trace_id=r["trace_id"], response_digest="abc123")
    run = rs.get_run(rid)
    assert run["state"] == "COMPLETED"
    events = rs.list_events(rid)
    assert any(e["event_type"] == "RESPONSE_COMPLETED" for e in events)
    assert any(e["event_type"] == "RUN_COMPLETED" for e in events)


def t_fail_run():
    _fresh_store()
    r = es.start_run("test")
    es.fail_run(r["run_id"], "model timeout", trace_id=r["trace_id"])
    run = rs.get_run(r["run_id"])
    assert run["state"] == "FAILED"


def t_run_summary():
    _fresh_store()
    r = es.start_run("test")
    rid = r["run_id"]
    es.emit(rid, "INTENT_DETECTED", trace_id=r["trace_id"],
            producer="router", intent="intro")
    es.complete_run(rid, trace_id=r["trace_id"])
    summary = es.run_summary(rid)
    assert summary["run_id"] == rid
    assert summary["event_count"] >= 4
    assert summary["may_authorize"] is False


def t_list_events_after_sequence():
    _fresh_store()
    r = es.start_run("test")
    rid = r["run_id"]
    es.emit(rid, "INTENT_DETECTED", trace_id=r["trace_id"])
    es.emit(rid, "MODEL_STARTED", trace_id=r["trace_id"])
    es.emit(rid, "MODEL_FINISHED", trace_id=r["trace_id"])
    # تمام eventها از sequence 2 به بعد
    after = rs.list_events(rid, after_sequence=2)
    assert all(e["sequence"] > 2 for e in after)
    assert len(after) >= 1


def t_duplicate_run_id_idempotent():
    _fresh_store()
    """append به همان run_id به همان فایل اضافه می‌کند — sequence ادامه می‌یابد."""
    r = es.start_run("test")
    rid = r["run_id"]
    s1 = es.emit(rid, "INTENT_DETECTED", trace_id=r["trace_id"])
    s2 = es.emit(rid, "INTENT_DETECTED", trace_id=r["trace_id"])
    assert s2 == s1 + 1, "sequence should continue"


if __name__ == "__main__":
    failed = harness.run([
        ("run_id unique", t_run_id_unique),
        ("start_run creates events", t_start_run_creates_events),
        ("sequence monotonic", t_sequence_monotonic),
        ("no raw text persisted", t_no_raw_text_persisted),
        ("may_authorize always false", t_may_authorize_always_false),
        ("complete_run terminal", t_complete_run_terminal),
        ("fail_run", t_fail_run),
        ("run_summary", t_run_summary),
        ("list_events after sequence", t_list_events_after_sequence),
        ("duplicate run_id idempotent", t_duplicate_run_id_idempotent),
    ])
    sys.exit(1 if failed else 0)
