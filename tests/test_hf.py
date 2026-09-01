"""تست‌های پذیرش هات‌فیکس‌ها (حکم ناظر ۲۰۲۶-09-02، §۵ و §۹).

HF-1: سقف مبلغ نهایی + کف متراژ → needs_owner_review (نه ارسال)
HF-2: rollback دیتابیس نباید ارسالِ تکراری بسازد — تستِ صریحِ ناظر
HF-3: هر رکورد کوت card_sha256 و fingerprint دارد
"""
import json
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "ofn" / "agents"))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "ofn" / "budget"))

import pytest  # noqa: E402

import quote_engine as qe  # noqa: E402
import quote_fingerprint as qfp  # noqa: E402
import rate_card_builder as rcb  # noqa: E402


@pytest.fixture
def env(tmp_path, monkeypatch):
    """محیط ایزوله: دیتابیس/کارت/fingerprint همه در tmp."""
    db = tmp_path / "p.sqlite"
    c = sqlite3.connect(db)
    c.execute("CREATE TABLE painting_leads (lead_id TEXT PRIMARY KEY, "
              "customer_name TEXT, email TEXT, status TEXT, next_action TEXT, "
              "next_action_at TEXT, follow_up_count INT, last_follow_up_at TEXT, "
              "budget_text TEXT)")
    c.execute("INSERT INTO painting_leads VALUES "
              "('lead:t1','Transport for NSW','x@transport.nsw.gov.au',"
              "'review','quote requested',NULL,0,NULL,'')")
    c.commit(); c.close()
    card = rcb.build([{"tender": {"title": "painting"},
                       "awards": [{"value": {"amount": 100000}}]}])
    card["approved_by_owner"] = True
    cardp = tmp_path / "card.json"
    cardp.write_text(json.dumps(card), encoding="utf-8")
    fpp = tmp_path / "fp.jsonl"
    monkeypatch.setattr(qe, "PAINTING_DB", db)
    monkeypatch.setattr(qe, "CARD", cardp)
    monkeypatch.setattr(qfp, "FP_FILE", fpp)
    return {"db": db, "card": cardp, "fp": fpp, "card_obj": card}


def test_hf1_over_cap_goes_to_review_not_send(env, monkeypatch):
    # ۵٬۰۰۰م² × ~$36.5 = ~$۱۸۲٬۰۰۰ — بالای سقف $۲۵٬۰۰۰
    sent = {}
    monkeypatch.setattr(qe.cap, "verified_send",
                        lambda *a, **k: sent.setdefault("called", True))
    res = qe.quote("lead:t1", {"area_m2": 5000, "kind": "internal",
                               "works": "w", "location": "l"})
    assert res["status"] == "needs_owner_review"
    assert res["reason"] == "over-quote-cap"
    assert res["total_aud"] > qe.QUOTE_MAX_AUD
    assert "called" not in sent  # هیچ تلاشِ ارسانی نشد
    assert qfp.seen(qfp.fingerprint(
        "lead:t1", {"area_m2": 5000, "kind": "internal", "works": "w",
                    "location": "l"}, res["total_aud"]), env["fp"])


def test_hf1_under_min_area_goes_to_review(env, monkeypatch):
    # ۱۰م² زیر کف ۲۰ — احتمالاً پارس اشتباه
    sent = {}
    monkeypatch.setattr(qe.cap, "verified_send",
                        lambda *a, **k: sent.setdefault("called", True))
    res = qe.quote("lead:t1", {"area_m2": 10, "kind": "internal",
                               "works": "w", "location": "l"})
    assert res["reason"] == "under-min-area"
    assert "called" not in sent


def test_hf1_normal_quote_still_flows(env, monkeypatch):
    # ۳۰۰م² = ~$۱۰٬۹۵۰ — زیر سقف، بالای کف: مسیر عادی (ارسال ماک‌شده)
    monkeypatch.setattr(qe.cap, "request_send_token",
                        lambda cand, purpose: ({"stub": True}, "ok"))
    monkeypatch.setattr(qe.cap, "verified_send",
                        lambda tok, cand, draft, purpose: {"sent": True,
                                                           "status": "SENT"})
    res = qe.quote("lead:t1", {"area_m2": 300, "kind": "internal",
                               "works": "w", "location": "l"})
    assert res.get("sent") is True
    c = sqlite3.connect(env["db"])
    row = c.execute("SELECT status, card_sha256, fingerprint, total_aud "
                    "FROM painting_quotes WHERE lead_id='lead:t1'").fetchone()
    c.close()
    assert row[0] == "sent"
    assert row[1]  # HF-3: hash کارت در رکورد
    assert row[2]  # HF-2: fingerprint در رکورد
    assert 8000 <= row[3] <= 15000


def test_hf2_rollback_does_not_resend(env, monkeypatch):
    """تستِ صریحِ ناظر: دیتابیس به «بکاپ» برگردد + اجرای دوباره = تکرار ممنوع."""
    monkeypatch.setattr(qe.cap, "request_send_token",
                        lambda cand, purpose: ({"stub": True}, "ok"))
    calls = []
    monkeypatch.setattr(qe.cap, "verified_send",
                        lambda tok, cand, draft, purpose:
                        calls.append(draft) or {"sent": True, "status": "SENT"})
    scope = {"area_m2": 300, "kind": "internal", "works": "w", "location": "l"}
    r1 = qe.quote("lead:t1", scope)
    assert r1.get("sent") is True and len(calls) == 1
    # ── شبیه‌سازی rollback: دیتابیس به snapshot پیش از کوت برمی‌گردد ──
    c = sqlite3.connect(env["db"])
    c.execute("DELETE FROM painting_quotes")
    c.execute("UPDATE painting_leads SET next_action='quote requested' "
              "WHERE lead_id='lead:t1'")
    c.commit(); c.close()
    r2 = qe.quote("lead:t1", scope)
    assert r2.get("status") == "DUPLICATE_BLOCKED", r2
    assert r2.get("error") == "duplicate-fingerprint-rollback-guard"
    assert len(calls) == 1  # هیچ ارسالِ دومی نیست — fingerprint بیرون از DB زنده است


def test_hf3_card_hash_recorded_and_stable(env, monkeypatch):
    monkeypatch.setattr(qe.cap, "request_send_token",
                        lambda cand, purpose: ({"stub": True}, "ok"))
    monkeypatch.setattr(qe.cap, "verified_send",
                        lambda tok, cand, draft, purpose: {"sent": True,
                                                           "status": "SENT"})
    qe.quote("lead:t1", {"area_m2": 400, "kind": "internal",
                         "works": "w", "location": "l"})
    c = sqlite3.connect(env["db"])
    sha_in_record = c.execute("SELECT card_sha256 FROM painting_quotes "
                              "WHERE lead_id='lead:t1'").fetchone()[0]
    c.close()
    import hashlib
    expect = hashlib.sha256(env["card"].read_bytes()).hexdigest()
    assert sha_in_record == expect  # گرهِ کوت به نسخهٔ دقیقِ کارت
