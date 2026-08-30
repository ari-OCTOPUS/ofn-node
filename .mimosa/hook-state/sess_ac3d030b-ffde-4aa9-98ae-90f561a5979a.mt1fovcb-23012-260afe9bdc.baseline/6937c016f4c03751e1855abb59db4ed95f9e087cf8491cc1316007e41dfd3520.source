"""test_lead_verdict_wiring.py — D1 (فاز D): وصلِ رأیِ کارتِ لید به لایهٔ اثر.

اثبات می‌کند که LiveLoop.record_proposal_outcome_by_token وقتی رأیِ approve روی یک
کارتِ lead می‌آید، lead_effect_gate.on_lead_verdict را صدا می‌زند — **فقط پشتِ فلگِ
OCTOPUS_WIRE_LEAD_VERDICT_EFFECT**. فلگ خاموش = no-op مطلق (رفتارِ امروز). فلگ روشن:
  · lead_id consented → یک effect ساخته/authorize می‌شود، ولی outbound = NOT_ARMED (صفر ارسال)
  · synthetic/market_signal/lead_id غایب → هیچ effectی
  · gate غایب → fail-closed (on_lead_verdict داخلش deny می‌کند)
  · fail-soft: هر خطا مسیرِ measurement را نمی‌کشد

تست‌ها ساختاراً sandbox هستند (harness.setup → OPS_DIR موقت). STOP/flagِ زنده دست‌نخورده.
"""
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE))
sys.path.insert(0, str(_HERE.parent))
sys.path.insert(0, str(_HERE.parent / "budget"))
sys.path.insert(0, str(_HERE.parent / "legs"))

import harness
ENV = harness.setup("lead-verdict-wiring")

import importlib                          # noqa: E402
import os                                 # noqa: E402
import json                               # noqa: E402
import uuid as _uuid                      # noqa: E402
import opslib                             # noqa: E402
importlib.reload(opslib)
import chrono                             # noqa: E402
importlib.reload(chrono)
import lead_candidate_inbox as lci        # noqa: E402
importlib.reload(lci)
import live_loop                          # noqa: E402
importlib.reload(live_loop)

FLAG = "OCTOPUS_WIRE_LEAD_VERDICT_EFFECT"


def _uniq_eid(tag: str) -> str:
    """هر تست یک external_id یکتا تولید کند تا submit_candidate lead_id متفاوتی برگرداند.
    submit_candidate از کلیدِ idempotencyِ محتوایی استفاده می‌کند، پس بدونِ این، همهٔ تست‌ها
    روی همان lead_id collapse می‌شوند (authz از تستِ قبلی spill می‌کند)."""
    return f"{tag}-{_uuid.uuid4().hex[:8]}"


def _gate():
    """هر تست یک DB موقتِ تازه می‌گیرد (جلوگیری از نشتِ effect بینِ تست‌ها).
   ChronoDB با WAL در همان فایل می‌نویسد، پس uuid-per-test لازم است."""
    import uuid as _uuid
    db = chrono.ChronoDB(str(opslib.STATE_DIR / f"chrono-d1-{_uuid.uuid4().hex[:8]}.db"))
    return chrono.EffectorGate(db), db


def _lead_outbound_effects(db, lead_id=None):
    """همهٔ effectهای lead_outbound را از جدولِ gated_effect بخوان (کمکیِ تست)."""
    rows = db.q("SELECT effect_id, kind, payload_ref, status FROM gated_effect "
                "WHERE kind='lead_outbound'")
    out = [{"effect_id": r[0], "kind": r[1], "target": r[2], "status": r[3]} for r in rows]
    if lead_id is not None:
        out = [e for e in out if e["target"] == lead_id]
    return out


class _FakeChannel:
    """کانالِ mock برای LiveLoop: فقط `.gate` را نگه می‌دارد (تزریق‌شده در wiring).
    send_text هم دارد تا route_leg_proposals (اگر صدا زده شود) crash نکند."""

    def __init__(self, gate):
        self.gate = gate
        self.sent = []

    def send_text(self, text, reply_markup=None):
        self.sent.append(text)
        return True


def _seed_lead(candidate: dict) -> str:
    """یک کاندید را از submit_candidate بگذران تا فایلِ inbox ساخته شود و lead_id برگردد.
    submit_candidate خودش پشتِ OCTOPUS_WIRE_LEAD_CANDIDATES است (پیش‌فرض خاموش)؛ این
    تستِ sandbox آن را فقط برایِ seeding روشن می‌کند (فایلِ inbox لازم است تا hook آن را بخواند)."""
    _prev = os.environ.get("OCTOPUS_WIRE_LEAD_CANDIDATES")
    os.environ["OCTOPUS_WIRE_LEAD_CANDIDATES"] = "1"
    try:
        r = lci.submit_candidate(candidate, source_id="owner")
    finally:
        if _prev is None:
            os.environ.pop("OCTOPUS_WIRE_LEAD_CANDIDATES", None)
        else:
            os.environ["OCTOPUS_WIRE_LEAD_CANDIDATES"] = _prev
    assert r.get("ok"), f"seed failed: {r}"
    return str(r["lead_id"])


def _consented_lead(tag: str = "cons"):
    return {"schema_version": "1.1",
            "source": {"channel": "telegram_manual", "source_id": "owner", "external_id": _uniq_eid(tag)},
            "candidate_type": "consented_inbound",
            "consent": {"basis": "explicit", "evidence": "owner_test"},
            "request": {"scope_text": "D1 test — repaint kitchen"}}


def _synthetic_lead(tag: str = "syn"):
    return {"schema_version": "1.1",
            "source": {"channel": "synthetic_test", "source_id": "owner", "external_id": _uniq_eid(tag)},
            "candidate_type": "consented_inbound",
            "consent": {"basis": "explicit", "evidence": "synthetic"},
            "request": {"scope_text": "D1 synthetic probe"}}


def _market_signal(tag: str = "sig"):
    return {"schema_version": "1.1",
            "source": {"channel": "nsw_da", "source_id": "n8n_da", "external_id": _uniq_eid(tag)},
            "candidate_type": "market_signal", "consent": {"basis": "none"},
            "request": {"scope_text": "D1 signal probe"}}


def _make_loop(gate):
    loop = live_loop.LiveLoop(approval_channel=_FakeChannel(gate))
    return loop


def _prime_token(loop, lead_id):
    """یک ورودیِ _proposal_cb دستی بساز که lead_id داشته باشد (شبیه‌سازیِ کارتِ تحویل‌شده).
    token ثابت؛ برگشتِ idempotency با decided چک می‌شود."""
    tok = "d1token00000000"
    loop._proposal_cb[tok] = {
        "proposal_id": "prop-D1-test",
        "amount": 0.0,
        "kind": "first_response",
        "leg_id": "lead",
        "correlation_id": "corr-d1",
        "mission_id": None,
        "lead_id": lead_id,
        "decided": None,
    }
    return tok


def t_a_flag_off_no_effect():
    """فلگ خاموش (پیش‌فرض) → هیچ effectی ساخته نمی‌شود. رفتارِ امروز بی‌تغییر."""
    os.environ.pop(FLAG, None)
    gate, db = _gate()
    loop = _make_loop(gate)
    lead_id = _seed_lead(_consented_lead("a"))
    tok = _prime_token(loop, lead_id)
    rec = loop.record_proposal_outcome_by_token(tok, "ok")
    assert rec is not None and rec.get("verdict") == "approved"   # measurement ثبت شد
    assert _lead_outbound_effects(db) == [], "فلگ خاموش نباید effectِ lead_outbound بسازد"


def t_b_flag_on_consented_creates_effect_but_not_armed():
    """فلگ روشن + lead_id consented → effect ساخته/authorize می‌شود؛ transport هنوز NOT_ARMED."""
    os.environ[FLAG] = "1"
    try:
        gate, db = _gate()
        loop = _make_loop(gate)
        lead_id = _seed_lead(_consented_lead("b"))
        tok = _prime_token(loop, lead_id)
        rec = loop.record_proposal_outcome_by_token(tok, "ok")
        assert rec is not None and rec.get("verdict") == "approved"
        effs = _lead_outbound_effects(db, lead_id)
        assert len(effs) == 1, f"یک effectِ lead_outbound انتظار می‌رفت، got {len(effs)}"
        # authorized ولی هنوز release نشده → status "pending". مهم: نه sent.
        assert effs[0]["status"] == "pending", f"status عجیب: {effs[0]['status']}"
    finally:
        os.environ.pop(FLAG, None)


def t_c_flag_on_synthetic_denied():
    """فلگ روشن + synthetic lead → on_lead_verdict خودش deny می‌کند (synthetic_never_sends)."""
    os.environ[FLAG] = "1"
    try:
        gate, db = _gate()
        loop = _make_loop(gate)
        lead_id = _seed_lead(_synthetic_lead("c"))
        tok = _prime_token(loop, lead_id)
        rec = loop.record_proposal_outcome_by_token(tok, "ok")   # measurement همچنان ثبت می‌شود
        assert rec is not None
        assert _lead_outbound_effects(db) == [], "synthetic نباید effectِ lead_outbound بگیرد"
    finally:
        os.environ.pop(FLAG, None)


def t_d_flag_on_market_signal_denied():
    """فلگ روشن + market_signal → consent-firewall deny می‌کند (market_signal_never_sends)."""
    os.environ[FLAG] = "1"
    try:
        gate, db = _gate()
        loop = _make_loop(gate)
        os.environ["OCTOPUS_WIRE_LEAD_CANDIDATES"] = "1"
        try:
            r = lci.submit_candidate(_market_signal("d"), source_id="n8n_da")
        finally:
            os.environ.pop("OCTOPUS_WIRE_LEAD_CANDIDATES", None)
        # market_signal فایلِ top-level نمی‌سازد (به signals/ می‌رود) → lead_id داریم ولی فایلِ inbox نه.
        # _fire_lead_effect_hook وقتی فایل نباشد ساکت برمی‌گردد (lead_id دار ولی فایل غایب).
        tok = _prime_token(loop, str(r.get("lead_id") or "no-such"))
        rec = loop.record_proposal_outcome_by_token(tok, "ok")   # measurement همچنان ثبت
        assert rec is not None
        assert _lead_outbound_effects(db) == [], "market_signal نباید effectِ lead_outbound بگیرد"
    finally:
        os.environ.pop(FLAG, None)


def t_e_non_lead_card_no_effect():
    """کارتِ non-lead (lead_id غایب) → hook برمی‌گردد، هیچ effectی."""
    os.environ[FLAG] = "1"
    try:
        gate, db = _gate()
        loop = _make_loop(gate)
        tok = "nolead0000000000"
        loop._proposal_cb[tok] = {
            "proposal_id": "prop-non-lead", "amount": 0.0, "kind": "rfc",
            "leg_id": "doctor", "correlation_id": None, "mission_id": None,
            "lead_id": None, "decided": None,
        }
        rec = loop.record_proposal_outcome_by_token(tok, "ok")
        assert rec is not None
        assert _lead_outbound_effects(db) == []
    finally:
        os.environ.pop(FLAG, None)


def t_f_reject_and_later_no_effect():
    """verb=no/later → فقط measurement، هیچ effectی (فقط approve اثر می‌سازد)."""
    os.environ[FLAG] = "1"
    try:
        gate, db = _gate()
        loop = _make_loop(gate)
        lead_id = _seed_lead(_consented_lead("f"))
        for verb in ("no", "later"):
            tok = f"v{verb}00000000000"[:16]
            loop._proposal_cb[tok] = {
                "proposal_id": f"prop-{verb}", "amount": 0.0, "kind": "first_response",
                "leg_id": "lead", "correlation_id": None, "mission_id": None,
                "lead_id": lead_id, "decided": None,
            }
            loop.record_proposal_outcome_by_token(tok, verb)
        assert _lead_outbound_effects(db) == [], "no/later نباید effect بسازد"
    finally:
        os.environ.pop(FLAG, None)


def t_g_idempotent_double_tap_one_effect():
    """دو تپِ approve روی همان کارت → فقط یک effect (idempotencyِ on_lead_verdict + decided)."""
    os.environ[FLAG] = "1"
    try:
        gate, db = _gate()
        loop = _make_loop(gate)
        lead_id = _seed_lead(_consented_lead("g"))
        tok = _prime_token(loop, lead_id)
        loop.record_proposal_outcome_by_token(tok, "ok")   # اول: effect + decided=True
        loop.record_proposal_outcome_by_token(tok, "ok")   # دوم: decided → None برگشت
        effs = _lead_outbound_effects(db, lead_id)
        assert len(effs) == 1, f"idempotency شکست: {len(effs)} effect"
    finally:
        os.environ.pop(FLAG, None)


def t_h_gate_missing_fail_closed():
    """gate=None (کانال بدونِ gate) → on_lead_verdict fail-closed deny، ولی measurement ثبت می‌شود."""
    os.environ[FLAG] = "1"
    try:
        loop = live_loop.LiveLoop(approval_channel=None)   # channel=None → gate=None
        lead_id = _seed_lead(_consented_lead("h"))
        tok = _prime_token(loop, lead_id)
        rec = loop.record_proposal_outcome_by_token(tok, "ok")
        # measurement همچنان کار می‌کند (لایهٔ اثر از سنجش جدا است)
        assert rec is not None and rec.get("verdict") == "approved"
    finally:
        os.environ.pop(FLAG, None)


def t_i_hook_failure_does_not_kill_measurement():
    """اگر لایهٔ اثر استثنا بدهد، measurement همچنان ثبت می‌شود (fail-soft)."""
    os.environ[FLAG] = "1"
    try:
        # یک gateِ خراب تزریق کن تا on_lead_verdict استثنا بدهد (نه از خودِ on_lead_verdict،
        # بلکه از gate.request). ولی on_lead_verdict خودش همه را try/except کرده → reason=exception.
        # این تست می‌سنجد که حتی اگر چیزی در hook بشکند، record_proposal_outcome برمی‌گردد.
        class _BoomGate:
            def request(self, *a, **k):
                raise RuntimeError("boom")
        loop = live_loop.LiveLoop(approval_channel=_FakeChannel(_BoomGate()))
        lead_id = _seed_lead(_consented_lead("i"))
        tok = _prime_token(loop, lead_id)
        rec = loop.record_proposal_outcome_by_token(tok, "ok")
        assert rec is not None and rec.get("verdict") == "approved", \
            "fail-soft: measurement باید حتی با خطایِ gate ثبت شود"
    finally:
        os.environ.pop(FLAG, None)


def main():
    tests = [v for k, v in sorted(globals().items()) if k.startswith("t_") and callable(v)]
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
    print(f"\ntest_lead_verdict_wiring: {passed}/{len(tests)}")
    if failed:
        for n, e in failed:
            print(f"  FAIL {n}: {e}")
        return 1
    return 0


if __name__ == "__main__":
    import sys as _sys
    _sys.exit(main())
