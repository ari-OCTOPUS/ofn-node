# -*- coding: utf-8 -*-
"""آزمون صف تأیید — approve-first با کانال فیک (ADR-006)."""
from core.approval import ApprovalQueueDB
from core.contracts import Channel, OutboxMessage
from core.memory import Memory


class FakeChannel(Channel):
    name = "telegram"

    def __init__(self, ok=True):
        self.sent = []
        self.ok = ok

    def send(self, to_ref, text):
        self.sent.append((to_ref, text))
        return self.ok


def _q(td, ok=True):
    m = Memory(td / "core.db")
    ch = FakeChannel(ok)
    return ApprovalQueueDB(m, {"telegram": ch}), m, ch


def _msg():
    return OutboxMessage(business="ziman", channel="telegram", to_ref="mom", text="سلام مامان")


def test_submit_pending_then_approve(td):
    q, m, ch = _q(td)
    mid = q.submit(_msg())
    assert [p.id for p in q.pending()] == [mid]
    assert ch.sent == []                      # قبل از تأیید هیچ ارسالی نیست
    q.resolve(mid, "approved")
    assert ch.sent == [("mom", "سلام مامان")]
    assert m.get_outbox(mid).status == "sent"
    assert q.pending() == []


def test_edit_then_send(td):
    q, m, ch = _q(td)
    mid = q.submit(_msg())
    q.resolve(mid, "approved", edited_text="سلام — نسخهٔ ویرایش‌شده")
    assert ch.sent[0][1] == "سلام — نسخهٔ ویرایش‌شده"
    assert m.get_outbox(mid).text == "سلام — نسخهٔ ویرایش‌شده"


def test_reject_never_sends(td):
    q, m, ch = _q(td)
    mid = q.submit(_msg())
    q.resolve(mid, "rejected")
    assert ch.sent == []
    assert m.get_outbox(mid).status == "rejected"
    q.resolve(mid, "approved")               # تصمیم دوم روی حل‌شده = بی‌اثر (fail-closed)
    assert ch.sent == []


def test_failed_channel(td):
    q, m, ch = _q(td, ok=False)
    mid = q.submit(_msg())
    q.resolve(mid, "approved")
    assert m.get_outbox(mid).status == "failed"


def test_unknown_channel(td):
    m = Memory(td / "core.db")
    q = ApprovalQueueDB(m, {})
    mid = q.submit(_msg())
    q.resolve(mid, "approved")
    assert m.get_outbox(mid).status == "failed"
