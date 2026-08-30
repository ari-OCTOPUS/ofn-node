#!/usr/bin/env python3
"""test_acct_review.py — موتورِ گفتگوی حسابداریِ تلگرام (2026-07-16).
اثبات: (الف) start مهم‌ترین (|مبلغ|) را اول می‌آورد؛ (ب) answer اعمال+پیش‌می‌رود+یاد می‌گیرد
(review→confirmed)؛ (پ) گاردِ سوالِ گذشته (stale idx)؛ (ت) parse_free قطعی → proposal، مبهم →
need-clarify؛ (ث) skip بدونِ تغییر پیش می‌رود؛ (ج) desc شماره‌حسابِ ۸+رقمی را scrub می‌کند؛
(چ) صفِ خالی → empty. ایزوله با فایلِ tmp (بدونِ opslib.ORG_ROOT، بدونِ شبکه). $0."""
import json
import sys
import tempfile
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE.parent / "legs"))
sys.path.insert(0, str(_HERE.parent / "budget"))
import acct_review as ar  # noqa: E402


def _store(tmp: Path, txns: list[dict]) -> Path:
    p = tmp / "txn-store.json"
    p.write_text(json.dumps({"_schema": "t", "currency": "AUD", "count": len(txns),
                             "generated": "2026-07-16", "txns": txns}, ensure_ascii=False), "utf-8")
    return p


def _txn(tid, amt, desc, owner="unknown", ptype="unknown", review="needs_review"):
    return {"id": tid, "date": "2026-01-01", "amount_cents": amt, "desc": desc,
            "owner": owner, "ptype": ptype, "review": review, "basis": "unmatched"}


def t_a_start_biggest_first():
    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d)
        sp = _store(tmp, [_txn("s", 5000, "small"), _txn("BIG", -900000, "PAYMENT FROM CARMY 00012345678"),
                          _txn("m", 20000, "mid")])
        sess = tmp / "sess.json"
        q = ar.start(store_path=sp, session_path=sess)
        assert q["kind"] == "question", q
        assert q["txn_id"] == "BIG", q                 # بزرگ‌ترین |مبلغ| اول
        assert q["amount"] == "-9000.00" and q["sign"] == "خروجی", q
        assert q["total"] == 3 and q["n"] == 1, q


def t_b_answer_applies_and_learns():
    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d)
        sp = _store(tmp, [_txn("x1", -50000, "BUNNINGS"), _txn("x2", 30000, "PAYPAL")])
        sess = tmp / "sess.json"
        q = ar.start(store_path=sp, session_path=sess)      # سوالِ ۱ = x1 (بزرگ‌تر)
        r = ar.answer("a", "e", tid_token=q["txn_id"], store_path=sp, session_path=sess)  # armin/expense
        assert r["kind"] == "applied" and r["applied"]["owner"] == "armin", r
        assert r["next"]["kind"] == "question" and r["next"]["txn_id"] == "x2", r
        # ذخیره شد و یاد گرفت (confirmed)
        doc = json.loads(sp.read_text("utf-8"))
        x1 = next(t for t in doc["txns"] if t["id"] == "x1")
        assert x1["owner"] == "armin" and x1["ptype"] == "expense", x1
        assert x1["review"] == "confirmed", x1              # مسیرِ یادگیری


def t_c_identity_guard_wrong_row():
    """فیکسِ HIGH: تپِ کارتِ *قدیمی* (توکنِ x1) وقتی سرِ صف حالا x2 است → stale، x2 دست‌نخورده."""
    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d)
        sp = _store(tmp, [_txn("x1", -50000, "A"), _txn("x2", -40000, "B")])
        sess = tmp / "sess.json"
        q1 = ar.start(store_path=sp, session_path=sess)
        tok_x1 = q1["txn_id"]                                # کارتِ x1
        ar.answer("a", "e", tid_token=tok_x1, store_path=sp, session_path=sess)  # x1 اعمال، سر → x2
        stale = ar.answer("b", "i", tid_token=tok_x1, store_path=sp, session_path=sess)  # کارتِ کهنهٔ x1
        assert stale["kind"] == "stale", stale
        doc = json.loads(sp.read_text("utf-8"))
        x2 = next(t for t in doc["txns"] if t["id"] == "x2")
        assert x2["review"] == "needs_review", x2           # پاسخِ کارتِ x1 به x2 اعمال نشد


def t_i_vanished_not_counted():
    """تراکنشِ غیب‌شده بینِ start و answer → kind=vanished، done شمرده نمی‌شود (نه green-lie)."""
    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d)
        sp = _store(tmp, [_txn("x1", -50000, "A"), _txn("x2", -40000, "B")])
        sess = tmp / "sess.json"
        ar.start(store_path=sp, session_path=sess)          # head x1
        doc = json.loads(sp.read_text("utf-8"))
        doc["txns"] = [t for t in doc["txns"] if t["id"] != "x1"]   # x1 حذف شد
        sp.write_text(json.dumps(doc, ensure_ascii=False), "utf-8")
        r = ar.answer("a", "e", tid_token="x1", store_path=sp, session_path=sess)
        assert r["kind"] == "vanished", r
        assert ar.progress(session_path=sess)["done"] == 0, "غیب‌شده نباید شمرده شود"
        assert r["next"]["txn_id"] == "x2", r


def t_j_iterative_skip_no_recursion():
    """صف با ۳۰۰۰ idِ غیب و storeِ خالی → done بدونِ RecursionError (فیکسِ recursion)."""
    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d)
        sp = _store(tmp, [])
        sess = tmp / "sess.json"
        sess.write_text(json.dumps({"active": True, "idx": 0,
                                    "order": [str(i) for i in range(3000)],
                                    "done": 0, "total_at_start": 3000}), "utf-8")
        q = ar.question(store_path=sp, session_path=sess)
        assert q["kind"] == "done", q


def t_d_parse_free_deterministic():
    p = ar.parse_free("این مالِ عباسه، خرجِ مصالح", use_local_llm=False)
    assert p["kind"] == "proposal", p
    assert p["owner"] == "abbas" and p["ptype"] == "expense", p
    assert p["owner_code"] == "b" and p["ptype_code"] == "e", p
    # مبهم → need-clarify
    amb = ar.parse_free("نمیدونم چیه", use_local_llm=False)
    assert amb["kind"] == "need-clarify", amb


def t_e_skip_advances_no_change():
    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d)
        sp = _store(tmp, [_txn("x1", -50000, "A"), _txn("x2", -40000, "B")])
        sess = tmp / "sess.json"
        ar.start(store_path=sp, session_path=sess)
        nxt = ar.skip(store_path=sp, session_path=sess)
        assert nxt["kind"] == "question" and nxt["txn_id"] == "x2", nxt
        doc = json.loads(sp.read_text("utf-8"))
        x1 = next(t for t in doc["txns"] if t["id"] == "x1")
        assert x1["review"] == "needs_review", x1          # skip چیزی عوض نکرد


def t_f_desc_scrubs_account_number():
    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d)
        sp = _store(tmp, [_txn("x1", -50000, "TRANSFER TO ACCT 12345678 VENDOR")])
        sess = tmp / "sess.json"
        q = ar.start(store_path=sp, session_path=sess)
        assert "12345678" not in q["desc"], q               # شماره‌حساب scrub شد
        assert "VENDOR" in q["desc"], q                     # vendor برای مالک ماند


def t_g_empty_queue():
    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d)
        sp = _store(tmp, [_txn("x1", -50000, "A", review="confirmed")])   # چیزی برای مرور نیست
        sess = tmp / "sess.json"
        q = ar.start(store_path=sp, session_path=sess)
        assert q["kind"] == "empty", q


def t_h_stop_ends_session():
    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d)
        sp = _store(tmp, [_txn("x1", -50000, "A")])
        sess = tmp / "sess.json"
        ar.start(store_path=sp, session_path=sess)
        r = ar.stop(session_path=sess)
        assert r["kind"] == "stopped", r
        assert ar.is_active(session_path=sess) is False


def t_k_memory_guess_ladder():
    """نردبانِ حدس: ردیفِ unknown → پیشنهادِ حافظهٔ قواعد در کارت (propose-only)."""
    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d)
        sp = _store(tmp, [_txn("m1", -45000, "BUNNINGS WAREHOUSE 616")])
        sess = tmp / "sess.json"
        orig = ar._memory_suggest
        ar._memory_suggest = lambda desc: {"owner": "armin", "ptype": "expense",
                                           "basis": "memory:5نمونه", "sample_count": 5}
        try:
            q = ar.start(store_path=sp, session_path=sess)
            assert q["guess"]["owner"] == "armin" and q["guess"]["ptype"] == "expense", q
            assert "memory" in q["guess"]["basis"], q
            # حافظه فقط حدس است — ردیف هنوز needs_review (تأیید با مالک)
            doc = json.loads(sp.read_text("utf-8"))
            assert doc["txns"][0]["review"] == "needs_review"
        finally:
            ar._memory_suggest = orig


def t_l_persisted_suggestion_used():
    """suggestionِ ماندگارِ LLM (pinشده از sync) در نردبانِ حدس دیده می‌شود."""
    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d)
        row = _txn("s1", -30000, "MYSTERY SHOP")
        row["suggestion"] = {"owner": "abbas", "ptype": "expense", "basis": "llm-suggest:local"}
        sp = _store(tmp, [row])
        sess = tmp / "sess.json"
        orig = ar._memory_suggest
        ar._memory_suggest = lambda desc: None          # حافظهٔ قواعد ساکت — نوبتِ LLMِ ماندگار
        try:
            q = ar.start(store_path=sp, session_path=sess)
            assert q["guess"]["owner"] == "abbas", q
            assert "llm" in q["guess"]["basis"], q
        finally:
            ar._memory_suggest = orig


if __name__ == "__main__":
    for f in (t_a_start_biggest_first, t_b_answer_applies_and_learns, t_c_identity_guard_wrong_row,
              t_d_parse_free_deterministic, t_e_skip_advances_no_change,
              t_f_desc_scrubs_account_number, t_g_empty_queue, t_h_stop_ends_session,
              t_i_vanished_not_counted, t_j_iterative_skip_no_recursion,
              t_k_memory_guess_ladder, t_l_persisted_suggestion_used):
        f()
        print("ok", f.__name__)
    print("PASS test_acct_review")
