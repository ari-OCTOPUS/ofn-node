#!/usr/bin/env python3
"""test_ledger_core.py — هستهٔ دفترِ دوطرفه (فازِ صفر، 2026-07-16).
اثبات: توازنِ اجباری · ردِ float · ردِ حساب/entity ناشناخته · قفلِ دوره · گاردِ GSTِ
fail-closed · idempotency · reversal بدونِ دست‌زدن به اصل · trial balance متوازن.
ایزوله با tmp dir (بدونِ ORG_ROOT). $0."""
import json
import sys
import tempfile
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE.parent / "legs"))
sys.path.insert(0, str(_HERE.parent / "budget"))
import ledger_core as lc  # noqa: E402

PROFILE = {"entities": [{"entity_id": "armin-abn", "gst_registered": "unknown"}],
           "lock_date": None}
PROFILE_GST = {"entities": [{"entity_id": "armin-abn", "gst_registered": True}],
               "lock_date": None}


def _entry(lines, date="2026-07-10", ent="armin-abn", **kw):
    return {"entity_id": ent, "date": date, "memo": "test", "lines": lines, **kw}


def _bal_lines(amt=11000):
    return [{"account": "5000", "debit_cents": amt, "credit_cents": 0},
            {"account": "1000", "debit_cents": 0, "credit_cents": amt}]


def t_a_balanced_posts_unbalanced_rejected():
    with tempfile.TemporaryDirectory() as d:
        ld = Path(d)
        r = lc.post_journal(_entry(_bal_lines()), PROFILE, ld)
        assert r["ok"] and r["journal_id"].startswith("j-"), r
        bad = _entry([{"account": "5000", "debit_cents": 10000, "credit_cents": 0},
                      {"account": "1000", "debit_cents": 0, "credit_cents": 9999}])
        r2 = lc.post_journal(bad, PROFILE, ld)
        assert not r2["ok"] and any("نامتوازن" in e for e in r2["errors"]), r2
        assert len(lc._read_ledger(ld)["journals"]) == 1     # ثبتِ بد هیچ اثری نگذاشت


def t_b_float_money_rejected():
    """ناوردای پول: float مردود است — تبدیل نمی‌شود، رد می‌شود."""
    bad = _entry([{"account": "5000", "debit_cents": 100.5, "credit_cents": 0},
                  {"account": "1000", "debit_cents": 0, "credit_cents": 100.5}])
    v = lc.validate_journal(bad, PROFILE)
    assert not v["ok"] and any("int" in e for e in v["errors"]), v


def t_c_unknown_account_entity_profile():
    v = lc.validate_journal(_entry([{"account": "9999", "debit_cents": 100, "credit_cents": 0},
                                    {"account": "1000", "debit_cents": 0, "credit_cents": 100}]),
                            PROFILE)
    assert not v["ok"] and any("ناشناخته" in e for e in v["errors"]), v
    v2 = lc.validate_journal(_entry(_bal_lines(), ent="ghost-entity"), PROFILE)
    assert not v2["ok"], v2
    v3 = lc.validate_journal(_entry(_bal_lines()), None)     # profile غایب → رد
    assert not v3["ok"] and any("policy-profile" in e for e in v3["errors"]), v3


def t_d_locked_period_rejected():
    locked = {"entities": PROFILE["entities"], "lock_date": "2026-06-30"}
    v = lc.validate_journal(_entry(_bal_lines(), date="2026-06-15"), locked)
    assert not v["ok"] and any("قفل" in e for e in v["errors"]), v
    v2 = lc.validate_journal(_entry(_bal_lines(), date="2026-07-10"), locked)
    assert v2["ok"], v2                                       # دورهٔ باز ok


def t_e_gst_fail_closed():
    """gst_registered=unknown → هر tax_code غیرِ N-T رد (needs-agent)؛ true → مجاز."""
    gst_lines = [{"account": "5000", "debit_cents": 10000, "credit_cents": 0, "tax_code": "GST"},
                 {"account": "1000", "debit_cents": 0, "credit_cents": 10000}]
    v = lc.validate_journal(_entry(gst_lines), PROFILE)
    assert not v["ok"] and any("needs-agent" in e for e in v["errors"]), v
    v2 = lc.validate_journal(_entry(gst_lines), PROFILE_GST)
    assert v2["ok"], v2


def t_f_idempotent_post():
    with tempfile.TemporaryDirectory() as d:
        ld = Path(d)
        e = _entry(_bal_lines(), idempotency_key="tg-update-991")
        r1 = lc.post_journal(e, PROFILE, ld)
        r2 = lc.post_journal(e, PROFILE, ld)                  # retry شبکه/دوباره‌تپ
        assert r1["ok"] and r2["ok"], (r1, r2)
        assert r2["duplicate"] is True and r1["journal_id"] == r2["journal_id"]
        assert len(lc._read_ledger(ld)["journals"]) == 1      # فقط یک ثبت


def t_g_reversal_not_overwrite():
    with tempfile.TemporaryDirectory() as d:
        ld = Path(d)
        r = lc.post_journal(_entry(_bal_lines(11000)), PROFILE, ld)
        jid = r["journal_id"]
        before = json.dumps(lc._read_ledger(ld)["journals"][0], sort_keys=True)
        rev = lc.reverse_journal(jid, "اشتباهِ ثبت", PROFILE, ld)
        assert rev["ok"], rev
        js = lc._read_ledger(ld)["journals"]
        assert len(js) == 2                                   # اصل + reversal (نه overwrite)
        assert json.dumps(js[0], sort_keys=True) == before    # اصل بایت‌به‌بایت دست‌نخورده
        assert js[1]["reverses"] == jid
        # دوباره reverse → رد
        rev2 = lc.reverse_journal(jid, "دوباره", PROFILE, ld)
        assert not rev2["ok"], rev2
        # بعدِ reversal ترازِ هر حساب صفر
        tb = lc.trial_balance(ld)
        assert tb["balanced"] and all(s["net_cents"] == 0 for s in tb["accounts"].values()), tb


def t_h_trial_balance_always_balanced():
    with tempfile.TemporaryDirectory() as d:
        ld = Path(d)
        lc.post_journal(_entry(_bal_lines(11000)), PROFILE, ld)
        lc.post_journal(_entry([{"account": "1000", "debit_cents": 594000, "credit_cents": 0},
                                {"account": "4000", "debit_cents": 0, "credit_cents": 594000}],
                               date="2026-07-11"), PROFILE, ld)
        tb = lc.trial_balance(ld)
        assert tb["balanced"], tb
        assert tb["total_debit_cents"] == tb["total_credit_cents"] == 605000, tb
        assert tb["accounts"]["4000"]["net_cents"] == -594000, tb   # درآمد = بستانکار


# ─── سخت‌سازی‌های auditِ خصمانهٔ 2026-07-16 (۴۳ یافته → گاردهای جدید) ─────────────
def t_i_ikey_conflict_different_payload():
    """audit #11: همان کلید + payloadِ متفاوت → conflict، نه بلعیدنِ بی‌صدا."""
    with tempfile.TemporaryDirectory() as d:
        ld = Path(d)
        lc.post_journal(_entry(_bal_lines(11000), idempotency_key="k1"), PROFILE, ld)
        r = lc.post_journal(_entry(_bal_lines(22000), idempotency_key="k1"), PROFILE, ld)
        assert not r["ok"] and r.get("conflict") is True, r
        assert len(lc._read_ledger(ld)["journals"]) == 1     # هیچ‌چیز بی‌صدا ننشست


def t_j_rev_namespace_reserved():
    """audit #1: نامفضای rev- بدونِ reverses هم‌خوان → رد در validate (poisoning غیرممکن)."""
    v = lc.validate_journal(_entry(_bal_lines(), idempotency_key="rev-jabc"), PROFILE)
    assert not v["ok"] and any("rev-" in e for e in v["errors"]), v


def t_k_identical_no_ikey_both_post():
    """audit #4: دو ثبتِ مشروعِ *یکسان* بدونِ ikey (دو دستمزدِ نقدیِ هم‌روز) هر دو می‌نشینند."""
    with tempfile.TemporaryDirectory() as d:
        ld = Path(d)
        e = _entry(_bal_lines(25000))
        r1 = lc.post_journal(dict(e), PROFILE, ld)
        r2 = lc.post_journal(dict(e), PROFILE, ld)
        assert r1["ok"] and r2["ok"] and not r2.get("duplicate"), (r1, r2)
        assert r1["journal_id"] != r2["journal_id"]
        tb = lc.trial_balance(ld)
        assert tb["total_debit_cents"] == 50000, tb          # هر دو شمرده شدند


def t_l_unknown_keys_rejected():
    """audit #24: قاچاقِ فیلد (gst_cents/متادیتای دلخواه) در entry یا سطر → رد."""
    v = lc.validate_journal({**_entry(_bal_lines()), "smuggled": 1}, PROFILE)
    assert not v["ok"] and any("ناشناخته در entry" in e for e in v["errors"]), v
    bad_line = [{"account": "5000", "debit_cents": 100, "credit_cents": 0, "gst_cents": 10},
                {"account": "1000", "debit_cents": 0, "credit_cents": 100}]
    v2 = lc.validate_journal(_entry(bad_line), PROFILE)
    assert not v2["ok"] and any("قاچاق" in e for e in v2["errors"]), v2


def t_m_gst_control_account_gated():
    """audit #7: ثبتِ مستقیم به حسابِ کنترلِ GST (2100) بدونِ ثبتِ GST → رد، حتی بی‌tax_code."""
    lines = [{"account": "2100", "debit_cents": 1000, "credit_cents": 0},
             {"account": "1000", "debit_cents": 0, "credit_cents": 1000}]
    v = lc.validate_journal(_entry(lines), PROFILE)
    assert not v["ok"] and any("کنترلِ GST" in e for e in v["errors"]), v
    assert lc.validate_journal(_entry(lines), PROFILE_GST)["ok"]     # با ثبت، مجاز


def t_n_tax_whitelist_when_open():
    """audit #38: حتی با گیتِ باز، tax_code فقط از whitelist."""
    lines = [{"account": "5000", "debit_cents": 100, "credit_cents": 0, "tax_code": "GARBAGE"},
             {"account": "1000", "debit_cents": 0, "credit_cents": 100}]
    v = lc.validate_journal(_entry(lines), PROFILE_GST)
    assert not v["ok"] and any("نامعتبر" in e for e in v["errors"]), v


def t_o_truthy_gst_still_closed():
    """audit #39: 'true'/1/'yes' گیت را باز نمی‌کنند — فقط `is True`."""
    for val in ("true", 1, "yes", 1.0):
        prof = {"entities": [{"entity_id": "armin-abn", "gst_registered": val}]}
        lines = [{"account": "5000", "debit_cents": 100, "credit_cents": 0, "tax_code": "GST"},
                 {"account": "1000", "debit_cents": 0, "credit_cents": 100}]
        v = lc.validate_journal(_entry(lines), prof)
        assert not v["ok"], f"gst gate opened by {val!r}"


def t_p_torn_tail_blocks_post():
    """audit #3: انتهای ناقص (torn) → ثبتِ بعدی fail-closed تا بازبینیِ دستی."""
    with tempfile.TemporaryDirectory() as d:
        ld = Path(d)
        lc.post_journal(_entry(_bal_lines()), PROFILE, ld)
        p = ld / "journals.jsonl"
        p.write_bytes(p.read_bytes() + b'{"journal_id": "torn')   # tear بدونِ newline
        r = lc.post_journal(_entry(_bal_lines(500)), PROFILE, ld)
        assert not r["ok"] and any("torn" in e for e in r["errors"]), r
        tb = lc.trial_balance(ld)
        assert tb["trustworthy"] is False and tb["torn_tail"] is True, tb


def t_q_calendar_and_bounds():
    """audit #35/#27: تاریخِ ناتقویمی و مبلغِ فراتر از سقف → رد."""
    v = lc.validate_journal(_entry(_bal_lines(), date="2026-99-99"), PROFILE)
    assert not v["ok"], v
    v2 = lc.validate_journal(_entry([
        {"account": "5000", "debit_cents": 10 ** 14, "credit_cents": 0},
        {"account": "1000", "debit_cents": 0, "credit_cents": 10 ** 14}]), PROFILE)
    assert not v2["ok"], v2


def t_r_reverse_of_reversal_reinstates():
    """audit #30: J→R→R2 یعنی J دوباره برقرار است و باید دوباره reverse-پذیر باشد."""
    with tempfile.TemporaryDirectory() as d:
        ld = Path(d)
        jid = lc.post_journal(_entry(_bal_lines(11000)), PROFILE, ld)["journal_id"]
        r1 = lc.reverse_journal(jid, "بار اول", PROFILE, ld)
        assert r1["ok"], r1
        r2 = lc.reverse_journal(r1["journal_id"], "برگشتِ برگشت", PROFILE, ld)
        assert r2["ok"], r2                              # reverseِ reversal مجاز
        r3 = lc.reverse_journal(jid, "بار دوم — J دوباره ایستاده", PROFILE, ld)
        assert r3["ok"], r3                              # J دوباره reverse-پذیر
        tb = lc.trial_balance(ld)
        assert all(s["net_cents"] == 0 for s in tb["accounts"].values()), tb


def t_s_reversal_keeps_tax_code():
    """audit #28/#37: reversal همان tax_code را حمل می‌کند تا تجمیعِ BAS نامتقارن نشود."""
    with tempfile.TemporaryDirectory() as d:
        ld = Path(d)
        lines = [{"account": "5000", "debit_cents": 10000, "credit_cents": 0, "tax_code": "GST"},
                 {"account": "2100", "debit_cents": 1000, "credit_cents": 0, "tax_code": "GST"},
                 {"account": "1000", "debit_cents": 0, "credit_cents": 11000, "tax_code": "N-T"}]
        jid = lc.post_journal(_entry(lines), PROFILE_GST, ld)["journal_id"]
        rv = lc.reverse_journal(jid, "tax", PROFILE_GST, ld)
        assert rv["ok"], rv
        revj = [j for j in lc._read_ledger(ld)["journals"] if j.get("reverses") == jid][0]
        assert [ln.get("tax_code") for ln in revj["lines"]] == ["GST", "GST", "N-T"], revj


def t_t_corrupt_original_reverse_clean_error():
    """audit #10: اصلِ با مبلغِ رشته‌ای → reversal با خطای تمیز، نه crash."""
    with tempfile.TemporaryDirectory() as d:
        ld = Path(d)
        p = ld / "journals.jsonl"
        p.parent.mkdir(parents=True, exist_ok=True)
        import json as _j
        p.write_text(_j.dumps({"journal_id": "j-bad", "entity_id": "armin-abn",
                               "date": "2026-07-01", "lines": [
                                   {"account": "5000", "debit_cents": "بد", "credit_cents": 0},
                                   {"account": "1000", "debit_cents": 0, "credit_cents": 100}],
                               "status": "posted"}, ensure_ascii=False) + "\n", "utf-8")
        r = lc.reverse_journal("j-bad", "تست", PROFILE, ld)
        assert not r["ok"] and any("خراب" in e for e in r["errors"]), r


if __name__ == "__main__":
    for f in (t_a_balanced_posts_unbalanced_rejected, t_b_float_money_rejected,
              t_c_unknown_account_entity_profile, t_d_locked_period_rejected,
              t_e_gst_fail_closed, t_f_idempotent_post, t_g_reversal_not_overwrite,
              t_h_trial_balance_always_balanced,
              t_i_ikey_conflict_different_payload, t_j_rev_namespace_reserved,
              t_k_identical_no_ikey_both_post, t_l_unknown_keys_rejected,
              t_m_gst_control_account_gated, t_n_tax_whitelist_when_open,
              t_o_truthy_gst_still_closed, t_p_torn_tail_blocks_post,
              t_q_calendar_and_bounds, t_r_reverse_of_reversal_reinstates,
              t_s_reversal_keeps_tax_code, t_t_corrupt_original_reverse_clean_error):
        f()
        print("ok", f.__name__)
    print("PASS test_ledger_core")
