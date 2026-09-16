"""Phase 4 — draft prompt, weekly report formatting, token fields."""
from db import Lead, RunLog
from drafts import build_draft_prompt
from telegram_bot import build_report_text


def test_draft_prompt_contains_lead_specifics_and_compliance():
    lead = Lead(
        source="austender", external_id="x", title="Repaint of Block C",
        description="External facade works", url="https://t.gov.au/1",
        suburb="Parramatta", category="gov", raw_json="", score=90,
        score_reason="", status="new", value_aud=None, deadline=None,
    )
    prompt = build_draft_prompt(lead)
    assert "Repaint of Block C" in prompt
    assert "https://t.gov.au/1" in prompt
    assert "Parramatta" in prompt
    assert "[YOUR NAME]" in prompt
    assert "Spam Act" in prompt
    assert "Subject" in prompt
    assert "150 words" in prompt


def test_report_text_formats():
    txt = build_report_text(
        days=7,
        per_source=[("austender", 5, 72.3), ("planning_alerts", 12, 55.0)],
        statuses=[("new", 10), ("saved", 4), ("skipped", 3)],
        pending_channels=2,
        approved_channels=1,
        hunter_runs=3,
        hunter_tokens=(120000, 8000),
        run_errors=1,
    )
    assert "austender: 5 | 72" in txt
    assert "saved: 4" in txt
    assert "pending 2" in txt and "approved 1" in txt
    assert "120,000" in txt
    assert "errors: 1" in txt


def test_report_text_empty_window():
    txt = build_report_text(7, [], [], 0, 0, 0, (0, 0), 0)
    assert "هیچ لیدی" in txt


def test_runlog_token_fields_default_zero():
    r = RunLog(kind="hunter")
    assert r.tokens_in == 0 and r.tokens_out == 0
