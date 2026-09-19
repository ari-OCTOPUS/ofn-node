"""Paired test for the exported OWNER-LINK glass_runner patches (RUNTIME-EXPORT PR).

Red against canonical (no callback spool, no sender fallback, no
edited_message), green with the exported runtime file. Covers the three
behavior promises of the +81 lines:

- an allowed inline-button tap is spooled to the MONEY lane with the chat's
  identity and kind=callback, and acknowledged via answerCallbackQuery
- a tap from a non-allowed chat is never spooled as an owner decision
- identity is the SENDER: an owner typing from a non-allowlisted group chat is
  still captured (chat rewritten to the sender, from_chat preserved)
- edited_message updates are processed like messages

Spools and the glass-seen audit path are redirected to tmp; nothing here
touches live state.
"""
import json

import pytest

from ofn.agents import glass_runner as gr


@pytest.fixture()
def harness(tmp_path, monkeypatch):
    money = tmp_path / "tg-inbox.jsonl"
    b3 = tmp_path / "go_b3_inbox.jsonl"
    seen = tmp_path / "seen"
    seen.mkdir()
    monkeypatch.setattr(gr, "_LANES", {"B3": b3, "MONEY": money})
    monkeypatch.setattr(gr, "_allowed_chats", lambda: {"111"})

    class _ShimPath:
        def __init__(self, name):
            self.name = name

        def __truediv__(self, other):
            return _ShimPath(str(other))

        def open(self, *a, **k):
            return (seen / self.name).open(*a, **k)

    class _ShimPathlib:
        Path = staticmethod(lambda p: _ShimPath(p))

    monkeypatch.setattr(gr, "pathlib", _ShimPathlib)

    acks = []
    monkeypatch.setattr(gr, "_tg", lambda token, method, payload=None: acks.append((method, payload)) or {})
    return {"money": money, "b3": b3, "seen": seen, "acks": acks}


def _rows(path):
    if not path.exists():
        return []
    return [json.loads(l) for l in path.read_text(encoding="utf-8").splitlines() if l.strip()]


def test_allowed_callback_spools_to_money_with_ack(harness):
    u = {"update_id": 1, "callback_query": {
        "id": "cb9", "data": " approve:GO-77 ",
        "message": {"chat": {"id": 111}}}}
    gr.process_updates([u], "tok")
    rows = _rows(harness["money"])
    cb = [r for r in rows if r.get("kind") == "callback"]
    assert len(cb) == 1
    assert cb[0]["chat"] == "111"
    assert cb[0]["text"] == "approve:GO-77"
    assert cb[0]["lane"] == "MONEY"
    assert cb[0]["route_reason"] == "callback_query"
    acks = [a for a in harness["acks"] if a[0] == "answerCallbackQuery"]
    assert acks and acks[0][1]["callback_query_id"] == "cb9"


def test_foreign_callback_never_spooled(harness):
    u = {"update_id": 2, "callback_query": {
        "id": "cbX", "data": "approve:GO-1", "message": {"chat": {"id": 222}}}}
    gr.process_updates([u], "tok")
    assert all(r.get("chat") != "222" for r in _rows(harness["money"]))


def test_sender_identity_fallback(harness):
    u = {"update_id": 3, "message": {
        "chat": {"id": 999}, "from": {"id": 111}, "text": "status report please"}}
    gr.process_updates([u], "tok")
    rows = [r for r in _rows(harness["money"]) if r.get("from_chat") == "999"]
    assert rows and rows[0]["chat"] == "111"
    assert rows[0]["text"] == "status report please"


def test_edited_message_processed(harness):
    u = {"update_id": 4, "edited_message": {
        "chat": {"id": 111}, "from": {"id": 111}, "text": "corrected my decision"}}
    gr.process_updates([u], "tok")
    rows = [r for r in _rows(harness["money"]) if r.get("kind") == "message"]
    assert any(r["text"].startswith("corrected") for r in rows)


def test_dropped_updates_are_visible_in_glass_seen(harness):
    u = {"update_id": 5, "message": {
        "chat": {"id": 555}, "from": {"id": 555}, "text": "hello"}}
    gr.process_updates([u], "tok")
    seen_rows = _rows(harness["seen"] / "glass-seen.jsonl")
    assert seen_rows and seen_rows[-1]["update_id"] == 5
    assert seen_rows[-1]["verdict"] == "chat_not_allowed"
