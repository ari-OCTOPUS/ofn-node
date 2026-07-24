"""test_consent_gate.py — D2a (فاز D): consent_store + consent_gate هستهٔ ایمنی.

اثبات می‌کند که:
  · CHECK firewall لایهٔ ۱ (SQL): market_signal+outreach=1 غیرممکن (t1).
  · derive_outreach_allowed لایهٔ ۲: truth-table کامل، none/unknown همیشه False (t2).
  · may_draft flag خاموش = (False, "flag-off") — وارونهٔ fail-soft (t3).
  · suppression قبل از هر draft بلاک می‌کند؛ بعد از purge رکورد هم پابرجا (t4).
  · compliance_state=RISK_FLAGGED → may_release=False (t7 — D2a variant).
  · public_b2b بدونِ evidence منتشرشده → outreach False (t8).
  · synthetic_test → may_release=False (t9).
  · replayِ همان event → یک ردیف (idempotency، t10).

همه sandbox (harness.setup → OPS_DIR موقت). flag/STOP/ACTIVATION زنده دست‌نخورده.
"""
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE))
sys.path.insert(0, str(_HERE.parent))
sys.path.insert(0, str(_HERE.parent / "legs"))

import harness
ENV = harness.setup("consent-gate-d2a")

import importlib                          # noqa: E402
import os                                 # noqa: E402
import sqlite3                            # noqa: E402
import uuid as _uuid                      # noqa: E402
import opslib                             # noqa: E402
importlib.reload(opslib)
import consent_store as cs                # noqa: E402
importlib.reload(cs)
import consent_gate as cg                 # noqa: E402
importlib.reload(cg)

FLAG = cg.FLAG


def _store():
    """هر تست یک db تازه (جلوگیری از spill، الگوی test_lead_verdict_wiring)."""
    return cs.ConsentStore(str(opslib.STATE_DIR / f"consent-d2a-{_uuid.uuid4().hex[:8]}.db"))


def _consented_rec(lead_id="L1"):
    return {"lead_id": lead_id, "candidate_type": "consented_inbound",
            "consent_basis": "explicit", "consent_evidence": "quote_form",
            "consent_state": "CONSENTED_INBOUND", "compliance_state": "UNREVIEWED",
            "outreach_allowed": True, "retention_class": "consented_customer",
            "retention_anchor_at": "2026-07-21T00:00:00+00:00",
            "source_channel": "telegram_manual"}


def _b2b_rec(lead_id="L2"):
    return {"lead_id": lead_id, "candidate_type": "public_b2b",
            "consent_basis": "inferred_business",
            "consent_evidence": "office_contact_conspicuously_published",
            "consent_state": "B2B_PROSPECT", "compliance_state": "UNREVIEWED",
            "outreach_allowed": True, "retention_class": "b2b_prospect_12m",
            "retention_anchor_at": "2026-07-21T00:00:00+00:00",
            "source_channel": "escalated_b2b"}


def _signal_rec(lead_id="L3"):
    return {"lead_id": lead_id, "candidate_type": "market_signal",
            "consent_basis": "none", "consent_state": "SIGNAL_ONLY",
            "compliance_state": "UNREVIEWED", "outreach_allowed": False,
            "retention_class": "signal_30d",
            "retention_anchor_at": "2026-07-21T00:00:00+00:00",
            "source_channel": "nsw_da"}


def t1_check_firewall_blocks_market_signal_outreach():
    """لایهٔ ۱ firewall: upsert market_signal با outreach_allowed=1 → IntegrityError (fail-closed)."""
    os.environ[FLAG] = "1"
    try:
        st = _store()
        bad = _signal_rec()
        bad["outreach_allowed"] = True   # ← تلاش برای دروغ
        try:
            st.upsert_current(bad)
            assert False, "باید IntegrityError می‌داد (firewall CHECK)"
        except sqlite3.IntegrityError:
            pass   # ✅ همانطور که انتظار بود رد شد
    finally:
        os.environ.pop(FLAG, None)


def t2_derive_outreach_allowed_truth_table():
    """لایهٔ ۲ firewall: derive — همهٔ ترکیب‌ها. none/unknown همیشه False."""
    # consented_inbound + explicit + evidence → True
    assert cg.derive_outreach_allowed({"candidate_type": "consented_inbound",
                                       "consent_basis": "explicit",
                                       "consent_evidence": "x"}) is True
    # consented_inbound بدونِ evidence → False
    assert cg.derive_outreach_allowed({"candidate_type": "consented_inbound",
                                       "consent_basis": "explicit"}) is False
    # public_b2b + inferred_business + published evidence → True
    assert cg.derive_outreach_allowed({"candidate_type": "public_b2b",
                                       "consent_basis": "inferred_business",
                                       "consent_evidence": "office_contact_conspicuously_published"}) is True
    # public_b2b بدونِ evidence منتشرشده → False
    assert cg.derive_outreach_allowed({"candidate_type": "public_b2b",
                                       "consent_basis": "inferred_business",
                                       "consent_evidence": "weak"}) is False
    # market_signal همیشه False
    for basis in ("explicit", "inferred_business", "none", "unknown", ""):
        assert cg.derive_outreach_allowed({"candidate_type": "market_signal",
                                           "consent_basis": basis,
                                           "consent_evidence": "x"}) is False, \
            f"market_signal با basis={basis} نباید outreach بگیرد"
    # basis none/unknown همیشه False (حتی با consented_inbound)
    for basis in ("none", "unknown"):
        assert cg.derive_outreach_allowed({"candidate_type": "consented_inbound",
                                           "consent_basis": basis,
                                           "consent_evidence": "x"}) is False, \
            f"basis={basis} نباید outreach بگیرد"
    # هر چیزِ عجیب → False
    assert cg.derive_outreach_allowed({}) is False
    assert cg.derive_outreach_allowed({"candidate_type": "???", "consent_basis": "???"}) is False


def t3_may_draft_flag_off_returns_false_flag_off():
    """وارونهٔ fail-soft: flag خاموش = (False, 'flag-off')، نه skip."""
    os.environ.pop(FLAG, None)
    st = _store()
    st.upsert_current(_consented_rec("L1a"))
    ok, why = cg.may_draft("L1a", store=st)
    assert ok is False and why == "flag-off", f"got ({ok}, {why})"


def t4_suppression_blocks_before_draft_and_survives_purge():
    """contactِ suppressed → may_draft=False حتی برای CONSENTED_INBOUND.
    بعد از purgeِ رکورد هم ردیفِ suppression پابرجا."""
    os.environ[FLAG] = "1"
    try:
        st = _store()
        phone_norm = cg.normalize_phone("+61412345678")
        rec = _consented_rec("L1b")
        rec["contact_value_norm"] = phone_norm   # inbox هنگامِ upsert این را ست می‌کند
        st.upsert_current(rec)
        # قبل از suppression: مجاز
        ok, _ = cg.may_draft("L1b", store=st)
        assert ok is True
        # بعد از suppression: بلاک
        st.insert_suppression(phone_norm, "phone", "manual_dnc")
        ok, why = cg.may_draft("L1b", store=st)
        assert ok is False and why.startswith("suppressed:"), f"got ({ok}, {why})"
        # purge رکورد: suppression پابرجا. رکوردِ PURGED باید outreach_allowed=False
        # داشته باشد (firewall CHECK اجازهٔ PURGED+outreach=1 نمی‌دهد — درست هم هست).
        rec2 = _consented_rec("L1b")
        rec2["purged"] = True
        rec2["consent_state"] = "PURGED"
        rec2["outreach_allowed"] = False
        rec2["contact_value_norm"] = phone_norm
        st.upsert_current(rec2)
        # ردیفِ suppression هنوز فعال است
        assert st.suppression_active(phone_norm) == "manual_dnc"
        # و رکوردِ نو با همان phone هم بلاک می‌شود
        rec3 = _consented_rec("L1b-new")
        rec3["contact_value_norm"] = phone_norm
        st.upsert_current(rec3)
        ok, why = cg.may_draft("L1b-new", store=st)
        assert ok is False and why.startswith("suppressed:")
    finally:
        os.environ.pop(FLAG, None)


def t7_compliance_risk_flagged_blocks_release():
    """compliance_state=RISK_FLAGGED → may_release=False (D2a variant: UNREVIEWED اجازه می‌دهد)."""
    os.environ[FLAG] = "1"
    try:
        st = _store()
        # UNREVIEWED → در D2a اجازه می‌دهد (D2b سخت‌گیرانه‌تر)
        rec = _consented_rec("L1c")
        rec["compliance_state"] = "UNREVIEWED"
        st.upsert_current(rec)
        ok, _ = cg.may_release("L1c", "lead_outbound", store=st)
        assert ok is True, "UNREVIEWED در D2a باید اجازه دهد (D2b سخت‌گیرانه‌تر)"
        # RISK_FLAGGED → deny
        rec2 = _consented_rec("L1d")
        rec2["compliance_state"] = "RISK_FLAGGED"
        st.upsert_current(rec2)
        ok, why = cg.may_release("L1d", "lead_outbound", store=st)
        assert ok is False and why == "compliance:RISK_FLAGGED", f"got ({ok}, {why})"
        # OWNER_CLEARED → اجازه
        rec3 = _consented_rec("L1e")
        rec3["compliance_state"] = "OWNER_CLEARED"
        st.upsert_current(rec3)
        ok, _ = cg.may_release("L1e", "lead_outbound", store=st)
        assert ok is True
    finally:
        os.environ.pop(FLAG, None)


def t8_b2b_without_published_evidence_no_outreach():
    """public_b2b بدونِ evidence منتشرشده → outreach False (بیزنس ≠ رضایتِ residential)."""
    os.environ[FLAG] = "1"
    try:
        st = _store()
        # با evidence منتشرشده → مجاز
        st.upsert_current(_b2b_rec("L2a"))
        ok, _ = cg.may_draft("L2a", store=st)
        assert ok is True
        # بدونِ evidence منتشرشده (consent-derivation deny) — ولی upsert با outreach=False مجاز است
        # (consent_gate derive دوباره چک می‌کند؛ ذخیرهٔ ۱ با CHECK سازگار است چون outreach=False)
        rec = _b2b_rec("L2b")
        rec["consent_evidence"] = "weak"
        rec["outreach_allowed"] = False
        st.upsert_current(rec)
        ok, why = cg.may_draft("L2b", store=st)
        assert ok is False and why == "consent-derivation", f"got ({ok}, {why})"
    finally:
        os.environ.pop(FLAG, None)


def t9_synthetic_may_release_false():
    """synthetic_test → may_release=False (G-SYNTH، حتی اگر consented)."""
    os.environ[FLAG] = "1"
    try:
        st = _store()
        rec = _consented_rec("L1f")
        rec["source_channel"] = "synthetic_test"
        st.upsert_current(rec)
        # may_draft موفق می‌شود (state CONSENTED + derive) ولی may_release synthetic را بلاک می‌کند
        ok, _ = cg.may_draft("L1f", store=st)
        assert ok is True, "synthetic در may_draft مجاز است (تا کارت)"
        ok, why = cg.may_release("L1f", "lead_outbound", store=st)
        assert ok is False and why == "synthetic-hard-block", f"got ({ok}, {why})"
    finally:
        os.environ.pop(FLAG, None)


def t10_event_replay_idempotent():
    """replayِ همان event با همان idempotency_key → یک ردیف (نه دو)."""
    os.environ[FLAG] = "1"
    try:
        st = _store()
        ev = {"lead_id": "L1g", "event_type": "consent.classified",
              "from_state": "RECEIVED", "to_state": "CONSENTED_INBOUND",
              "actor": "inbox", "idempotency_key": "L1g|consent.classified|CONSENTED_INBOUND",
              "payload": {"foo": "bar"}}
        first = st.record_event(ev)
        second = st.record_event(ev)   # همان idempotency_key
        assert first is True, "اولین درج باید True باشد"
        assert second is False, "دومین درج با همان key باید False (idempotent) باشد"
        # فقط یک ردیف در جدول
        events = st.events_for_lead("L1g")
        assert len(events) == 1, f"باید ۱ ردیف باشد، got {len(events)}"
    finally:
        os.environ.pop(FLAG, None)


def t11_load_current_none_for_missing():
    """load_current برای lead_id ناموجود → None."""
    os.environ[FLAG] = "1"
    try:
        st = _store()
        assert st.load_current("does-not-exist") is None
    finally:
        os.environ.pop(FLAG, None)


def t12_may_release_kind_allowlist():
    """effect_kind که lead_outbound نیست → deny (allowlist ساده در D2a)."""
    os.environ[FLAG] = "1"
    try:
        st = _store()
        st.upsert_current(_consented_rec("L1h"))
        ok, why = cg.may_release("L1h", "send", store=st)
        assert ok is False and why == "kind-not-allowlisted", f"got ({ok}, {why})"
        ok, _ = cg.may_release("L1h", "lead_outbound", store=st)
        assert ok is True
    finally:
        os.environ.pop(FLAG, None)


def main():
    # الگوی نام‌گذاری: tN_<desc> (تطبیقِ t1_, t2_, ..., t12_). ترتیب بر اساسِ حرف.
    tests = [v for k, v in sorted(globals().items())
             if k.startswith("t") and k[1:2].isdigit() and callable(v)
             and not k.startswith("test")]
    passed = 0
    failed = []
    for t in tests:
        try:
            t()
            passed += 1
            print(f"  ✅ {t.__name__}")
        except Exception as e:  # noqa: BLE001
            failed.append((t.__name__, repr(e)))
            print(f"  ❌ {t.__name__}: {e!r}")
    print(f"\ntest_consent_gate: {passed}/{len(tests)}")
    if failed:
        for n, e in failed:
            print(f"  FAIL {n}: {e}")
        return 1
    return 0


if __name__ == "__main__":
    import sys as _sys
    _sys.exit(main())
