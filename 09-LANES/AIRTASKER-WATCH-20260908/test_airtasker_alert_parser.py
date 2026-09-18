"""Tests for airtasker_alert_parser (AIRTASKER-WATCH lane, 2026-09-08).

IMPORTANT — fixture honesty: the fixture email below is a MODEL built from the
documented task-alert concept (support articles in CHANNEL-MAP.md). The real
Airtasker alert format has NOT been observed yet (status: unverified). These
tests therefore prove E2-on-designed-input only: the parser behaves
deterministically, fails closed, and fabricates nothing. The real-format E2
gate is: owner saves one real alert email as .eml in this lane folder.
"""
import email.message
import pytest

import airtasker_alert_parser as p


def _msg(fr="alerts@airtasker.com", subj="New painting tasks in Sydney",
         html=None, text=None, date="Tue, 08 Sep 2026 09:00:00 +1000"):
    m = email.message.EmailMessage()
    m["From"] = fr
    m["Subject"] = subj
    m["Date"] = date
    if html:
        m.set_content(html, subtype="html")
    elif text:
        m.set_content(text)
    return m


HTML_ALERT = """<html><body>
<h2>New tasks matching your Painting alert in Sydney</h2>
<ul>
<li><a href="https://www.airtasker.com/tasks/paint-2-bedroom-unit-newtown-1234567">
Paint 2-bedroom unit in Newtown</a> — $600 – $800 — Sydney, NSW</li>
<li><a href="https://www.airtasker.com/tasks/exterior-touch-up-parramatta-7654321">
Exterior touch-up, Parramatta</a> — budget not stated</li>
</ul>
</body></html>"""


def test_sender_gate_non_airtasker_mail_is_untouched():
    m = _msg(fr="friend@example.com")
    assert p.is_airtasker_sender("alerts@airtasker.com") is True
    assert p.is_airtasker_sender("alerts@mail.airtasker.com") is True
    assert p.is_airtasker_sender("friend@example.com") is False
    # gate function itself is the contract; parser on foreign mail = caller's
    # responsibility NOT to call it (documented integration point).


def test_multi_task_alert_parses_designed_input():
    res = p.parse_alert_message(_msg(html=HTML_ALERT))
    assert len(res.tasks) == 2, res.errors
    t1, t2 = res.tasks
    assert t1.task_id == "1234567"
    assert t1.title == "Paint 2-bedroom unit in Newtown"
    assert t1.budget_text == "$600 – $800"
    assert t1.location_text == "Sydney"
    assert t1.supply_risk is False
    # second task has no budget in text → None, never fabricated
    assert t2.budget_text is None
    assert res.received_at == "Tue, 08 Sep 2026 09:00:00 +1000"
    assert res.subject == "New painting tasks in Sydney"


def test_truncated_html_fails_closed_no_fabrication():
    truncated = HTML_ALERT[: len(HTML_ALERT) // 2]  # cut mid-document
    res = p.parse_alert_message(_msg(html=truncated))
    # whatever it finds, every TaskRef must have a real URL; nothing invented
    for t in res.tasks:
        assert t.url.startswith("https://")
        if t.task_id is None:
            assert any(e.startswith("task_id_not_found") for e in res.errors)
    # fields that never appeared stay None
    assert all(t.posted_at is None for t in res.tasks)


def test_empty_body_no_raise_no_tasks():
    res = p.parse_alert_message(_msg())
    assert res.tasks == []
    assert res.errors, "must record why, not fail silently"


def test_supply_side_flagged_not_silent():
    html = ('<a href="https://www.airtasker.com/tasks/painter-available-9999">'
            'Painter available for work in Sydney</a>')
    res = p.parse_alert_message(_msg(html=html))
    assert res.tasks and res.tasks[0].supply_risk is True


def test_dedupe_same_task_once():
    html = (HTML_ALERT + HTML_ALERT)  # same two links twice
    res = p.parse_alert_message(_msg(html=html))
    assert len(res.tasks) == 2


def test_text_only_fallback():
    text = ("New painting tasks:\n"
            "https://www.airtasker.com/tasks/interior-repaint-1112223\n"
            "$450 Sydney NSW")
    res = p.parse_alert_message(_msg(text=text))
    assert len(res.tasks) == 1
    assert res.tasks[0].task_id == "1112223"
    assert res.tasks[0].budget_text == "$450"


def test_card_renders_missing_as_dash():
    t = p.TaskRef(url="https://www.airtasker.com/tasks/x-1")
    card = t.to_card()
    assert "—" in card and t.url in card
