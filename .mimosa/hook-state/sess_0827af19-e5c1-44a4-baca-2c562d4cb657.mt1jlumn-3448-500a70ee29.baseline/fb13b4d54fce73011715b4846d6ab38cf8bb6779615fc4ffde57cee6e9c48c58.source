"""test_consent_firewall.py — Trust-Engine P0: دیوارِ رضایت (structural، fail-closed).

نامتغیرها: market_signal هرگز outreach؛ رضایتِ غایب/نامعلوم → بسته؛ public_b2b ≠ رضایتِ
مسکونی؛ هر استثنا → بسته. هیچ مسیری نباید یک سیگنال را به outreach برساند.
"""
import os
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE.parent / "legs"))
import consent_firewall as cf   # noqa: E402


def _c(ctype=None, channel=None, basis=None, evidence=None, **kw):
    d = {"consent": {}, "source": {}}
    if ctype is not None:
        d["candidate_type"] = ctype
    if channel is not None:
        d["source"]["channel"] = channel
    if basis is not None:
        d["consent"]["basis"] = basis
    if evidence is not None:
        d["consent"]["evidence"] = evidence
    d.update(kw)
    return d


def t_a_market_signal_never_outreach():
    """R1: هیچ ترکیبی از فیلدها نمی‌تواند market_signal را outreach کند."""
    for basis in ("none", "unknown", "explicit", "inferred_business", "bogus"):
        for ev in (None, "office_contact_published", "submitted_quote_form"):
            c = _c(ctype="market_signal", basis=basis, evidence=ev, channel="nsw_da")
            r = cf.evaluate(c)
            assert r["outreach_allowed"] is False, (basis, ev, r)
            assert cf.may_outreach(c) is False


def t_b_missing_consent_fails_closed():
    """R2: basis غایب/none/unknown → بسته، حتی برای consented_inbound."""
    for basis in (None, "none", "unknown", "", "garbage"):
        r = cf.evaluate(_c(ctype="consented_inbound", basis=basis, channel="telegram_manual"))
        assert r["outreach_allowed"] is False, (basis, r)


def t_c_consented_inbound_explicit_allowed():
    """consented_inbound + basis=explicit → مجاز (خودشان درخواست کردند)."""
    r = cf.evaluate(_c(ctype="consented_inbound", basis="explicit",
                       evidence="submitted_quote_form", channel="telegram_manual"))
    assert r["outreach_allowed"] is True
    assert r["retention_class"] == "consented_customer"


def t_d_public_b2b_needs_inferred_business_and_evidence():
    """R3: public_b2b فقط با inferred_business + evidence مجاز؛ وگرنه بسته.
    یک تماسِ b2b هرگز رضایتِ مسکونی تلقی نمی‌شود. public_b2b فقط از کانالِ escalation
    می‌آید (نه اعلامِ خام producer روی کانالِ سیگنال)."""
    assert cf.evaluate(_c(ctype="public_b2b", channel="escalated_b2b", basis="inferred_business",
                          evidence="office_contact_published"))["outreach_allowed"] is True
    # بدونِ evidence → بسته
    assert cf.evaluate(_c(ctype="public_b2b", channel="escalated_b2b",
                          basis="inferred_business"))["outreach_allowed"] is False
    # basis=explicit روی b2b (تلاش برای جا زدنِ رضایتِ مسکونی) → بسته
    assert cf.evaluate(_c(ctype="public_b2b", channel="escalated_b2b", basis="explicit",
                          evidence="x"))["outreach_allowed"] is False


def t_e_classify_channel_fallback_is_market_signal():
    """کانالِ ناشناخته یا نوعِ نامعتبر → market_signal (سخت‌گیرانه‌ترین)."""
    assert cf.classify(_c(channel="totally_unknown_channel")) == "market_signal"
    assert cf.classify(_c(ctype="not_a_real_type", channel="nsw_da")) == "market_signal"
    assert cf.classify(_c(channel="telegram_manual")) == "consented_inbound"
    assert cf.classify(_c(channel="facebook_group")) == "market_signal"


def t_f_exception_input_fails_closed():
    """R4: ورودیِ خراب/غیرمنتظره → کاملاً بسته، بدونِ پرتابِ استثنا."""
    for bad in (None, [], "string", 42, {"consent": "not-a-dict"},
                {"source": 5, "consent": {"basis": "explicit"}}):
        try:
            r = cf.evaluate(bad)
        except Exception as e:  # noqa: BLE001
            assert False, f"firewall نباید استثنا بدهد: {type(e).__name__} روی {bad!r}"
        assert r["outreach_allowed"] is False, (bad, r)
        assert cf.may_outreach(bad) is False


def t_h_signal_channel_cannot_be_upgraded_by_declared_type():
    """رگرسیونِ راستی‌آزماییِ متخاصمِ 2026-07-21 (R4-critical): یک رکوردِ کانالِ سیگنال‌محور
    که خود را consented_inbound + explicit اعلام می‌کند، هرگز نباید outreach بگیرد.
    declared نمی‌تواند از سقفِ کانال بالاتر برود."""
    for ch in ("nsw_da", "domain_listing", "facebook_group", "totally_unknown"):
        c = _c(ctype="consented_inbound", channel=ch, basis="explicit", evidence="scraped")
        assert cf.classify(c) == "market_signal", (ch, cf.classify(c))
        r = cf.evaluate(c)
        assert r["outreach_allowed"] is False, (ch, r)
        assert r["retention_class"] == "signal_30d", (ch, r)   # نه consented_customer
    # همچنین: کانالِ سیگنال که خود را public_b2b اعلام کند → clamp به market_signal
    c2 = _c(ctype="public_b2b", channel="nsw_da", basis="inferred_business", evidence="x")
    assert cf.classify(c2) == "market_signal"
    assert cf.evaluate(c2)["outreach_allowed"] is False
    # کانالِ consent-محور همچنان downgrade به market_signal را می‌پذیرد (≤ سقف)
    assert cf.classify(_c(ctype="market_signal", channel="telegram_manual")) == "market_signal"


def t_g_synthetic_test_channel_is_consented_but_gate_blocks_downstream():
    """synthetic_test به consented_inbound نگاشت می‌شود (تا کلِ لوله را طی کند)
    ولی رضایتش تنها وقتی مجاز است که basis=explicit — بلاکِ سختِ ارسال جای EffectorGate است."""
    assert cf.classify(_c(channel="synthetic_test")) == "consented_inbound"
    # حتی synthetic بدونِ basis صریح → بسته (fail-closed)
    assert cf.evaluate(_c(channel="synthetic_test", basis="none"))["outreach_allowed"] is False


if __name__ == "__main__":
    checks = [(n, f) for n, f in sorted(globals().items()) if n.startswith("t_")]
    failed = 0
    for name, fn in checks:
        try:
            fn()
            print(f"  ✅ {name}")
        except AssertionError as e:
            failed += 1
            print(f"  ❌ {name}: {e}")
    print(f"\n{'✅' if not failed else '❌'} test_consent_firewall: "
          f"{len(checks) - failed}/{len(checks)}")
    sys.exit(1 if failed else 0)
