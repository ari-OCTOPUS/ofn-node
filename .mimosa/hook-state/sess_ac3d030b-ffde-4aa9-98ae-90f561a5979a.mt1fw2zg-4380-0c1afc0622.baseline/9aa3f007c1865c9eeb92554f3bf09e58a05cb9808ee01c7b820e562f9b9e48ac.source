#!/usr/bin/env python3
"""test_recon.py — موتورِ reconciliation واقعی (فازِ صفر، 2026-07-16).
تستِ پرچم‌دار: سناریوی خودِ نقد — دو خطای متضاد با خالصِ برابر باید **رد** شود
(net-comparison هرگز معیارِ سبز نیست). $0، بدونِ فایل."""
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE.parent / "legs"))
import recon  # noqa: E402


def _t(i, amt):
    return {"id": str(i), "amount_cents": amt}


def t_a_balance_identity():
    b = recon.balance_check(100000, [-11000, 50000], 139000)
    assert b["ok"] and b["diff_cents"] == 0, b
    b2 = recon.balance_check(100000, [-11000, 50000], 140000)   # یک دلار گم
    assert not b2["ok"] and b2["diff_cents"] == 1000, b2


def t_b_FLAGSHIP_offsetting_errors_equal_net_must_fail():
    """حکمِ نقد: «برابریِ خالص صحت نیست.» دفترِ ما یک درآمدِ +500 و یک خرجِ −500 را
    جا انداخته → خالص‌ها برابرند ولی reconciliation باید ۲ قلمِ حل‌نشده گزارش کند."""
    theirs = [_t("i1", 50000), _t("e1", -50000), _t("x1", 20000), _t("x2", -7000)]
    ours = [_t("x1", 20000), _t("x2", -7000)]                    # i1 و e1 گم شده‌اند
    r = recon.reconcile(ours, theirs)
    assert r["net_ours_cents"] == r["net_theirs_cents"] == 13000  # خالص‌ها برابر!
    assert not r["ok"], r                                         # ولی سبز نیست
    assert r["completeness"]["unresolved"] == 2, r["completeness"]
    assert sorted(r["completeness"]["missing_in_ours"]) == ["e1", "i1"]
    assert r["net_equal_but_not_proof"] is True, r                # صریحاً «برابر ولی اثبات نه»


def t_c_mismatch_and_dup_detected():
    theirs = [_t("a", 10000), _t("b", -5000)]
    ours = [_t("a", 10001), _t("b", -5000), _t("b", -5000), _t("c", 999)]
    c = recon.completeness(ours, theirs)
    assert "a" in c["amount_mismatch"], c                        # اختلافِ یک سنت هم گزارش
    assert "b" in c["dup_ids_ours"], c                           # id تکراری در دفترِ ما
    assert "c" in c["missing_in_theirs"], c                      # قلمِ اضافیِ ما
    assert not c["ok"], c


def t_d_perfect_match_green():
    rows = [_t("a", 10000), _t("b", -5000)]
    r = recon.reconcile(list(rows), list(rows), opening_cents=0, closing_cents=5000)
    assert r["ok"] and r["completeness"]["matched"] == 2, r
    assert r["balance"]["ok"], r


def t_e_bad_amounts_gate_red():
    """audit #9/#12/#25: مبلغِ غایب/رشته/float → bad شمرده و قرمز؛ ۰==۰ روی دو خرابی match نمی‌شود."""
    ours = [{"id": "a", "amount_cents": "خراب"}, {"id": "b"}]        # ناسالم + غایب
    theirs = [{"id": "a", "amount_cents": "خراب"}, {"id": "b", "amount_cents": 5000}]
    c = recon.completeness(ours, theirs)
    assert not c["ok"], c
    assert c["bad_amounts_ours"] == 2 and c["bad_amounts_theirs"] == 1, c
    assert "a" in c["amount_mismatch"] and "b" in c["amount_mismatch"], c   # None هرگز match نیست
    b = recon.balance_check("خراب", [1000], 1000)                    # opening ناسالم → قرمز
    assert not b["ok"] and b["bad_bounds"], b


def t_f_id_zero_valid():
    """audit #8: id==0 معتبر است (چکِ حضور، نه truthiness)."""
    rows = [{"id": 0, "amount_cents": 100}]
    c = recon.completeness(list(rows), list(rows))
    assert c["ok"] and c["matched"] == 1 and c["bad_rows_ours"] == 0, c


def t_g_vacuous_empty_not_green():
    """audit #26: دو مجموعهٔ خالی = vacuous، سبز نیست (ضدِ ترکیب با خواننده‌های fail-soft)."""
    r = recon.reconcile([], [])
    assert not r["ok"] and r["vacuous"] is True, r


def t_h_truncation_flagged():
    """audit #43: لیستِ سقف‌خورده پرچمِ صریح دارد؛ شمارش کامل می‌ماند."""
    theirs = [_t(i, 100) for i in range(250)]
    r = recon.completeness([], theirs)
    assert r["missing_in_ours_truncated"] is True, r
    assert len(r["missing_in_ours"]) == 200 and r["unresolved"] == 250, r


def t_i_long_id_capped():
    """audit #42: idِ متنِ آزاد (ستونِ اشتباه) در گزارش [:40] می‌شود — نشتِ PII محدود."""
    long_id = "PAYMENT TO SOMEBODY VERY PRIVATE 1234567890 EXTRA"
    c = recon.completeness([], [{"id": long_id, "amount_cents": 1}])
    assert all(len(k) <= 40 for k in c["missing_in_ours"]), c


if __name__ == "__main__":
    for f in (t_a_balance_identity, t_b_FLAGSHIP_offsetting_errors_equal_net_must_fail,
              t_c_mismatch_and_dup_detected, t_d_perfect_match_green,
              t_e_bad_amounts_gate_red, t_f_id_zero_valid, t_g_vacuous_empty_not_green,
              t_h_truncation_flagged, t_i_long_id_capped):
        f()
        print("ok", f.__name__)
    print("PASS test_recon")
