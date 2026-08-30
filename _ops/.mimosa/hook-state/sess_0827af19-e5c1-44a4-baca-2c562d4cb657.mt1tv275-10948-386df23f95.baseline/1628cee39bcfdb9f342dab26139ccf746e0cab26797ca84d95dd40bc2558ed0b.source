#!/usr/bin/env python3
"""test_lead_gate_handshake.py — برشِ ۱-الف: دستِ live_loop به gate ِ واقعی می‌رسد؟

کشفِ ۲۰۲۶-۰۸-۰۳: `TelegramApprovalChannel.__init__` (approval_channel.py:403)
`self._gate = gate` را ذخیره می‌کند ولی هیچ `def gate` (public) نداشت.
`live_loop._fire_lead_effect_hook` (live_loop.py:628) با
`getattr(chan, "gate", None)` می‌خواندش — که همیشه None برمی‌گرداند، حتی وقتی
`wiring.make_telegram_channel()` یک `chrono.EffectorGate` واقعی تزریق کرده بود
(wiring.py:246،249). یعنی مسیرِ اثرِ لید روی کانالِ **واقعی** همیشه fail-closed
بود؛ فقط فیکِ `test_lead_verdict_wiring._FakeChannel` (که `.gate` را مستقیماً
attribute می‌گذارد و کلاسِ واقعی را دور می‌زند) این را پنهان نگه داشته بود.

advisory ِ `LEAD_EFFECT_HOOK` هم `"armed": False` را hardcode می‌کرد — یعنی حتی
اگر gate واقعی می‌رسید، رسیدِ advisory دروغ می‌گفت.

این فایل کلاسِ **واقعی** (`approval_channel.TelegramApprovalChannel`) را
می‌سازد، نه فیک — تا فیکسِ property را واقعاً بسنجد، نه اینکه دورش بزند.
"""
import os
import sys
import uuid as _uuid
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE))
sys.path.insert(0, str(_HERE.parent))
sys.path.insert(0, str(_HERE.parent / "budget"))
sys.path.insert(0, str(_HERE.parent / "legs"))

import harness
ENV = harness.setup("lead-gate-handshake")

import importlib                       # noqa: E402
import opslib                          # noqa: E402
importlib.reload(opslib)
import chrono                          # noqa: E402
importlib.reload(chrono)
import lead_candidate_inbox as lci     # noqa: E402
importlib.reload(lci)
import live_loop                       # noqa: E402
importlib.reload(live_loop)
from approval_channel import TelegramApprovalChannel   # noqa: E402

FLAG = "OCTOPUS_WIRE_LEAD_VERDICT_EFFECT"


def _uniq_eid(tag: str) -> str:
    return f"{tag}-{_uuid.uuid4().hex[:8]}"


def _real_gate():
    """همان الگوی test_lead_verdict_wiring._gate — DB ِ موقتِ تازه، جدا از هر تستِ دیگر."""
    db = chrono.ChronoDB(str(opslib.STATE_DIR / f"chrono-gh-{_uuid.uuid4().hex[:8]}.db"))
    return chrono.EffectorGate(db), db


def _lead_outbound_effects(db, lead_id=None):
    rows = db.q("SELECT effect_id, kind, payload_ref, status FROM gated_effect "
                "WHERE kind='lead_outbound'")
    out = [{"effect_id": r[0], "kind": r[1], "target": r[2], "status": r[3]} for r in rows]
    if lead_id is not None:
        out = [e for e in out if e["target"] == lead_id]
    return out


def _seed_lead(tag: str) -> str:
    _prev = os.environ.get("OCTOPUS_WIRE_LEAD_CANDIDATES")
    os.environ["OCTOPUS_WIRE_LEAD_CANDIDATES"] = "1"
    try:
        r = lci.submit_candidate({
            "schema_version": "1.1",
            "source": {"channel": "telegram_manual", "source_id": "owner",
                       "external_id": _uniq_eid(tag)},
            "candidate_type": "consented_inbound",
            "consent": {"basis": "explicit", "evidence": "owner_test"},
            "request": {"scope_text": "gate-handshake test — repaint kitchen"},
        }, source_id="owner")
    finally:
        if _prev is None:
            os.environ.pop("OCTOPUS_WIRE_LEAD_CANDIDATES", None)
        else:
            os.environ["OCTOPUS_WIRE_LEAD_CANDIDATES"] = _prev
    assert r.get("ok"), f"seed failed: {r}"
    return str(r["lead_id"])


def _prime_token(loop, lead_id, tok="ghtoken0000000000"):
    loop._proposal_cb[tok] = {
        "proposal_id": "prop-GH-test", "amount": 0.0, "kind": "first_response",
        "leg_id": "lead", "correlation_id": "corr-gh", "mission_id": None,
        "lead_id": lead_id, "decided": None,
    }
    return tok


def _last_hook_advisory(loop):
    for ev in reversed(loop._advisory_signals):
        if ev.get("type") == "LEAD_EFFECT_HOOK":
            return ev["payload"]
    return None


def t_a_property_returns_the_injected_gate():
    """رفعِ ریشه‌ای: `.gate` روی کلاسِ واقعی همان شیءِ تزریق‌شده را برمی‌گرداند."""
    sentinel = object()
    chan = TelegramApprovalChannel(gate=sentinel)
    assert chan.gate is sentinel
    # همان الگوی دقیقِ live_loop.py:628 — getattr با defaultِ None
    assert getattr(chan, "gate", None) is sentinel


def t_b_property_is_none_when_not_wired():
    """کانالِ بدونِ gate (rare ولی معتبر) → None، نه AttributeError."""
    chan = TelegramApprovalChannel()
    assert chan.gate is None
    assert getattr(chan, "gate", None) is None


def t_c_real_channel_end_to_end_creates_effect():
    """قلبِ رگرسیون: قبل از فیکس این تست با _FakeChannel سبز می‌ماند ولی با کانالِ
    واقعی هیچ effectی نمی‌ساخت (gate همیشه None می‌رسید). با فیکس، effect ساخته
    می‌شود — دقیقاً مثلِ t_b_flag_on_consented_creates_effect_but_not_armed ِ
    سوییتِ خواهر، ولی روی کلاسِ واقعی."""
    os.environ[FLAG] = "1"
    try:
        gate, db = _real_gate()
        chan = TelegramApprovalChannel(gate=gate)
        loop = live_loop.LiveLoop(approval_channel=chan)
        lead_id = _seed_lead("c")
        tok = _prime_token(loop, lead_id)
        rec = loop.record_proposal_outcome_by_token(tok, "ok")
        assert rec is not None and rec.get("verdict") == "approved"
        effs = _lead_outbound_effects(db, lead_id)
        assert len(effs) == 1, (
            f"gate از کانالِ واقعی به bridge_from_inbox نرسید — {len(effs)} effect ساخته شد "
            f"(انتظار ۱). این دقیقاً همان باگی است که این فایل رفع می‌کند.")
        assert effs[0]["status"] == "pending"
    finally:
        os.environ.pop(FLAG, None)


def t_d_advisory_reports_armed_true_when_gate_present():
    """advisory دیگر armed=False را hardcode نمی‌کند — وقتی gate واقعی رسید True است."""
    os.environ[FLAG] = "1"
    try:
        gate, _db = _real_gate()
        chan = TelegramApprovalChannel(gate=gate)
        loop = live_loop.LiveLoop(approval_channel=chan)
        lead_id = _seed_lead("d")
        tok = _prime_token(loop, lead_id, tok="ghtoken0000000001")
        loop.record_proposal_outcome_by_token(tok, "ok")
        payload = _last_hook_advisory(loop)
        assert payload is not None, "advisoryِ LEAD_EFFECT_HOOK ثبت نشد"
        assert payload["armed"] is True, f"gate واقعی بود ولی armed={payload['armed']!r}"
    finally:
        os.environ.pop(FLAG, None)


def t_e_advisory_reports_armed_false_when_gate_absent():
    """کانال بدونِ gate → armed=False واقعی (نه hardcode — نتیجهٔ محاسبه)."""
    os.environ[FLAG] = "1"
    try:
        chan = TelegramApprovalChannel()   # gate=None
        loop = live_loop.LiveLoop(approval_channel=chan)
        tok = "ghtoken0000000002"
        loop._proposal_cb[tok] = {
            "proposal_id": "prop-GH-e", "amount": 0.0, "kind": "first_response",
            "leg_id": "lead", "correlation_id": None, "mission_id": None,
            "lead_id": "no-such-lead-e", "decided": None,
        }
        loop.record_proposal_outcome_by_token(tok, "ok")
        payload = _last_hook_advisory(loop)
        assert payload is not None, "advisoryِ LEAD_EFFECT_HOOK ثبت نشد"
        assert payload["armed"] is False
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
    print(f"\ntest_lead_gate_handshake: {passed}/{len(tests)}")
    if failed:
        for n, e in failed:
            print(f"  FAIL {n}: {e}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
