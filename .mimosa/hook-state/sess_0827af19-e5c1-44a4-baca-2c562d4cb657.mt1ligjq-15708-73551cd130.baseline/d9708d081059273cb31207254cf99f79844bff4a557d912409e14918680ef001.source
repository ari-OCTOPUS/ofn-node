#!/usr/bin/env python3
"""تستِ ارکستراتورِ حسابدار (2026-07-16): خط‌لوله + گزارشِ سنتی + حذفِ transfer.

اثبات:
  (الف) report: income/expense به تفکیکِ owner، **transfer در net نمی‌آید**، حقوق جدا، سنت.
  (ب) run روی fixture: counts + reconcile + صفِ بازبینی تولید می‌شود.
  (پ) apply_review تصحیحِ مالک را اعمال و گزارش را عوض می‌کند.
$0 آفلاین، stdlib، fixture در tmp.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import harness  # noqa: E402
ENV = harness.setup("accountant")

_LEGS = harness.SELF_OPS / "legs"
if str(_LEGS) not in sys.path:
    sys.path.insert(0, str(_LEGS))
import accountant  # noqa: E402
import money       # noqa: E402


def t_a_report_excludes_transfer():
    """transfer نه در income نه expense؛ در net نمی‌آید (pass-through)."""
    txns = [
        {"owner": "armin", "ptype": "income", "amount_cents": 100000},
        {"owner": "armin", "ptype": "expense", "amount_cents": -30000},
        {"owner": "armin", "ptype": "transfer", "amount_cents": 500000},   # باید حذف شود
        {"owner": "armin", "ptype": "wage", "amount_cents": 25000},
    ]
    rep = accountant.report(txns)
    a = rep["armin"]
    assert a["income_cents"] == 100000 and a["expense_cents"] == 30000
    assert a["net_cents"] == 70000, a          # transfer/wage در net نیست
    assert a["transfer_cents"] == 500000 and a["wage_cents"] == 25000
    assert a["display"]["net"] == "700.00"     # سنت→نمایش


def t_b_unknown_split_by_sign():
    """ptype=unknown: مثبت→income، منفی→expense (تا مالک برچسب بزند)."""
    txns = [{"owner": "unknown", "ptype": "unknown", "amount_cents": 5000},
            {"owner": "unknown", "ptype": "unknown", "amount_cents": -8000}]
    a = accountant.report(txns)["unknown"]
    assert a["income_cents"] == 5000 and a["expense_cents"] == 8000


def t_c_apply_review_changes_report():
    """تصحیحِ مالک (unknown→transfer) درآمد را از net حذف می‌کند."""
    txns = [{"id": "x1", "owner": "unknown", "ptype": "unknown", "amount_cents": 100000, "review": "needs_review"}]
    rep0 = accountant.report(txns)["unknown"]
    assert rep0["net_cents"] == 100000
    # اعمالِ تصحیح مستقیم (بدونِ فایل)
    import attributor
    fixed = attributor.apply_corrections(txns, {"x1": {"owner": "armin", "ptype": "transfer"}})
    rep1 = accountant.report(fixed)
    assert rep1["armin"]["net_cents"] == 0 and rep1["armin"]["transfer_cents"] == 100000, rep1


def t_d_network_summary_card_pii_safe():
    """network_summary_card: تجمیعِ درست (سطل‌های ≥۲) + هرگز نام/desc/شماره‌حساب/تراکنشِ خام."""
    txns = [
        {"id": "c1", "owner": "abbas", "ptype": "income", "amount_cents": 297000,
         "desc": "PAYMENT FROM CARMY PTY LTD 000031", "review": "needs_review"},
        {"id": "c2", "owner": "abbas", "ptype": "income", "amount_cents": 297000,
         "desc": "PAYMENT FROM CARBON HEROES", "review": "needs_review"},
        {"id": "c3", "owner": "sume", "ptype": "expense", "amount_cents": -1353900,
         "desc": "Payment to Sume Asadi #12345678", "review": "auto"},
        {"id": "c4", "owner": "sume", "ptype": "expense", "amount_cents": -1353899,
         "desc": "Payment to Sume Asadi #87654321", "review": "auto"},
        {"id": "c5", "owner": "armin", "ptype": "wage", "amount_cents": -12500,
         "desc": "حقوق ارمین", "review": "confirmed"},
        {"id": "c6", "owner": "armin", "ptype": "wage", "amount_cents": -12500,
         "desc": "حقوق ارمین", "review": "confirmed"},
    ]
    card = accountant.network_summary_card(txns=txns)
    assert card["live"] is True and card["unique"] == 6, card
    # تجمیعِ درست (سنتِ صحیح) — هر سطل ≥۲ تراکنش، پس ماسک نمی‌شود
    assert card["abbas_net"] == "5940.00", card
    assert card["assoc_total"] == "-27077.99", card
    assert card["client_revenue"] == "5940.00", card
    assert card["wage_total"] == "250.00" and card["wage_days"] == 1, card
    assert card["counts"] == {"confirmed": 2, "auto": 2, "needs_review": 2}, card
    # هیچ نشتِ PII در کلِ ساختار
    blob = repr(card)
    for leak in ("CARMY", "CARBON", "Sume", "Asadi", "12345678", "87654321",
                 "PAYMENT", "حقوق", "desc"):
        assert leak not in blob, f"leak: {leak!r} در network_summary_card"


def t_e_network_summary_absent_is_honest():
    """منبعِ غایب/خالی → live=False، صفر عددِ ساختگی."""
    absent = accountant.network_summary_card(path=Path("nonexistent-xyz.json"))
    assert absent["live"] is False, absent
    empty = accountant.network_summary_card(txns=[])
    assert empty["live"] is False, empty


def t_f_network_k_anonymity_masks_singletons():
    """کفِ k-ناشناسی: سطلِ تک-تراکنشی → '—' (مبلغِ خامِ تراکنشِ منفرد هرگز لو نرود)."""
    # دو تراکنش، هر کدام از یک طرفِ متفاوت → هر سطل n=۱
    card = accountant.network_summary_card(txns=[
        {"owner": "abbas", "ptype": "income", "amount_cents": 594000, "review": "needs_review"},
        {"owner": "sume", "ptype": "expense", "amount_cents": -45000, "review": "auto"},
    ])
    assert card["live"] is True and card["unique"] == 2, card
    assert card["abbas_net"] == "—", card              # آبباس فقط ۱ تراکنش → ماسک
    assert card["assoc_total"] == "—", card            # طرف‌حسابِ تک-تراکنشی → ماسک
    assert card["client_revenue"] == "—", card
    blob = repr(card)
    assert "5940.00" not in blob and "450.00" not in blob, blob   # هیچ مبلغِ خامِ تک-ردیف
    # کمتر از k کل → کلاً خاموش (نه نمایشِ تراکنشِ منفرد)
    one = accountant.network_summary_card(txns=[
        {"owner": "sume", "ptype": "expense", "amount_cents": -45000}])
    assert one["live"] is False, one


def t_g_network_fail_soft_bad_rows():
    """amount_cents خرابِ رشته‌ای crash نمی‌کند؛ ردیفِ non-dict در unique شمرده نمی‌شود."""
    card = accountant.network_summary_card(txns=[
        {"owner": "armin", "ptype": "expense", "amount_cents": "بد", "review": "auto"},
        {"owner": "armin", "ptype": "expense", "amount_cents": -5000, "review": "auto"},
        None,                                           # ردیفِ خراب — نه crash، نه در unique
    ])
    assert card["live"] is True and card["unique"] == 2, card   # None شمرده نشد


# ─── حفظِ تأییدهای مالک در sync (auditِ فازِ ۱ — #3/#4/#5/#15) ─────────────────────
def t_h_pin_restore_by_content_hash():
    """pin با content-hash: مهاجرتِ id تأیید را نگه می‌دارد؛ تغییرِ محتوا زیرِ همان id
    برچسبِ کهنه نمی‌گیرد (به /review برمی‌گردد — صادق)."""
    import tempfile as _tf
    with _tf.TemporaryDirectory() as d:
        sp = Path(d) / "txn-store.json"
        old = [{"id": "file-hash-1", "date": "2026-07-01", "amount_cents": -11000,
                "desc": "BUNNINGS WAREHOUSE", "owner": "armin", "ptype": "expense",
                "review": "confirmed"},
               {"id": "same-id", "date": "2026-07-02", "amount_cents": 50000,
                "desc": "CLIENT PAY", "owner": "abbas", "ptype": "income",
                "review": "confirmed"}]
        sp.write_text(json.dumps({"txns": old}, ensure_ascii=False), "utf-8")
        orig_sp = accountant._store_path
        accountant._store_path = lambda: sp
        try:
            keep, err = accountant._pin_confirmed()
            assert err is None and len(keep) == 2, (err, keep)
            fresh = [
                # همان محتوا، idِ نو (مهاجرتِ فایل→PS) → باید برگردد
                {"id": "ps-999", "date": "2026-07-01", "amount_cents": -11000,
                 "desc": "BUNNINGS WAREHOUSE", "owner": "unknown", "ptype": "unknown",
                 "review": "needs_review"},
                # همان id، محتوای عوض‌شده → نباید برچسبِ کهنه بگیرد
                {"id": "same-id", "date": "2026-07-02", "amount_cents": 51000,
                 "desc": "CLIENT PAY", "owner": "unknown", "ptype": "unknown",
                 "review": "needs_review"},
            ]
            n = accountant._restore_confirmed(fresh, keep)
            assert n == 1, (n, fresh)
            assert fresh[0]["review"] == "confirmed" and fresh[0]["owner"] == "armin", fresh[0]
            assert fresh[1]["review"] == "needs_review", fresh[1]      # صادقانه به مرور برگشت
        finally:
            accountant._store_path = orig_sp


def t_i_pin_fail_closed_on_corrupt_store():
    """storeِ موجود ولی ناخوانا → error (سکوت = پاک‌شدنِ همهٔ تأییدها — ممنوع)."""
    import tempfile as _tf
    with _tf.TemporaryDirectory() as d:
        sp = Path(d) / "txn-store.json"
        sp.write_text("{corrupt", "utf-8")
        orig_sp = accountant._store_path
        accountant._store_path = lambda: sp
        try:
            keep, err = accountant._pin_confirmed()
            assert err is not None and keep == {}, (err, keep)
            # storeِ غایب اما ok (شروعِ تمیز)
            sp.unlink()
            keep2, err2 = accountant._pin_confirmed()
            assert err2 is None and keep2 == {}, (err2, keep2)
        finally:
            accountant._store_path = orig_sp


def t_j_suggestion_pinned_across_sync():
    """ضدِ فراموشی (اسکنِ ارگانیسم): suggestionِ LLM روی ردیفِ تأییدنشده هم با content-hash
    از sync جان به‌در می‌برد — یک‌بار فکر، همیشه یادش."""
    import tempfile as _tf
    with _tf.TemporaryDirectory() as d:
        sp = Path(d) / "txn-store.json"
        old = [{"id": "a1", "date": "2026-07-01", "amount_cents": -11000,
                "desc": "BUNNINGS WAREHOUSE", "owner": "unknown", "ptype": "unknown",
                "review": "needs_review",
                "suggestion": {"owner": "armin", "ptype": "expense", "basis": "llm-suggest:local"}}]
        sp.write_text(json.dumps({"txns": old}, ensure_ascii=False), "utf-8")
        orig_sp = accountant._store_path
        accountant._store_path = lambda: sp
        try:
            keep, err = accountant._pin_confirmed()
            assert err is None and len(keep) == 1, (err, keep)
            fresh = [{"id": "ps-777", "date": "2026-07-01", "amount_cents": -11000,
                      "desc": "BUNNINGS WAREHOUSE", "owner": "unknown", "ptype": "unknown",
                      "review": "needs_review"}]
            n = accountant._restore_confirmed(fresh, keep)
            assert n == 1 and fresh[0]["suggestion"]["owner"] == "armin", fresh[0]
            assert fresh[0]["review"] == "needs_review"      # پیشنهاد ≠ تأیید (propose-only)
        finally:
            accountant._store_path = orig_sp


def t_k_content_hash_unified_with_txn_store_hash():
    """Regression guard (2026-07-18، فاز ۵.۲ — رفعِ باگِ دو-هش): _content_hash باید همون
    خروجیِ txn_store._hash را بدهد (full desc، case-sensitive، 16 hex). قبلاً _content_hash
    از desc[:20].lower() و 40 hex استفاده می‌کرد که باعث suppress می‌شد. اگه drift کنند،
    این تست fail می‌شود."""
    import txn_store
    cases = [
        {"date": "2026-07-10", "amount_cents": -11000,
         "desc": "BUNNINGS WAREHOUSE MELBOURNE", "account": "anz-main"},
        {"date": "2026-07-10", "amount_cents": -11000,
         "desc": "BUNNINGS WAREHOUSE SYDNEY", "account": "anz-main"},   # desc فرق بعد از کاراکتر 20
        {"date": "2026-01-15", "amount_cents": 25000,
         "desc": "SALARY", "account": "anz-main"},
        {"date": "2026-03-01", "amount_cents": -5000,
         "desc": "مصالح نقاشی", "account": "cba-biz"},                  # فارسی
    ]
    for t in cases:
        ch = accountant._content_hash(t)
        # txn_store._hash همون فرمول را استفاده می‌کند (full desc، case-sensitive)
        expected = txn_store._hash(t["date"], t["amount_cents"], t["desc"], t["account"])
        # NOTE: _content_hash ابتدا desc را به strip+truncate(:120) می‌کند تا با _mk هماهنگ شود؛
        # برای این cases کوتاه، هیچ تفاوتی نیست.
        assert ch == expected, (
            f"hash divergence! _content_hash={ch!r} vs txn_store._hash={expected!r} "
            f"for txn={t}")
    # حالتِ بحرانیِ باگِ قدیم: دو تراکنشِ مجزا با desc فرق‌دار بعد از کاراکتر ۲۰ باید
    # hash متفاوت داشته باشند (قبلاً یکی می‌شدند → suppress).
    a = accountant._content_hash(cases[0])
    b = accountant._content_hash(cases[1])
    assert a != b, (
        f"REGRESSION: دو تراکنشِ مجزا hash یکسان دارند (باگِ دو-هش برگشت): {a!r}")


if __name__ == "__main__":
    for f in (t_a_report_excludes_transfer, t_b_unknown_split_by_sign, t_c_apply_review_changes_report,
              t_d_network_summary_card_pii_safe, t_e_network_summary_absent_is_honest,
              t_f_network_k_anonymity_masks_singletons, t_g_network_fail_soft_bad_rows,
              t_h_pin_restore_by_content_hash, t_i_pin_fail_closed_on_corrupt_store,
              t_j_suggestion_pinned_across_sync, t_k_content_hash_unified_with_txn_store_hash):
        f()
        print("ok", f.__name__)
    print("PASS test_accountant")
