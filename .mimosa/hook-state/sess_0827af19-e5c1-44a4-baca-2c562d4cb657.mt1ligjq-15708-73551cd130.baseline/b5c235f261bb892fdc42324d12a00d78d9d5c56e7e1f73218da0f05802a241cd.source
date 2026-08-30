"""test_seam_r16_claim_20260816.py — SEAM-LOOP فاز ۳ (مصوب مالک): قاعدهٔ ۴ R16.

برداشتن از صف فقط با ارجاعِ ثبت‌شده (research_session/تست) — اتمی، بدون حذف،
با رکورد سیاست. چهار قفل:
  A) pending + ارجاع → claimed + رخداد سیاست
  B) claim دوباره → رد
  C) ارجاع خالی → رد (قلبِ قاعدهٔ ۴)
  D) dedup ردیف → غیرقابل claim
"""
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from memory import store  # noqa: E402


def _seed(tmp_path, monkeypatch):
    db = tmp_path / "c.db"
    monkeypatch.setattr(store, "DB_PATH", db)
    store._ensure_db()
    pid = store.save_hypothesis("d", "claimable hypothesis", "r")
    did = store.save_hypothesis("d", "claimable hypothesis", "r")  # تکرار → dedup
    return db, pid, did


def test_claim_ok_and_policy_event(tmp_path, monkeypatch):
    db, pid, _ = _seed(tmp_path, monkeypatch)
    r = store.claim_hypothesis(pid, "research_session=rs-42")
    assert r["ok"] and r["status"] == "claimed"
    conn = sqlite3.connect(str(db))
    st = conn.execute("SELECT status FROM hypotheses WHERE id=?", (pid,)).fetchone()[0]
    ev = conn.execute(
        "SELECT action, detail FROM hypothesis_policy_events"
        " WHERE row_id=? AND action='claim'", (pid,)).fetchone()
    conn.close()
    assert st == "claimed" and ev and "rs-42" in ev[1]


def test_double_claim_rejected(tmp_path, monkeypatch):
    _, pid, _ = _seed(tmp_path, monkeypatch)
    assert store.claim_hypothesis(pid, "rs-1")["ok"]
    r2 = store.claim_hypothesis(pid, "rs-2")
    assert not r2["ok"] and "status=claimed" in r2["reason"]


def test_empty_ref_rejected(tmp_path, monkeypatch):
    _, pid, _ = _seed(tmp_path, monkeypatch)
    for bad in ("", "   ", None):
        r = store.claim_hypothesis(pid, bad)
        assert not r["ok"] and "قاعدهٔ ۴" in r["reason"]


def test_dedup_row_not_claimable(tmp_path, monkeypatch):
    db, pid, did = _seed(tmp_path, monkeypatch)
    assert did != pid
    r = store.claim_hypothesis(did, "rs-3")
    assert not r["ok"]
