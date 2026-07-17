#!/usr/bin/env python3
"""تستِ دسته‌بندِ قطعیِ تراکنش (attributor) — CATEGORIZERِ حسابدارِ چندایجنتی (2026-07-16).

اثبات:
  (الف) WAGE: desc «armin» + مبلغ مضربِ $۲۵۰ → ptype=wage, owner=armin, review=needs_review،
        basis="wage-pattern:$250xN".
  (ب)  TRANSFER (pass-through): inbound سپس outboundِ تقریباً-برابر روی همان account ظرفِ ~۳ روز
        → هر دو ptype=transfer, review=needs_review (از درآمد/هزینه EXCLUDED، دوباره‌شمرده نشود).
        + نشانهٔ desc (send to abbas) هم → transfer.
  (پ)  قاعدهٔ فروشنده: bunnings → category=materials, ptype=expense, review=auto.
  (ت)  ناشناخته → review=needs_review (مالک برچسب می‌زند).
  (ث)  apply_corrections: تصحیحِ مالک → review=confirmed + basis=owner (مسیرِ یادگیری).
  (ج)  روش ۸ — دسته‌بند هرگز خودش confirm نمی‌کند: attribute هیچ txnی را confirmed نمی‌گذارد.
  (چ)  هیچ مبلغِ خامی فراتر از خودِ txn نشت نمی‌کند (counts/basis فقط الگو/شمارش).
$0 آفلاین، stdlib.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import harness  # noqa: E402
ENV = harness.setup("attributor")

_LEGS = harness.REAL_VAULT / "_ops" / "legs"
if str(_LEGS) not in sys.path:
    sys.path.insert(0, str(_LEGS))
import attributor as at  # noqa: E402


def _txn(id, cents, desc, account="armin-main", date="2026-07-01"):
    """txnِ خام مطابقِ شِمای txn_store (owner/ptype unknown، review pending)."""
    return {"id": id, "date": date, "amount_cents": cents, "desc": desc,
            "source": "test", "account": account, "owner": "unknown",
            "ptype": "unknown", "category": "", "review": "pending", "note": ""}


def _by_id(txns):
    return {t["id"]: t for t in txns}


def t_a_wage_detection():
    """armin + مبلغ مضربِ $۲۵۰ (۳×۲۵۰=۷۵۰) → wage/armin/needs_review + citation."""
    a = at.attribute([_txn("w", 75000, "Armin wage july")])
    r = _by_id(a)["w"]
    assert r["ptype"] == "wage", r
    assert r["owner"] == "armin", r
    assert r["review"] == "needs_review", r          # حقوق حساس است — مالک تأیید
    assert r["basis"] == "wage-pattern:$250x3", r


def t_a2_wage_non_multiple_not_wage():
    """مبلغِ غیرمضربِ $۲۵۰ (حتی با نامِ armin) → wage نمی‌شود (قاعدهٔ محافظه‌کار)."""
    a = at.attribute([_txn("w2", 73000, "Armin something")])
    assert _by_id(a)["w2"]["ptype"] != "wage"


def t_b_transfer_pair_passthrough():
    """inbound سپس outboundِ برابر روی همان account ظرفِ ۳ روز → هر دو transfer/needs_review."""
    a = at.attribute([
        _txn("in", 120000, "job deposit", account="armin-main", date="2026-07-02"),
        _txn("out", -120000, "payment", account="armin-main", date="2026-07-03"),
    ])
    r = _by_id(a)
    assert r["in"]["ptype"] == "transfer" and r["out"]["ptype"] == "transfer", r
    assert r["in"]["review"] == "needs_review", r
    assert "passthrough-candidate" in r["in"]["basis"], r


def t_b2_transfer_desc_hint():
    """نشانهٔ desc «send to abbas» → transfer حتی بدونِ جفتِ ساختاری."""
    a = at.attribute([_txn("x", -50000, "send to abbas")])
    assert _by_id(a)["x"]["ptype"] == "transfer"


def t_b3_diff_account_not_paired():
    """inbound و outbound روی accountِ متفاوت → جفتِ pass-through نمی‌شود (محافظه‌کار)."""
    a = at.attribute([
        _txn("in2", 90000, "deposit", account="acct-A", date="2026-07-02"),
        _txn("out2", -90000, "spend groceries", account="acct-B", date="2026-07-03"),
    ])
    r = _by_id(a)
    assert r["in2"]["ptype"] != "transfer" and r["out2"]["ptype"] != "transfer", r


def t_c_vendor_rule():
    """bunnings → materials/expense/auto؛ petrol → transport/expense."""
    a = at.attribute([_txn("v", -8990, "BUNNINGS Warehouse 123"),
                      _txn("f", -6000, "Shell petrol")])
    r = _by_id(a)
    assert r["v"]["category"] == "materials" and r["v"]["ptype"] == "expense", r
    assert r["v"]["review"] == "auto", r
    assert r["f"]["category"] == "transport", r


def t_d_unknown_needs_review():
    """ناشناخته → needs_review، ptype همچنان unknown (مالک برچسب می‌زند)."""
    a = at.attribute([_txn("u", -4200, "random cafe zzz")])
    r = _by_id(a)["u"]
    assert r["review"] == "needs_review" and r["ptype"] == "unknown", r


def t_e_apply_corrections_confirms():
    """تصحیحِ مالک → review=confirmed + basis=owner + فیلدهای برچسب‌خورده."""
    a = at.attribute([_txn("u", -4200, "random cafe zzz")])
    fixed = at.apply_corrections(a, {"u": {"owner": "armin", "ptype": "expense",
                                           "category": "dining"}})
    r = _by_id(fixed)["u"]
    assert r["review"] == "confirmed" and r["basis"] == "owner", r
    assert r["ptype"] == "expense" and r["owner"] == "armin" and r["category"] == "dining", r


def t_f_agent_never_confirms():
    """روش ۸ — گیتِ سختِ انسانی: attribute هیچ txnی را confirmed نمی‌گذارد (فقط auto/needs_review)."""
    a = at.attribute([_txn("w", 75000, "Armin wage"), _txn("v", -8990, "bunnings"),
                      _txn("u", -4200, "mystery")])
    assert all(t["review"] in ("auto", "needs_review") for t in a)
    assert not any(t["review"] == "confirmed" for t in a)


def t_g_review_queue_material_first():
    """صف نامطمئن‌ها، بزرگ‌ترین |amount| اول."""
    a = at.attribute([_txn("small", -500, "mystery small"),
                      _txn("big", -900000, "mystery big"),
                      _txn("mid", -30000, "mystery mid")])
    q = at.review_queue(a)
    ids = [t["id"] for t in q]
    assert ids == ["big", "mid", "small"], ids


def t_h_counts_shape():
    """counts = {auto, needs_review, by_ptype ...}؛ transfer دوتا شمرده شود."""
    a = at.attribute([
        _txn("in", 120000, "deposit", date="2026-07-02"),
        _txn("out", -120000, "pay", date="2026-07-03"),
        _txn("v", -8990, "bunnings"),
        _txn("u", -4200, "mystery"),
    ])
    c = at.counts(a)
    assert c["auto"] == 1 and c["needs_review"] == 3, c
    assert c["by_ptype"]["transfer"] == 2, c


def t_i_no_raw_amount_leak():
    """هیچ مبلغِ خامی فراتر از خودِ txn نشت نمی‌کند: نه در basis، نه در counts (فقط الگو/شمارش)."""
    secret = 987654                                   # مبلغِ خامِ متمایز
    a = at.attribute([_txn("u", -secret, "mystery vendor")])
    r = _by_id(a)["u"]
    assert str(secret) not in r["basis"], "basis نباید مبلغِ خام را echo کند"
    cblob = json.dumps(at.counts(a), ensure_ascii=False)
    assert str(secret) not in cblob and "9876.54" not in cblob, "counts نباید مبلغ echo کند"


if __name__ == "__main__":
    for f in (t_a_wage_detection, t_a2_wage_non_multiple_not_wage,
              t_b_transfer_pair_passthrough, t_b2_transfer_desc_hint,
              t_b3_diff_account_not_paired, t_c_vendor_rule, t_d_unknown_needs_review,
              t_e_apply_corrections_confirms, t_f_agent_never_confirms,
              t_g_review_queue_material_first, t_h_counts_shape, t_i_no_raw_amount_leak):
        f()
        print("ok", f.__name__)
    print("PASS test_attributor")
