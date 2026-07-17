#!/usr/bin/env python3
"""تستِ دفترِ شخصی/مشترکِ v2 (2026-07-16): ۳ دفتر (آرمین/عباس/واحدِ ATO) + دامنهٔ کامل.

اثبات:
  (الف) ledger نبود → live=False + propose «قالب را پر کن».
  (ب) دفترِ شخصی: income/expense/asset/liability → cashflow + net_worth درست.
  (پ) حسابِ مشترک: split + paid_by → تسویهٔ «کی به کی» درست؛ سهم به دفترِ هرکس هم می‌رود.
  (ت) رول‌آپِ واحدِ ATO: income/expense تجمیعی + by_category + GST.
  (ث) مرزِ PII: خروجی نه descِ تراکنش، نه لیستِ خام — فقط ترازِ تجمیعی.
$0 آفلاین، stdlib.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import harness  # noqa: E402
ENV = harness.setup("personal-ledger")

_LEGS = harness.REAL_VAULT / "_ops" / "legs"
if str(_LEGS) not in sys.path:
    sys.path.insert(0, str(_LEGS))
import personal_ledger as pl  # noqa: E402


def _write(entries):
    import opslib
    p = opslib.ORG_ROOT / "03 - Projects" / "Accounting" / "personal" / "ledger.json"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps({"_schema": "personal-shared-ledger.v2", "currency": "AUD",
                             "default_split": {"armin": 50, "abbas": 50},
                             "entries": entries}, ensure_ascii=False), "utf-8")
    return p


def t_a_no_ledger():
    st = pl.personal_status(path=Path("F:/nope/ledger.json"))
    assert st["live"] is False and "پر کن" in st["note"], st


def t_b_personal_networth_cashflow():
    """آرمین: درآمد ۱۰۰، خرج ۳۰، دارایی ۵۰۰، بدهی ۲۰۰ → cashflow 70، net_worth 300."""
    p = _write([
        {"desc": "s", "amount": 100, "type": "income", "party": "armin", "category": "salary_wages"},
        {"desc": "g", "amount": 30, "type": "expense", "party": "armin", "category": "groceries"},
        {"desc": "sv", "amount": 500, "type": "asset", "party": "armin", "category": "savings"},
        {"desc": "cc", "amount": 200, "type": "liability", "party": "armin", "category": "credit_card"},
    ])
    a = pl.personal_status(p)["balance"]["per_party"]["armin"]
    assert a["cashflow"] == 70.0 and a["net_worth"] == 300.0, a


def t_c_joint_split_settlement():
    """اجاره‌ی مشترکِ ۱۰۰۰، ۶۰/۴۰، آرمین پرداخت → عباس ۴۰۰ به آرمین بدهکار؛ سهم به دفترِ هرکس."""
    p = _write([{"desc": "rent", "amount": 1000, "type": "expense", "party": "joint",
                 "paid_by": "armin", "split": {"armin": 60, "abbas": 40}, "category": "rent_mortgage"}])
    b = pl.personal_status(p)["balance"]
    assert b["joint_settlement"]["net_owed_to_armin"] == 400.0, b["joint_settlement"]
    assert b["per_party"]["armin"]["expense"] == 600.0 and b["per_party"]["abbas"]["expense"] == 400.0, b["per_party"]


def t_d_entity_ato_rollup():
    """رول‌آپِ واحد: income/expense تجمیعی + by_category + GST."""
    p = _write([
        {"desc": "sal", "amount": 5000, "type": "income", "party": "armin", "category": "salary_wages"},
        {"desc": "biz", "amount": 2000, "type": "income", "party": "abbas", "category": "business_income", "gst": 200},
        {"desc": "rent", "amount": 1500, "type": "expense", "party": "joint", "paid_by": "armin", "category": "rent_mortgage"},
    ])
    e = pl.personal_status(p)["balance"]["entity_ato"]
    assert e["income_total"] == 7000.0 and e["expense_total"] == 1500.0
    assert e["net_before_tax"] == 5500.0 and e["gst_total"] == 200.0
    assert e["by_category"]["income"]["salary_wages"] == 5000.0
    assert e["by_category"]["income"]["business_income"] == 2000.0


def t_e_no_desc_or_raw_entries_leaked():
    p = _write([{"desc": "رازِ-خصوصی", "amount": 999, "type": "expense", "party": "joint", "paid_by": "armin", "category": "misc"}])
    st = pl.personal_status(p)
    blob = json.dumps(st, ensure_ascii=False)
    assert "رازِ-خصوصی" not in blob, "descِ تراکنش نباید echo شود"
    assert "entries" not in st, "لیستِ خام نباید در خروجی باشد"


def t_f_categories_taxonomy_present():
    assert "salary_wages" in pl.CATEGORIES["income"]
    assert "rent_mortgage" in pl.CATEGORIES["expense"]
    assert "savings" in pl.CATEGORIES["asset"] and "credit_card" in pl.CATEGORIES["liability"]
    assert pl.PARTIES == ("armin", "abbas")


if __name__ == "__main__":
    for f in (t_a_no_ledger, t_b_personal_networth_cashflow, t_c_joint_split_settlement,
              t_d_entity_ato_rollup, t_e_no_desc_or_raw_entries_leaked, t_f_categories_taxonomy_present):
        f()
        print("ok", f.__name__)
    print("PASS test_personal_ledger")
