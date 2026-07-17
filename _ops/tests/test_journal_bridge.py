#!/usr/bin/env python3
"""test_journal_bridge.py — پلِ برچسب→دفتر (فازِ ۱ + سخت‌سازیِ auditِ دوم، 2026-07-16).
اثبات: نگاشتِ ۴ ptype · گاردِ حسابِ entity (csv=skip) · transferِ business=skip · فقط
confirmed · هیچ tax_code · idempotency · **apply صف را باور نمی‌کند** (مسموم‌سازی → stale،
نه ثبت) · صفِ خراب fail-closed (ردها زنده نمی‌شوند) · refreshِ پیشنهادِ کهنه · scrubِ
شماره‌های گروهی. ایزوله با tmp. $0."""
import json
import sys
import tempfile
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE.parent / "legs"))
sys.path.insert(0, str(_HERE.parent / "budget"))
import journal_bridge as jb  # noqa: E402
import ledger_core as lc     # noqa: E402

PROFILE = {"entities": [{"entity_id": "armin-abn", "gst_registered": True}], "lock_date": None}


def _store(tmp: Path, txns):
    p = tmp / "txn-store.json"
    p.write_text(json.dumps({"txns": txns}, ensure_ascii=False), "utf-8")
    return p


def _t(tid, amt, ptype, owner="armin", review="confirmed", source="pocketsmith-api", **kw):
    return {"id": tid, "date": "2026-07-10", "amount_cents": amt,
            "desc": f"D-{tid} ACCT 12345678", "owner": owner, "ptype": ptype,
            "review": review, "source": source, **kw}


def t_a_mapping_four_types():
    m = jb.map_txn(_t("i1", 594000, "income", owner="abbas"))
    assert m["eligible"] and m["entry"]["lines"][0]["account"] == "1000", m
    assert m["entry"]["lines"][1]["account"] == "4000", m
    m = jb.map_txn(_t("e1", -11000, "expense", owner="rent"))
    assert m["entry"]["lines"][0]["account"] == "5200", m
    m = jb.map_txn(_t("w1", -25000, "wage"))
    assert m["entry"]["lines"][0]["account"] == "5300", m
    m_in = jb.map_txn(_t("tr1", 500000, "transfer"))
    m_out = jb.map_txn(_t("tr2", -500000, "transfer"))
    assert m_in["entry"]["lines"][1]["account"] == "2200", m_in
    assert m_out["entry"]["lines"][0]["account"] == "2200", m_out
    assert m_in.get("note"), "transfer باید هشدارِ 2200 داشته باشد"
    for m2 in (m_in, m_out):
        lines = m2["entry"]["lines"]
        assert sum(l["debit_cents"] for l in lines) == sum(l["credit_cents"] for l in lines)
        assert all("tax_code" not in l for l in lines), lines     # RD-002
    assert m_in["entry"]["idempotency_key"] == "txn-tr1"
    assert "12345678" not in m_in["entry"]["memo"]


def t_b_guards_and_honest_skips():
    assert not jb.map_txn(_t("x", 100, "income", review="needs_review"))["eligible"]
    assert not jb.map_txn(_t("x", -100, "income"))["eligible"]        # incomeِ خروجی
    assert not jb.map_txn(_t("x", 100, "wage"))["eligible"]           # wageِ ورودی
    assert not jb.map_txn(_t("x", 0, "income"))["eligible"]
    assert not jb.map_txn(_t("x", 100, "unknown"))["eligible"]
    # audit #7: ردیفِ حسابِ غیرِ entity (CSV طرف‌حساب) هرگز به دفترِ entity نمی‌رود
    m = jb.map_txn(_t("c1", -50000, "expense", owner="behzad", source="csv:behzad"))
    assert not m["eligible"] and "entity" in m["reason"], m
    # audit #8: transferِ business → نگاشتِ دستی
    assert not jb.map_txn(_t("tb", 1000, "transfer", owner="business"))["eligible"]
    # audit #16: هیچ hintِ سرمایه‌سازی — خریدِ 'tool' دارایی نمی‌شود
    m = jb.map_txn(_t("tl", -9000, "expense", desc="TRADE TOOLS SHOP"))
    assert m["entry"]["lines"][0]["account"] != "1500", m


def t_c_rebuild_idempotent_and_refresh():
    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d)
        sp = _store(tmp, [_t("i1", 594000, "income", owner="abbas"),
                          _t("w1", 25000, "wage"),                    # مبهم → skip
                          _t("n1", 100, "income", review="needs_review")])
        qp = tmp / "q.json"
        r1 = jb.rebuild(store_path=sp, queue_path=qp)
        assert r1["ok"] and r1["built"] == 1 and r1["pending"] == 1, r1
        r2 = jb.rebuild(store_path=sp, queue_path=qp)
        assert r2["built"] == 0 and r2["pending"] == 1, r2
        # audit #18/#22: تغییرِ مبلغِ همان txn → rebuild پیشنهاد را تازه می‌کند
        _store(tmp, [_t("i1", 600000, "income", owner="abbas")])
        r3 = jb.rebuild(store_path=sp, queue_path=qp)
        assert r3["refreshed"] == 1, r3
        p = jb.get("i1", queue_path=qp)
        assert p["entry"]["lines"][0]["debit_cents"] == 600000, p
        # txn غایب → stale (نه ثبت‌پذیرِ ابدی)
        _store(tmp, [])
        r4 = jb.rebuild(store_path=sp, queue_path=qp)
        assert r4["staled"] == 1 and r4["pending"] == 0, r4


def t_d_apply_rederives_and_double_tap_safe():
    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d)
        sp = _store(tmp, [_t("i1", 594000, "income", owner="abbas")])
        qp = tmp / "q.json"
        ld = tmp / "ledger"
        jb.rebuild(store_path=sp, queue_path=qp)
        r = jb.apply("i1", profile=PROFILE, queue_path=qp, ledger_dir=ld, store_path=sp)
        assert r["ok"] and r["journal_id"].startswith("j-"), r
        tb = lc.trial_balance(ld)
        assert tb["balanced"] and tb["total_debit_cents"] == 594000, tb
        r2 = jb.apply("i1", profile=PROFILE, queue_path=qp, ledger_dir=ld, store_path=sp)
        assert not r2["ok"], r2                                       # تپِ دوباره
        assert len(lc._read_ledger(ld)["journals"]) == 1


def t_e_poisoned_queue_never_posts():
    """audit #1 (HIGH): entryِ دستکاری‌شده در صف هرگز ثبت نمی‌شود — apply از store بازاشتقاق
    می‌کند؛ ناهم‌خوان → stale-refresh، و ثبتِ بعدی فقط entryِ درست."""
    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d)
        sp = _store(tmp, [_t("i1", 594000, "income", owner="abbas")])
        qp = tmp / "q.json"
        ld = tmp / "ledger"
        jb.rebuild(store_path=sp, queue_path=qp)
        q = json.loads(qp.read_text("utf-8"))
        q["proposals"]["i1"]["entry"]["lines"] = [          # مسموم: 9M$ به برداشتِ مالک
            {"account": "3000", "debit_cents": 900000000, "credit_cents": 0},
            {"account": "1000", "debit_cents": 0, "credit_cents": 900000000}]
        qp.write_text(json.dumps(q, ensure_ascii=False), "utf-8")
        r = jb.apply("i1", profile=PROFILE, queue_path=qp, ledger_dir=ld, store_path=sp)
        assert not r["ok"] and r.get("stale"), r            # ثبت نشد؛ کارت باید تازه شود
        assert lc._read_ledger(ld)["journals"] == []        # دفتر دست‌نخورده
        p = jb.get("i1", queue_path=qp)
        assert p["entry"]["lines"][0]["account"] == "1000", p   # صف به حقیقت برگشت
        r2 = jb.apply("i1", profile=PROFILE, queue_path=qp, ledger_dir=ld, store_path=sp)
        assert r2["ok"], r2                                  # حالا entryِ درست ثبت شد
        js = lc._read_ledger(ld)["journals"]
        assert js[0]["lines"][0]["account"] == "1000" and \
               js[0]["lines"][0]["debit_cents"] == 594000, js


def t_f_corrupt_queue_fail_closed():
    """audit #13/#20: صفِ خرابِ موجود بازنویسی نمی‌شود؛ ردها بی‌صدا زنده نمی‌شوند."""
    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d)
        sp = _store(tmp, [_t("e1", -11000, "expense")])
        qp = tmp / "q.json"
        qp.write_text("{corrupt!!", "utf-8")
        r = jb.rebuild(store_path=sp, queue_path=qp)
        assert not r["ok"], r
        assert "{corrupt!!" in qp.read_text("utf-8")         # فایلِ شاهد دست‌نخورده
        assert jb.pending(queue_path=qp) == []
        assert not jb.apply("e1", profile=PROFILE, queue_path=qp,
                            ledger_dir=tmp / "l", store_path=sp)["ok"]


def t_g_reject_final_and_scrub():
    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d)
        sp = _store(tmp, [_t("e1", -11000, "expense")])
        qp = tmp / "q.json"
        jb.rebuild(store_path=sp, queue_path=qp)
        assert jb.reject("e1", "غلط بود", queue_path=qp)["ok"]
        assert jb.pending(queue_path=qp) == []
        assert not jb.apply("e1", profile=PROFILE, queue_path=qp,
                            ledger_dir=tmp / "l", store_path=sp)["ok"]
    # audit #17: شماره‌های گروهی (BSB/کارت) هم scrub می‌شوند
    s = jb._scrub("BSB 062-000 acct 1234567 CARD 1234 5678 9012")
    assert "062" not in s and "1234" not in s, s


if __name__ == "__main__":
    for f in (t_a_mapping_four_types, t_b_guards_and_honest_skips,
              t_c_rebuild_idempotent_and_refresh, t_d_apply_rederives_and_double_tap_safe,
              t_e_poisoned_queue_never_posts, t_f_corrupt_queue_fail_closed,
              t_g_reject_final_and_scrub):
        f()
        print("ok", f.__name__)
    print("PASS test_journal_bridge")
