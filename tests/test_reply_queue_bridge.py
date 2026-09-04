"""Reply-queue bridge — brain replies land in OWNER-QUEUE."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from reply_queue_bridge import extract_proposals, append_to_queue  # noqa: E402


def _seed_inbox(tmp_path, entries):
    inbox = tmp_path / "inbox"
    inbox.mkdir()
    for i, e in enumerate(entries):
        (inbox / f"{i}.json").write_text(json.dumps(e), encoding="utf-8")
    return inbox


def test_proposal_extraction(tmp_path) -> None:
    inbox = _seed_inbox(tmp_path, [
        {"idempotency_key": "abc", "payload": {"response": {
            "claim_type": "proposal", "confidence": 0.3,
            "evidence": ["painting:BLOCKED"]}, "businesses": ["painting"]}},
        {"idempotency_key": "def", "payload": {"response": {
            "claim_type": "observation"}}},
    ])
    import reply_queue_bridge as _rqb
    orig = _rqb.SEEN_FILE
    _rqb.SEEN_FILE = tmp_path / "seen.json"
    try:
        props = extract_proposals(inbox)
    finally:
        _rqb.SEEN_FILE = orig
    assert len(props) == 1
    assert props[0]["idempotency_key"] == "abc"


def test_dedup_second_pass(tmp_path) -> None:
    inbox = _seed_inbox(tmp_path, [
        {"idempotency_key": "abc", "payload": {"response": {
            "claim_type": "proposal", "confidence": 0.5, "evidence": []}}},
    ])
    import reply_queue_bridge as _rqb
    orig = _rqb.SEEN_FILE
    _rqb.SEEN_FILE = tmp_path / "seen.json"
    try:
        p1 = extract_proposals(inbox)
        assert len(p1) == 1
        p2 = extract_proposals(inbox)
        assert len(p2) == 0
    finally:
        _rqb.SEEN_FILE = orig


def test_append_to_queue(tmp_path) -> None:
    import reply_queue_bridge as _rqb
    orig = _rqb.QUEUE
    _rqb.QUEUE = tmp_path / "OWNER-QUEUE.md"
    try:
        n = append_to_queue([
            {"confidence": 0.3, "evidence": ["painting:BLOCKED_HONEST:sha"]},
        ])
    finally:
        _rqb.QUEUE = orig
    assert n == 1
    assert _rqb.QUEUE.exists()
