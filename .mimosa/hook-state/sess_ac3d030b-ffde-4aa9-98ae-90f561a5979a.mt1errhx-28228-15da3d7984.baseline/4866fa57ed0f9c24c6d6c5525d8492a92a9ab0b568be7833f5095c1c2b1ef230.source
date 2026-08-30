#!/usr/bin/env python3
"""test_acct_memory.py — حافظهٔ ضدِ فراموشیِ حسابدار (2026-07-16).
اثبات: merchant_key نرمالِ قطعی · rebuild قاعدهٔ اکثریت با کفِ نمونه (تک‌نمونه هرگز فعال
نمی‌شود) · نرخِ استثنا قاعده را غیرفعال می‌کند · suggest فقط قاعدهٔ فعال · بازتولیدپذیری
(حذفِ فایلِ حافظه هیچ دانشی را نمی‌کشد) · evaluate پوشش/دقت/drift. ایزوله با tmp. $0."""
import json
import sys
import tempfile
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE.parent / "legs"))
sys.path.insert(0, str(_HERE.parent / "budget"))
import acct_memory as am  # noqa: E402


def _store(tmp: Path, txns):
    p = tmp / "txn-store.json"
    p.write_text(json.dumps({"txns": txns}, ensure_ascii=False), "utf-8")
    return p


def _t(desc, owner="armin", ptype="expense", review="confirmed"):
    return {"id": desc[:8], "desc": desc, "owner": owner, "ptype": ptype,
            "review": review, "amount_cents": -1000, "date": "2026-07-01"}


def t_a_merchant_key_normal():
    assert am.merchant_key("BUNNINGS 616000 WAREHOUSE #123") == "bunnings warehouse"
    assert am.merchant_key("PAYMENT FROM CARMY PTY LTD 00031") == "carmy"
    assert am.merchant_key("VISA DEBIT 1234") == ""                # فقط نویز → بی‌کلید
    assert am.merchant_key(None) == ""


def t_b_rules_majority_and_min_samples():
    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d)
        sp = _store(tmp, [_t("BUNNINGS W 1"), _t("BUNNINGS W 2"), _t("BUNNINGS W 3"),
                          _t("ONE OFF SHOP X")])                    # تک‌نمونه
        mp = tmp / "mem.json"
        r = am.rebuild(store_path=sp, memory_path=mp)
        assert r["ok"] and r["active"] == 1, r                      # فقط bunnings فعال
        s = am.suggest("BUNNINGS W 99 NEW", memory_path=mp)
        assert s and s["owner"] == "armin" and s["ptype"] == "expense", s
        assert "نمونه" in s["basis"], s
        assert am.suggest("ONE OFF SHOP X", memory_path=mp) is None  # تک‌نمونه هرگز


def t_c_exception_rate_deactivates():
    """اگر مالک خلافِ الگو تأیید کند (۲/۵=۴۰٪)، قاعده غیرفعال — ضدِ تکثیرِ اشتباه."""
    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d)
        rows = [_t(f"MIXED VENDOR {i}") for i in range(3)] + \
               [_t(f"MIXED VENDOR {i}", ptype="income") for i in (3, 4)]
        sp = _store(tmp, rows)
        mp = tmp / "mem.json"
        r = am.rebuild(store_path=sp, memory_path=mp)
        assert r["rules"] == 1 and r["active"] == 0, r
        assert am.suggest("MIXED VENDOR 9", memory_path=mp) is None


def t_d_reproducible_after_delete():
    """ضدِ فراموشیِ ساختاری: فایلِ حافظه پاک شود → rebuild همان دانش را برمی‌گرداند."""
    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d)
        sp = _store(tmp, [_t("BUNNINGS W 1"), _t("BUNNINGS W 2"), _t("BUNNINGS W 3")])
        mp = tmp / "mem.json"
        am.rebuild(store_path=sp, memory_path=mp)
        before = am.suggest("BUNNINGS W", memory_path=mp)
        mp.unlink()                                                # crash/گم‌شدنِ کش
        assert am.suggest("BUNNINGS W", memory_path=mp) is None    # کش نیست
        am.rebuild(store_path=sp, memory_path=mp)                  # از منبعِ ماندگار
        after = am.suggest("BUNNINGS W", memory_path=mp)
        assert after == before, (before, after)


def t_e_evaluate_and_drift():
    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d)
        sp = _store(tmp, [_t("BUNNINGS W 1"), _t("BUNNINGS W 2"), _t("BUNNINGS W 3")])
        mp = tmp / "mem.json"
        am.rebuild(store_path=sp, memory_path=mp)
        ev = am.evaluate(store_path=sp, memory_path=mp)
        assert ev["ok"] and ev["n"] == 3 and ev["coverage_pct"] == 100.0, ev
        assert ev["accuracy_pct"] == 100.0 and ev["drift_alarm"] is False, ev
        # مرزِ درست: only confirmedها در طلایی‌اند
        golden = am.export_golden(store_path=sp)
        assert all(g["owner"] == "armin" for g in golden)


if __name__ == "__main__":
    for f in (t_a_merchant_key_normal, t_b_rules_majority_and_min_samples,
              t_c_exception_rate_deactivates, t_d_reproducible_after_delete,
              t_e_evaluate_and_drift):
        f()
        print("ok", f.__name__)
    print("PASS test_acct_memory")
