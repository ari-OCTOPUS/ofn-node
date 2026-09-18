"""AIRTASKER-WIRE integration tests — patched imap_listener (138-base) + intake.

Proves TWO things per owner order:
1) چیز اولی حذف/تغییر نکرده: regression — every pre-existing classify()/_act
   behaviour identical to 138 runtime base (fixtures mirror listener contract).
2) اتصال واقعی کار می‌کند: airtasker sender → alert branch → intake insert
   (tmp DB) → dedupe → supply_risk skip → dry writes nothing.

No network, no real Gmail, no real Telegram (owner_notify faked).
"""
from __future__ import annotations

import email
import email.policy
import json
import sqlite3
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).parent
DEPLOY = HERE / "deploy"
OFN_LAPTOP = Path("F:/ofn-node/ofn")
# order matters: deploy must WIN for imap_listener/airtasker_*; laptop clone
# only supplies opslib/memory_chain deps. (insert(0) reverses — deploy last.)
for p in (str(OFN_LAPTOP / "agents"), str(OFN_LAPTOP / "budget")):
    if p not in sys.path:
        sys.path.insert(0, p)
sys.path.insert(0, str(DEPLOY))

import imap_listener  # noqa: E402  (patched, 138-base)
import airtasker_intake  # noqa: E402
import airtasker_alert_parser as parser  # noqa: E402


# ── fixtures ────────────────────────────────────────────────────────────────

def _msg(fr, subj="hello", body="plain text body", html=None, rpt=False):
    if rpt:
        raw = (
            "From: MAILER-DAEMON@x.com\r\n"
            "Subject: Undeliverable: test\r\n"
            "Content-Type: multipart/report; report-type=delivery-status;"
            " boundary=\"BB\"\r\n\r\n"
            "--BB\r\nContent-Type: text/plain\r\n\r\nfailed\r\n"
            "--BB\r\nContent-Type: message/delivery-status\r\n\r\n"
            "Final-Recipient: rfc822;a@b.c\r\n"
            "--BB--\r\n")
        return email.message_from_string(raw, policy=email.policy.default)
    m = email.message.EmailMessage()
    m["From"] = fr
    m["Subject"] = subj
    if html:
        m.set_content(html, subtype="html")
    else:
        m.set_content(body)
    return m


KNOWN = {"lead@example.com": "L1"}

LEADS_DDL = """
CREATE TABLE IF NOT EXISTS painting_leads (
    lead_id TEXT PRIMARY KEY, tenant_id TEXT NOT NULL DEFAULT 'lead',
    source TEXT NOT NULL, source_ref TEXT NOT NULL DEFAULT '',
    customer_name TEXT NOT NULL DEFAULT '', phone TEXT NOT NULL DEFAULT '',
    email TEXT NOT NULL DEFAULT '', suburb TEXT NOT NULL DEFAULT '',
    budget_text TEXT NOT NULL DEFAULT '', message TEXT NOT NULL DEFAULT '',
    temperature TEXT NOT NULL DEFAULT 'new'
      CHECK (temperature IN ('hot','warm','cold','new')),
    status TEXT NOT NULL DEFAULT 'new'
      CHECK (status IN ('new','review','contacted','quoted','won','lost','spam','archived')),
    created_at TEXT NOT NULL, updated_at TEXT NOT NULL,
    notes TEXT NOT NULL DEFAULT '',
    score INTEGER NOT NULL DEFAULT 0)
"""


class _FakeOwnerNotify:
    calls = []

    @classmethod
    def alert_owner(cls, text):
        cls.calls.append(text)


@pytest.fixture()
def sandbox(tmp_path, monkeypatch):
    """tmp DB + tmp receipt file + fake telegram; real code paths otherwise."""
    db = tmp_path / "painting.sqlite"
    con = sqlite3.connect(db)
    con.executescript(LEADS_DDL)
    con.commit()
    con.close()
    monkeypatch.setenv("AIRTASKER_INTAKE_DB", str(db))
    monkeypatch.setattr(airtasker_intake, "EVENTS_PATH",
                        tmp_path / "events.jsonl")
    fake = sys.modules.get("owner_notify") or type(sys)("owner_notify")
    fake.alert_owner = _FakeOwnerNotify.alert_owner
    sys.modules["owner_notify"] = fake
    _FakeOwnerNotify.calls.clear()
    return db


ALERT_HTML = """<html><body><ul>
<li><a href="https://www.airtasker.com/tasks/paint-unit-newtown-1234567">
Paint unit in Newtown</a> — $600 – $800 — Sydney, NSW</li>
<li><a href="https://www.airtasker.com/tasks/exterior-parramatta-7654321">
Exterior touch-up, Parramatta</a> — Sydney</li>
<li><a href="https://www.airtasker.com/tasks/painter-available-9999">
Painter available for work Sydney</a> — $50/hr</li>
</ul></body></html>"""


def _alert_msg():
    return _msg("task-alerts@airtasker.com", "New painting tasks in Sydney",
                html=ALERT_HTML)


# ── 1) regression: nothing removed / changed for old paths ─────────────────

def test_regression_bounce_dsn():
    m = _msg("MAILER-DAEMON@x.com", "Undeliverable: …", rpt=True)
    assert imap_listener.classify(m, "mailer-daemon@x.com", KNOWN) == (
        "bounce", "dsn", "delivery-status")


def test_regression_known_reply_general():
    m = _msg("lead@example.com", "Re: quote", "thanks, call me")
    k, i, detail = imap_listener.classify(m, "lead@example.com", KNOWN)
    assert (k, i) == ("reply", "general")
    assert detail.startswith("thanks, call me")  # set_content adds trailing \n


def test_regression_known_quote_request():
    m = _msg("lead@example.com", "hi", "can you send a quote for painting?")
    k, i, _ = imap_listener.classify(m, "lead@example.com", KNOWN)
    assert (k, i) == ("reply", "quote_request")


def test_regression_known_acceptance():
    m = _msg("lead@example.com", "hi", "we accept, please proceed")
    k, i, _ = imap_listener.classify(m, "lead@example.com", KNOWN)
    assert (k, i) == ("reply", "acceptance")


def test_regression_optout():
    m = _msg("lead@example.com", "hi", "STOP")
    k, i, _ = imap_listener.classify(m, "lead@example.com", KNOWN)
    assert (k, i) == ("reply", "optout")


def test_regression_autoreply_subject():
    m = _msg("lead@example.com", "Automatic reply: out of office")
    k, i, _ = imap_listener.classify(m, "lead@example.com", KNOWN)
    assert (k, i) == ("reply", "autoreply")


def test_regression_unknown_personal_sender_still_noise_untouched():
    m = _msg("friend@example.com", "dinner?", "see you at 8")
    assert imap_listener.classify(m, "friend@example.com", KNOWN) == (
        "noise", "", "")


def test_regression_act_dry_returns_before_any_write():
    m = _msg("friend@example.com")
    res = imap_listener._act("noise", "", "friend@example.com", "", "", m,
                             KNOWN, dry=True)
    assert res.get("dry") is True


# ── 2) new branch: airtasker → alert ───────────────────────────────────────

def test_airtasker_sender_classified_as_alert():
    k, i, _ = imap_listener.classify(_alert_msg(), "task-alerts@airtasker.com",
                                     KNOWN)
    assert (k, i) == ("alert", "airtasker")


def test_airtasker_subdomain_sender_ok():
    m = _msg("alerts@mail.airtasker.com")
    k, i, _ = imap_listener.classify(m, "alerts@mail.airtasker.com", KNOWN)
    assert (k, i) == ("alert", "airtasker")


def test_act_alert_branch_dry_writes_nothing(sandbox):
    res = imap_listener._act("alert", "airtasker", "task-alerts@airtasker.com",
                             "", "", _alert_msg(), KNOWN, dry=True)
    assert res["dry"] is True and res["tasks_seen"] == 3
    assert res["supply_risk_skipped"] == 1
    assert res["would_insert"] and "1234567" in res["would_insert"][0]
    assert not sandbox.exists() or sqlite3.connect(sandbox).execute(
        "select count(*) from painting_leads").fetchone()[0] == 0
    assert not _FakeOwnerNotify.calls


def test_act_alert_branch_live_insert_and_dedupe(sandbox):
    res1 = imap_listener._act("alert", "airtasker",
                              "task-alerts@airtasker.com", "", "",
                              _alert_msg(), KNOWN, dry=False)
    assert res1["inserted"] == 2 and res1["dupes"] == 0
    assert res1["supply_risk_skipped"] == 1
    assert res1["cards_sent"] == 2
    con = sqlite3.connect(sandbox)
    rows = con.execute("select lead_id, budget_text, suburb, status, temperature"
                       " from painting_leads order by lead_id").fetchall()
    con.close()
    assert rows == [("at:1234567", "$600 – $800", "Sydney", "new", "new"),
                    ("at:7654321", "", "Sydney", "new", "new")]
    # idempotent: same email again → dupes, no double insert
    res2 = imap_listener._act("alert", "airtasker",
                              "task-alerts@airtasker.com", "", "",
                              _alert_msg(), KNOWN, dry=False)
    assert res2["inserted"] == 0 and res2["dupes"] == 2


def test_supply_risk_never_becomes_lead(sandbox):
    html = ('<a href="https://www.airtasker.com/tasks/painter-available-1">'
            'Painter available for work</a>')
    m = _msg("alerts@airtasker.com", "x", html=html)
    res = imap_listener._act("alert", "airtasker", "alerts@airtasker.com",
                             "", "", m, KNOWN, dry=False)
    assert res["supply_risk_skipped"] == 1 and res["inserted"] == 0


def test_receipt_chain_written(sandbox, tmp_path):
    imap_listener._act("alert", "airtasker", "task-alerts@airtasker.com",
                       "", "", _alert_msg(), KNOWN, dry=False)
    p = tmp_path / "events.jsonl"
    assert p.exists()
    lines = [json.loads(x) for x in p.read_text(encoding="utf-8").splitlines()]
    kinds = {l["event_type"] for l in lines}
    assert "airtasker.alert_seen" in kinds
    assert "airtasker.email_processed" in kinds


def test_parser_importable_and_pure():
    # sanity: parser module in deploy == tested module contract
    assert parser.is_airtasker_sender("a@airtasker.com")
    assert not parser.is_airtasker_sender("a@evil-airtasker.com.evil.net")


def test_score_rule_populated(sandbox):
    res = imap_listener._act("alert", "airtasker", "task-alerts@airtasker.com",
                             "", "", _alert_msg(), KNOWN, dry=False)
    assert res["inserted"] == 2
    import sqlite3
    con = sqlite3.connect(sandbox)
    scores = con.execute("select lead_id, score from painting_leads order by lead_id").fetchall()
    con.close()
    assert scores == [("at:1234567", 100), ("at:7654321", 60)]  # budget+loc+id+demand / loc+id+demand
