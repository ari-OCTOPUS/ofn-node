"""تست‌های دندان (نقشهٔ سند تلاقی، گام ۳ — انضباط teeth).

«بررسی‌کننده‌ای که نمی‌تواند شکست بخورد چیزی را اثبات نمی‌کند» — هر invariant
reconcile با یک حالتِ عمداً خراب همراه شده و تست می‌کند checker آن را بگیرد.
همچنین: توکنِ دست‌کاری‌شده/منقضی باید رد شود؛ زنجیرهٔ حافظهٔ دست‌کاری‌شده
باید chain_verify را قرمز کند.
"""
import importlib
import json
import sqlite3
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "ofn" / "agents"))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "ofn" / "budget"))

import capability_token as cap  # noqa: E402
import memory_chain  # noqa: E402

RECONCILE = Path(__file__).resolve().parent.parent / "tools" / "reconcile.py"
spec = importlib.util.spec_from_file_location("reconcile_mod", RECONCILE)
rc = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rc)


def _mk_db(tmp_path, wal_rows=(), counter=None, leads=()):
    wal = tmp_path / "wal.sqlite"
    c = sqlite3.connect(wal)
    c.execute("CREATE TABLE outbound_effects (effect_id TEXT, lead_id TEXT, "
              "payload_hash TEXT, state TEXT, provider_message_id TEXT, "
              "attempt_count INT, reason TEXT, created_at TEXT, updated_at TEXT)")
    today = time.strftime("%Y-%m-%d")
    for i, state in enumerate(wal_rows):
        c.execute("INSERT INTO outbound_effects VALUES (?,?,?,?,?,?,?,?,?)",
                  (f"e{i}", f"lead:{i}", "h", state, None, 1, None, today, today))
    c.commit(); c.close()
    paint = tmp_path / "paint.sqlite"
    c = sqlite3.connect(paint)
    c.execute("CREATE TABLE painting_leads (lead_id TEXT, status TEXT, "
              "email TEXT, next_action TEXT)")
    for lid, status, na in leads:
        c.execute("INSERT INTO painting_leads VALUES (?,?,?,?)",
                  (lid, status, lid + "@x.gov.au", na))
    c.commit(); c.close()
    return wal, paint


def _run(monkeypatch, tmp_path, wal_rows, counter, events_text="", leads=()):
    wal, paint = _mk_db(tmp_path, wal_rows, counter, leads)
    events = tmp_path / "events.jsonl"
    events.write_text(events_text, encoding="utf-8")
    ox = tmp_path / "outbox.sqlite"
    c = sqlite3.connect(ox)
    c.execute("CREATE TABLE outbox (tenant TEXT, idem_key TEXT, kind TEXT, "
              "payload TEXT, tier TEXT, status TEXT)")
    for i, state in enumerate(wal_rows):
        c.execute("INSERT INTO outbox VALUES ('lead', ?, 'k', '{}', 'GREEN', 'sent')",
                  (f"lead-quote:lead:{i}",))
    c.commit(); c.close()
    monkeypatch.setattr(rc, "WAL", wal)
    monkeypatch.setattr(rc, "PAINT", paint)
    monkeypatch.setattr(rc, "EVENTS", events)
    monkeypatch.setattr(rc, "OUTBOX", ox)
    monkeypatch.setattr(rc, "_counter", lambda: counter)
    return rc.run()


def test_tooth_R1_counter_drift_detected(tmp_path, monkeypatch):
    # شمارنده ۳ ولی WAL فقط ۲ sent — checker باید قرمز شود
    rep = _run(monkeypatch, tmp_path, ["sent", "sent"], counter=3)
    assert rep["checks"]["R1_counter_eq_wal_today"]["match"] is False
    assert rep["ok"] is False


def test_tooth_R1_healthy_case_passes(tmp_path, monkeypatch):
    today = time.strftime("%Y-%m-%d")
    ev = "\n".join(
        json.dumps({"event_type": "communication.sent",
                    "occurred_at": f"{today}T12:00:0{i}Z", "payload": {}})
        for i in (1, 2))
    rep = _run(monkeypatch, tmp_path, ["sent", "sent"], counter=2,
               events_text=ev,
               leads=[("lead:a", "contacted", "await reply")])
    assert rep["checks"]["R1_counter_eq_wal_today"]["match"] is True
    assert rep["checks"]["R2_events_today"]["match"] is True
    assert rep["ok"] is True


def test_tooth_R6_nonfinal_wal_detected(tmp_path, monkeypatch):
    # یک افکت در حالت 'sending' رها شده — checker باید بگیرد
    rep = _run(monkeypatch, tmp_path, ["sent", "sending"], counter=1)
    assert rep["checks"]["R6_wal_no_nonfinal"]["match"] is False
    assert rep["ok"] is False


def test_tooth_R5_suppressed_lead_in_cycle(tmp_path, monkeypatch):
    rep = _run(monkeypatch, tmp_path, ["sent"], counter=1,
               leads=[("lead:s", "contacted", "do not contact")])
    assert rep["checks"]["R5_no_suppressed_in_cycle"]["violations"] == 1


def test_token_tamper_detected():
    tok = cap.issue("send_email", "x@nsw.gov.au", "test")
    ok, why = cap.verify(tok, "send_email", "x@nsw.gov.au")
    assert ok
    tok2 = dict(tok); tok2["subject"] = "victim@attacker.com"  # سوییچ قربانی
    ok, why = cap.verify(tok2, "send_email", "victim@attacker.com")
    assert not ok and why == "bad-mac"
    ok, why = cap.verify(tok, "send_email", "other@nsw.gov.au")
    assert not ok and why == "subject-mismatch"


def test_token_expired():
    tok = cap.issue("send_email", "y@nsw.gov.au", "test", ttl_s=-1)
    ok, why = cap.verify(tok, "send_email", "y@nsw.gov.au")
    assert not ok and why == "expired"


def test_memory_chain_detects_tamper(tmp_path, monkeypatch):
    chain = tmp_path / "chain.jsonl"
    monkeypatch.setattr(memory_chain, "CHAIN", chain)
    memory_chain.append("reply", "lead:a", {"x": 1})
    memory_chain.append("quote_sent", "lead:a", {"qt": "QT-1"})
    assert memory_chain.chain_verify(chain)["ok"] is True
    # دست‌کاریِ وسطِ زنجیره — مقدار detail ردیف ۱ عوض شود
    rows = chain.read_text().splitlines()
    r0 = json.loads(rows[0])
    r0["detail"] = {"x": 999}
    rows[0] = json.dumps(r0, ensure_ascii=False)
    chain.write_text("\n".join(rows) + "\n", encoding="utf-8")
    res = memory_chain.chain_verify(chain)
    assert res["ok"] is False and "row1" in (res["first_break"] or "")
