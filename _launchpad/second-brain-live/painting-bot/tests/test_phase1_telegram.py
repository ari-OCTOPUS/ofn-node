"""Phase 1 — telegram formatting, escaping and action-command routing."""
from db import Channel, Lead
from telegram_bot import ACTION_RE, _format_channel, _format_lead, esc


def _lead(**kw):
    base = dict(
        id=7, source="planning_alerts", external_id="x",
        title='<b>50% & "off" *deal*_[x]', description="d",
        url="https://x.au/?a=1&b=2", value_aud=150000, deadline=None,
        suburb="Bondi & Co <NSW>", category="strata_remedial",
        raw_json="", score=88, score_reason="action=draft | strata match",
        status="new",
    )
    base.update(kw)
    return Lead(**base)


def test_action_regex():
    assert ACTION_RE.match("/save_12").groups() == ("save", "12")
    assert ACTION_RE.match("/approve_3@paintbot").groups() == ("approve", "3")
    assert ACTION_RE.match("/saved_12") is None
    assert ACTION_RE.match("/save_") is None
    assert ACTION_RE.match("/new") is None


def test_esc():
    assert esc('<b>&"x"') == '&lt;b&gt;&amp;"x"'
    assert esc(None) == ""


def test_format_lead_escapes_hostile_fields():
    out = _format_lead(_lead())
    assert "&lt;b&gt;50% &amp;" in out
    assert "<b>50%" not in out
    assert "Bondi &amp; Co &lt;NSW&gt;" in out
    assert "a=1&amp;b=2" in out
    assert "~$150,000 AUD" in out


def test_format_lead_button_order_follows_action():
    out = _format_lead(_lead())
    assert out.rstrip().splitlines()[-1].startswith("/draft_7")
    out2 = _format_lead(_lead(id=9, score_reason="action=save | ok"))
    assert out2.rstrip().splitlines()[-1].startswith("/save_9")


def test_format_channel_escaped_with_buttons():
    ch = Channel(
        id=3, name="A<b>&B", type="strata", url="https://c.au", access="api",
        cost_to_enter="free", lead_volume="high", typical_value="$50K",
        competition="low", geo="Sydney", sample_lead="",
        notes="note <i>x</i> & y", score=70, status="pending",
        discovered_at=None, approved_at=None,
    )
    out = _format_channel(ch)
    assert "A&lt;b&gt;&amp;B" in out
    assert "/approve_3" in out and "/reject_3" in out
