# -*- coding: utf-8 -*-
"""آزمون Memory Layer — رفت‌وبرگشت همهٔ جدول‌ها."""
from core.contracts import Brief, Feedback, OutboxMessage
from core.memory import Memory


def _mem(td):
    return Memory(td / "core.db")


def test_brief_roundtrip_and_notify(td):
    m = _mem(td)
    bid = m.add_brief(Brief(business="ziman", title="t", opportunity="o",
                            why="w", action="a", source="s"))
    assert bid == 1
    un = m.unnotified_briefs()
    assert len(un) == 1 and un[0].title == "t"
    m.mark_brief_notified(bid)
    assert m.unnotified_briefs() == []
    assert m.recent_briefs(5)[0].id == bid


def test_feedback_loop(td):
    m = _mem(td)
    bid = m.add_brief(Brief(business="ziman", title="t", opportunity="o",
                            why="w", action="a", source="s"))
    m.add_feedback(Feedback(brief_id=bid, useful=True))
    m.add_feedback(Feedback(brief_id=bid, useful=False, note="تکراری"))
    fbs = m.feedback_for("ziman")
    assert len(fbs) == 2 and fbs[0].note == "تکراری"
    assert m.feedback_for("painting") == []


def test_outbox_states(td):
    m = _mem(td)
    mid = m.add_outbox(OutboxMessage(business="ziman", channel="telegram",
                                     to_ref="mom", text="سلام"))
    assert m.pending_outbox()[0].id == mid
    assert len(m.unnotified_outbox()) == 1
    m.mark_outbox_notified(mid)
    assert m.unnotified_outbox() == []          # ولی هنوز pending است
    assert len(m.pending_outbox()) == 1
    m.set_outbox(mid, "sent", text="سلام ویرایش‌شده")
    assert m.pending_outbox() == []
    assert m.get_outbox(mid).status == "sent"
    assert m.get_outbox(mid).text == "سلام ویرایش‌شده"


def test_cache_and_usage(td):
    m = _mem(td)
    k = m.cache_key("prompt-x")
    assert m.cache_get(k) is None
    m.cache_put(k, "جواب")
    assert m.cache_get(k) == "جواب"
    m.usage_add("deepseek", 1000, 500, 0.001, "ziman")
    m.usage_add("fugu", 10000, 2000, 0.11)
    assert m.day_cost("deepseek") > 0
    assert m.month_cost("fugu") == 0.11
    st = m.stats()
    assert st["fugu_month"] == 0.11 and st["briefs"] == 0
