"""test_lead_candidate_inbox.py — Trust-Engine P0: برشِ عمودیِ synthetic (D5).

مسیرِ synthetic: لید → validate → firewall → dedup → receipt → routing. صفر ارسالِ بیرونی.
نامتغیرها: market_signal فایلِ کاندیدِ top-level نمی‌سازد؛ در halt فقط receipt؛ نامعتبر→quarantine
(هرگز حذف)؛ idempotency هیچ لیدِ دومی نمی‌سازد؛ external_send_allowed همیشه False از inbox؛
خروجیِ آداپتر توسطِ lead_sense.read_inbox واقعاً مصرف می‌شود (قوسِ موجود).
"""
import json
import os
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE.parent))
sys.path.insert(0, str(_HERE.parent / "budget"))
sys.path.insert(0, str(_HERE.parent / "legs"))

import harness
ENV = harness.setup("lead-candidate-inbox")

import importlib                       # noqa: E402
import opslib                          # noqa: E402
import consent_firewall               # noqa: E402
importlib.reload(consent_firewall)
import lead_candidate_inbox as lci     # noqa: E402
importlib.reload(lci)
import lead_sense                      # noqa: E402
importlib.reload(lead_sense)


def _syn(external_id="syn-1", scope="interior painting 3br Mosman", channel="synthetic_test"):
    return {
        "schema_version": "1.1",
        "source": {"channel": channel, "source_id": "owner", "external_id": external_id,
                   "received_at": "2026-07-21T10:00:00Z"},
        "candidate_type": "consented_inbound",
        "consent": {"basis": "explicit", "evidence": "submitted_quote_form"},
        "contact": {"name": "TEST", "organisation": None},
        "property": {"address": None, "suburb": "Mosman"},
        "request": {"service": "interior painting", "scope_text": scope, "urgency": "flexible"},
    }


def _clear():
    os.environ.pop(lci.FLAG, None)


def _top_level_candidates():
    box = opslib.STATE_DIR / "legs" / "lead-inbox"
    return sorted(p.name for p in box.glob("*.json")) if box.is_dir() else []


def t_a_flag_off_is_noop():
    _clear()
    assert lci.enabled() is False
    r = lci.submit_candidate(_syn())
    assert r["ok"] is False and r["status"] == "gate_off"
    assert not (opslib.STATE_DIR / "legs" / "lead-inbox").exists()


def t_b_synthetic_accepted_full_journey():
    os.environ[lci.FLAG] = "1"
    r = lci.submit_candidate(_syn(external_id="syn-b"), source_id="owner")
    assert r["ok"] is True and r["status"] == "accepted", r
    assert r["lead_id"] and r["candidate_type"] == "consented_inbound"
    # فایلِ کاندید نوشته شد با description ناخالی + نشانِ synthetic + external_send=False
    box = opslib.STATE_DIR / "legs" / "lead-inbox"
    files = list(box.glob(f"{r['lead_id']}.json"))
    assert len(files) == 1, files
    data = json.loads(files[0].read_text("utf-8"))
    assert data["description"].strip()
    assert data["candidate"]["synthetic"] is True
    assert data["candidate"]["workflow"]["external_send_allowed"] is False
    # receipt نوشته شد
    ev = opslib.STATE_DIR / "legs" / "lead-inbox" / "events.jsonl"
    recs = [json.loads(l) for l in open(ev, encoding="utf-8")]
    assert any(x["event_type"] == "lead.candidate.received" and
               x["correlation_id"] == r["lead_id"] for x in recs)


def t_c_lead_sense_consumes_the_written_candidate():
    """اثباتِ اتصال: خروجیِ آداپتر را قوسِ موجود (lead_sense.read_inbox) واقعاً می‌خواند."""
    os.environ[lci.FLAG] = "1"
    r = lci.submit_candidate(_syn(external_id="syn-c", scope="repaint hallway"), source_id="owner")
    assert r["ok"]
    seen = lead_sense.read_inbox()
    assert any(d.get("lead_id") == r["lead_id"] and d.get("description")
               for _, d in seen), "lead_sense باید کاندیدِ نوشته‌شده را ببیند"


def t_d_invalid_quarantined_never_deleted():
    os.environ[lci.FLAG] = "1"
    bad = _syn(external_id="syn-d")
    bad["request"]["scope_text"] = "   "        # scope خالی → نامعتبر
    bad.pop("description", None)
    before = _top_level_candidates()
    r = lci.submit_candidate(bad, source_id="owner")
    assert r["ok"] is False and r["status"] == "quarantined", r
    # هیچ فایلِ کاندیدِ top-level اضافه نشد
    assert _top_level_candidates() == before
    # بدنه + سایدکارِ دلیل در quarantine (هرگز حذف)
    q = opslib.STATE_DIR / "legs" / "lead-inbox" / "quarantine"
    assert q.is_dir() and any(p.name.endswith(".reason.json") for p in q.iterdir())


def t_e_idempotency_no_second_lead():
    os.environ[lci.FLAG] = "1"
    c = _syn(external_id="syn-e-dupe")
    r1 = lci.submit_candidate(c, source_id="owner")
    r2 = lci.submit_candidate(c, source_id="owner")
    assert r1["ok"] and r1["status"] == "accepted"
    assert r2["ok"] and r2["status"] == "duplicate", r2
    assert r2["lead_id"] == r1["lead_id"]           # همان لید، نه دومی
    box = opslib.STATE_DIR / "legs" / "lead-inbox"
    assert len(list(box.glob(f"{r1['lead_id']}.json"))) == 1


def t_f_market_signal_makes_no_top_level_candidate():
    """اصلاحِ B2: market_signal فایلِ کاندیدِ top-level نمی‌سازد → وارد قوسِ draft نمی‌شود."""
    os.environ[lci.FLAG] = "1"
    sig = {
        "schema_version": "1.1",
        "source": {"channel": "nsw_da", "source_id": "n8n_da", "external_id": "DA-100",
                   "received_at": "2026-07-21T06:00:00Z"},
        "candidate_type": "market_signal",
        "consent": {"basis": "none"},
        "request": {"scope_text": "DA approved: alterations & additions"},
    }
    before = set(_top_level_candidates())
    r = lci.submit_candidate(sig, source_id="n8n_da")
    assert r["ok"] and r["status"] == "signal_recorded", r
    assert r["outreach_allowed"] is False
    # هیچ کاندیدِ top-level نو → lead_sense هرگز draftش نمی‌کند
    assert set(_top_level_candidates()) == before
    # در signals/ ثبت شد
    sigs = opslib.STATE_DIR / "legs" / "lead-inbox" / "signals"
    assert sigs.is_dir() and any(p.suffix == ".json" for p in sigs.iterdir())


def t_g_halt_writes_receipt_only_zero_state():
    os.environ[lci.FLAG] = "1"
    stop = opslib.STOP_ORGANISM
    stop.parent.mkdir(parents=True, exist_ok=True)
    stop.write_text("stop", "utf-8")
    try:
        before = _top_level_candidates()
        r = lci.submit_candidate(_syn(external_id="syn-halt"), source_id="owner")
        assert r["ok"] is False and r["status"] == "halted", r
        assert _top_level_candidates() == before      # صفر جهشِ state
        ev = opslib.STATE_DIR / "legs" / "lead-inbox" / "events.jsonl"
        recs = [json.loads(l) for l in open(ev, encoding="utf-8")]
        assert any(x["payload"].get("outcome") == "halted_refused" for x in recs)   # receipt هست
    finally:
        try:
            stop.unlink()
        except OSError:
            pass


def t_h_no_external_send_surface():
    """ساختاری: آداپتر هیچ سطحِ ارسال/شبکه import نمی‌کند؛ external_send همیشه False."""
    src = Path(lci.__file__).read_text("utf-8")
    for bad in ("import smtplib", "import requests", "twilio", "sendgrid",
                "urllib.request", "http.client", "socket.socket"):
        assert bad not in src, f"سطحِ ارسال ممنوع: {bad}"
    # external_send_allowed هرگز True نوشته نمی‌شود
    assert '"external_send_allowed": True' not in src
    assert "external_send_allowed = True" not in src


if __name__ == "__main__":
    checks = [(n, f) for n, f in sorted(globals().items()) if n.startswith("t_")]
    failed = harness.run(checks)
    print(f"\n{'✅' if not failed else '❌'} test_lead_candidate_inbox: "
          f"{len(checks) - failed}/{len(checks)}")
    sys.exit(1 if failed else 0)
