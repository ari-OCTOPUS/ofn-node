"""تست‌های آفلاینِ Lane E/Q — بدون شبکه، بدون ارسال (pytest).
اجرای بورد: python3 -m pytest tests/test_lane_e_q.py -q
"""
import email
import email.policy
import importlib
import json
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "ofn" / "agents"))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "ofn" / "budget"))

import imap_listener as il  # noqa: E402
import rate_card_builder as rcb  # noqa: E402
import lead_email_writer as lew  # noqa: E402

KNOWN = {"amprocurement@det.nsw.edu.au": "lead:x"}


def _msg(frm, subj, body, ctype="text/plain"):
    m = email.message.EmailMessage(policy=email.policy.default)
    m["From"] = frm
    m["Subject"] = subj
    m.set_content(body)
    return m


def test_classify_reply_general():
    m = _msg("AMprocurement@det.nsw.edu.au", "Re: painting",
             "Thanks for the note, we will keep you on file.")
    assert il.classify(m, "amprocurement@det.nsw.edu.au", KNOWN) == (
        "reply", "general", il.classify(m, "amprocurement@det.nsw.edu.au", KNOWN)[2])


def test_classify_quote_request():
    m = _msg("AMprocurement@det.nsw.edu.au", "Re: painting",
             "Please send us a quote for the upcoming scope of works.")
    assert il.classify(m, "amprocurement@det.nsw.edu.au", KNOWN)[1] == "quote_request"


def test_classify_acceptance():
    m = _msg("AMprocurement@det.nsw.edu.au", "Re: quote",
             "We accept your quote, please proceed.")
    assert il.classify(m, "amprocurement@det.nsw.edu.au", KNOWN)[1] == "acceptance"


def test_classify_optout_standalone_stop():
    m = _msg("AMprocurement@det.nsw.edu.au", "Re: painting", "Thanks.\nSTOP")
    assert il.classify(m, "amprocurement@det.nsw.edu.au", KNOWN)[1] == "optout"


def test_classify_optout_not_false_positive():
    # «stop» داخل جملهٔ عادی نباید optout شود
    m = _msg("AMprocurement@det.nsw.edu.au", "Re: painting",
             "Can you stop by the site next week?")
    assert il.classify(m, "amprocurement@det.nsw.edu.au", KNOWN)[1] != "optout"


def test_classify_noise_personal_mail_untouched():
    m = _msg("friend@gmail.com", "hello", "lunch tomorrow?")
    assert il.classify(m, "friend@gmail.com", KNOWN)[0] == "noise"


def test_classify_autoreply_not_engaged():
    # پاسخِ خودکارِ اداری نباید engaged/آلارم شود (کشفِ ۲۰۲۶-۰۹-۰۱ از Transport IAU)
    m = _msg("AMprocurement@det.nsw.edu.au", "Automatic reply: painting",
             "You have reached the information unit. We deal with...")
    assert il.classify(m, "amprocurement@det.nsw.edu.au", KNOWN) == (
        "reply", "autoreply", "automatic reply: painting")


def test_classify_bounce_daemon():
    m = email.message.EmailMessage(policy=email.policy.default)
    m["From"] = "MAILER-DAEMON@transport.nsw.gov.au"
    m["Subject"] = "Undeliverable: Painting quote"
    m.set_content("5.1.1 user unknown")
    assert il.classify(m, "mailer-daemon@transport.nsw.gov.au", KNOWN)[0] == "bounce"


def test_followup_writer_variety_and_gate():
    d1 = lew.write_followup("lead:a", "Transport for NSW", 1)
    d2 = lew.write_followup("lead:b", "HealthShare NSW", 1)
    d3 = lew.write_followup("lead:a", "Transport for NSW", 2)
    assert d1["body"] != d2["body"]
    assert d1["body"] != d3["body"]
    for d in (d1, d2, d3):
        assert not lew.check_followup(d), lew.check_followup(d)
    assert "Re:" not in d1["subject"]  # جعل ترد ممنوع


def test_rate_card_build_and_labels():
    releases = [
        {"tender": {"title": "painting services"},
         "awards": [{"value": {"amount": 100000}}, {"value": {"amount": 250000}}]},
        {"tender": {"title": "cleaning services"},
         "awards": [{"value": {"amount": 50000}}]},
    ]
    card = rcb.build(releases)
    assert card["ocp_derived"]["n_contracts"] == 2  # cleaning حذف شد
    assert card["approved_by_owner"] is False       # قفلِ رأی Q6
    assert "ASSUMPTION" in card["market_assumption"]["_label"]


def test_quote_lock_and_pricing(tmp_path, monkeypatch):
    import quote_engine as qe
    monkeypatch.setattr(qe, "CARD", tmp_path / "card.json")
    card = rcb.build([{"tender": {"title": "painting"},
                       "awards": [{"value": {"amount": 100000}}]}])
    card["approved_by_owner"] = False
    (tmp_path / "card.json").write_text(json.dumps(card), encoding="utf-8")
    # قفل: بدون تأیید مالک، کوت قیمت ندارد
    est = qe.estimate({"area_m2": 500, "kind": "internal"}, qe.load_card())
    assert est["priced"] is False and "not-approved" in est["reason"]
    # بعد از تأیید: قیمت از بازهٔ کارت
    card["approved_by_owner"] = True
    (tmp_path / "card.json").write_text(json.dumps(card), encoding="utf-8")
    est = qe.estimate({"area_m2": 500, "kind": "internal"}, qe.load_card())
    assert est["priced"] is True
    lo, hi = card["market_assumption"]["internal_per_m2_aud"]
    assert lo * 500 <= est["total_aud"] <= hi * 500


def test_quote_style_gate():
    import quote_engine as qe
    bad = {"subject": "s", "body": "we leverage solutions"}
    assert qe.style_gate_ok(bad) is False


def test_followup_due_query(tmp_path, monkeypatch):
    import followup_worker as fw
    db = tmp_path / "p.sqlite"
    c = sqlite3.connect(db)
    c.execute("CREATE TABLE painting_leads (lead_id TEXT, customer_name TEXT, "
              "email TEXT, follow_up_count INT, next_action_at TEXT, "
              "budget_text TEXT, status TEXT)")
    c.execute("INSERT INTO painting_leads VALUES (?,?,?,?,?,?,?)",
              ("lead:due", "X", "x@x.gov.au", 0, "2026-08-30 00:00:00", "", "contacted"))
    c.execute("INSERT INTO painting_leads VALUES (?,?,?,?,?,?,?)",
              ("lead:fut", "Y", "y@y.gov.au", 0, "2026-12-30 00:00:00", "", "contacted"))
    c.execute("INSERT INTO painting_leads VALUES (?,?,?,?,?,?,?)",
              ("lead:max", "Z", "z@z.gov.au", 2, "2026-08-30 00:00:00", "", "contacted"))
    c.commit(); c.close()
    monkeypatch.setattr(fw, "PAINTING_DB", db)
    due = fw.due_leads("2026-09-01T00:00:00Z")
    ids = [d["lead_id"] for d in due]
    assert ids == ["lead:due"]  # future نه، دوبار‌رفته نه
