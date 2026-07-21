"""test_lead_effect_gate.py — LEAD-SAFETY-C1: per-effect gate + kill batch-release footgun.

اثبات می‌کند ارسالِ لید یکی-یکی، صریح، fail-closed است و **هرگز نمی‌فرستد**:
- batch-release (release_gated_effects) نمی‌تواند kindِ lead_outbound را آزاد کند (footgun بسته)
- release_one دقیقاً یکی را آزاد می‌کند
- market_signal/synthetic/بدون-authorization/STOP/gate-غایب → deny (fail-closed، بی‌crash)
- idempotent (double-authorize/settled دوباره release نمی‌شود)
- outbound_worker همیشه NOT_ARMED (صفر ارسال)، flag خاموش = بی‌اثر
"""
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE))
sys.path.insert(0, str(_HERE.parent))
sys.path.insert(0, str(_HERE.parent / "budget"))
sys.path.insert(0, str(_HERE.parent / "legs"))

import harness
ENV = harness.setup("lead-effect-gate")

import importlib                     # noqa: E402
import opslib                        # noqa: E402
importlib.reload(opslib)
import chrono                        # noqa: E402
importlib.reload(chrono)
import consent_firewall              # noqa: E402
importlib.reload(consent_firewall)
import lead_effect_gate as leg       # noqa: E402
importlib.reload(leg)
import outbound_worker as ow         # noqa: E402
importlib.reload(ow)

_H_MS = 3_600_000


def _gate():
    db = chrono.ChronoDB(str(opslib.STATE_DIR / "chrono-c1.db"))
    return chrono.EffectorGate(db), db


def _consented():
    return {"schema_version": "1.1",
            "source": {"channel": "telegram_manual", "source_id": "owner", "external_id": "e1"},
            "candidate_type": "consented_inbound",
            "consent": {"basis": "explicit", "evidence": "quote_form"},
            "contact": {"preferred_channel": "sms"},
            "request": {"scope_text": "repaint hallway"}}


def t_a_batch_release_cannot_release_lead_outbound():
    """footgun بسته: یک human-append (release_gated_effects) kindِ lead_outbound را آزاد نمی‌کند."""
    gate, db = _gate()
    eid_lead = gate.request("lead_outbound", "lead-1", beat=1)
    eid_send = gate.request("send", "money-1", beat=1)      # kindِ پول (مسیرِ قدیمی)
    n = gate.release_gated_effects({"hash": "human-append-h1"})
    assert gate.status_of(eid_send) == "releasable"          # پول آزاد شد (بی‌تغییر)
    assert gate.status_of(eid_lead) == "pending", "lead_outbound نباید با batch آزاد شود"
    assert n == 1                                             # فقط یکی (send)، نه lead


def t_b_release_one_targets_exactly_one():
    gate, db = _gate()
    e1 = gate.request("lead_outbound", "L1", beat=1)
    e2 = gate.request("lead_outbound", "L2", beat=1)
    assert gate.release_one(e1, {"hash": "tok-1"}) is True
    assert gate.status_of(e1) == "releasable"
    assert gate.status_of(e2) == "pending"                   # فقط e1 آزاد شد
    # بدونِ ref → fail-closed
    assert gate.release_one(e2, {"hash": ""}) is False
    assert gate.status_of(e2) == "pending"


def t_c_market_signal_denied_at_gate():
    """دفاع در عمق (R4): حتی با authorization، یک market_signal آزاد نمی‌شود."""
    gate, db = _gate()
    eid = gate.request("lead_outbound", "sig-1", beat=1)
    leg.authorize(eid, "sig-1", "tok")
    sig = {"source": {"channel": "nsw_da"}, "candidate_type": "market_signal",
           "consent": {"basis": "none"}, "request": {"scope_text": "DA"}}
    r = leg.may_release(eid, sig, gate=gate)
    assert r["allow"] is False and r["reason"] == "market_signal_never_sends", r


def t_d_synthetic_denied_at_gate():
    gate, db = _gate()
    eid = gate.request("lead_outbound", "syn-1", beat=1)
    leg.authorize(eid, "syn-1", "tok")
    syn = dict(_consented())
    syn["source"] = {"channel": "synthetic_test", "source_id": "owner"}
    r = leg.may_release(eid, syn, gate=gate)
    assert r["allow"] is False and r["reason"] == "synthetic_never_sends", r


def t_e_not_authorized_denied():
    """allowlist پیش‌فرض خالی → لیدِ معتبرِ authorize‌نشده آزاد نمی‌شود."""
    gate, db = _gate()
    eid = gate.request("lead_outbound", "L-unauth", beat=1)
    r = leg.may_release(eid, _consented(), gate=gate)
    assert r["allow"] is False and r["reason"] == "not_authorized", r


def t_f_halt_denied():
    gate, db = _gate()
    eid = gate.request("lead_outbound", "L-halt", beat=1)
    leg.authorize(eid, "L-halt", "tok")
    stop = opslib.STOP_ORGANISM
    stop.parent.mkdir(parents=True, exist_ok=True)
    stop.write_text("stop", "utf-8")
    try:
        r = leg.may_release(eid, _consented(), gate=gate)
        assert r["allow"] is False and r["reason"].startswith("halted"), r
    finally:
        try:
            stop.unlink()
        except OSError:
            pass


def t_g_no_gate_fail_closed_no_crash():
    """gate=None و ورودیِ خراب → deny، بدونِ استثنا، بدونِ send."""
    for bad in (None, [], "str", {"source": 5}):
        try:
            r = leg.may_release("eid", bad, gate=None)
        except Exception as e:  # noqa: BLE001
            assert False, f"may_release نباید crash کند روی {bad!r}: {type(e).__name__}"
        assert r["allow"] is False, (bad, r)


def t_h_happy_path_settles_but_transport_not_armed():
    """authorize → may_release allow → release_and_settle → settled؛ ولی outbound = NOT_ARMED."""
    gate, db = _gate()
    eid = gate.request("lead_outbound", "L-ok", beat=1)
    leg.authorize(eid, "L-ok", "human-token-xyz")
    now = 1_000_000_000_000
    r = leg.release_and_settle(eid, _consented(), gate=gate, now_ms=now)
    assert r["released"] is True and r["settled"] is True, r
    assert gate.status_of(eid) == "settled"
    # outbound worker: flag روشن هم = NOT_ARMED (صفر ارسال)
    import os
    os.environ["OCTOPUS_WIRE_LEAD_OUTBOUND"] = "1"
    try:
        eid2 = gate.request("lead_outbound", "L-ok2", beat=1)
        leg.authorize(eid2, "L-ok2", "tok2")
        out = ow.send_one(eid2, _consented(), gate=gate, now_ms=now)
    finally:
        os.environ.pop("OCTOPUS_WIRE_LEAD_OUTBOUND", None)
    assert out["sent"] is False and out["status"] == "NOT_ARMED", out


def t_i_idempotent_settled_not_re_released():
    gate, db = _gate()
    eid = gate.request("lead_outbound", "L-idem", beat=1)
    a1 = leg.authorize(eid, "L-idem", "tok")
    a2 = leg.authorize(eid, "L-idem", "tok-different")   # idempotent — همان اولی
    assert a1["ok"] and a2["reason"] == "already_authorized"
    now = 1_000_000_000_000
    r1 = leg.release_and_settle(eid, _consented(), gate=gate, now_ms=now)
    assert r1["settled"] is True
    # بارِ دوم: settled → deny (idempotent)
    r2 = leg.may_release(eid, _consented(), gate=gate)
    assert r2["allow"] is False and r2["reason"] == "already_settled", r2


def t_j_outbound_flag_off_inert():
    gate, db = _gate()
    eid = gate.request("lead_outbound", "L-off", beat=1)
    leg.authorize(eid, "L-off", "tok")
    out = ow.send_one(eid, _consented(), gate=gate)   # flag off (پیش‌فرض)
    assert out["sent"] is False and out["status"] == "flag_off", out
    assert gate.status_of(eid) == "pending"           # هیچ آزادسازی رخ نداد


def t_k_no_network_imports():
    """ساختاری (AST، نه substring — ذکرِ نامِ transport در docstring مجاز است): هیچ ماژولِ
    شبکه/ارسال واقعاً import نمی‌شود در outbound_worker یا lead_effect_gate."""
    import ast
    forbidden = {"smtplib", "requests", "twilio", "sendgrid", "socket",
                 "http", "urllib", "ftplib", "telnetlib"}
    for mod in (ow, leg):
        tree = ast.parse(Path(mod.__file__).read_text("utf-8"))
        imported = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for n in node.names:
                    imported.add(n.name.split(".")[0])
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported.add(node.module.split(".")[0])
        leaked = imported & forbidden
        assert not leaked, f"{mod.__name__}: سطحِ شبکهٔ ممنوع import شد: {leaked}"


def t_l_batch_allowlist_blocks_noncanonical_customer_kinds():
    """رگرسیونِ متخاصم (2026-07-21): batch-release حالا allowlist است — kindهای
    غیر-canonicalِ ارسال (casing/whitespace/synonym) fail-safe فقط per-effect می‌روند."""
    gate, db = _gate()
    # kindهای پول (هر case) → همچنان batch-release
    e_send = gate.request("send", "m1", beat=1)
    e_pay = gate.request("PAY", "m2", beat=1)          # uppercase پول (test_telegram_channel)
    # kindهای ارسال با هجیِ غیر-canonical → نباید batch شوند
    e_up = gate.request("LEAD_OUTBOUND", "c1", beat=1)
    e_sp = gate.request("lead_outbound ", "c2", beat=1)   # trailing space
    e_syn = gate.request("sms_send", "c3", beat=1)         # synonym خارج از allowlist
    gate.release_gated_effects({"hash": "h"})
    assert gate.status_of(e_send) == "releasable"     # پول آزاد شد
    assert gate.status_of(e_pay) == "releasable"      # PAY (lower(trim)→pay) آزاد شد
    assert gate.status_of(e_up) == "pending", "LEAD_OUTBOUND نباید batch شود"
    assert gate.status_of(e_sp) == "pending", "'lead_outbound ' نباید batch شود"
    assert gate.status_of(e_syn) == "pending", "sms_send (سینونیمِ ناشناخته) نباید batch شود"


def t_m_synthetic_guard_normalizes_whitespace():
    """رگرسیونِ متخاصم: کانالِ ' synthetic_test' (فاصله/تب/newline/case) دیگر گارد را دور نمی‌زند."""
    gate, db = _gate()
    for ch in (" synthetic_test", "synthetic_test ", "\tsynthetic_test", "Synthetic_Test", "synthetic_test\n"):
        eid = gate.request("lead_outbound", f"syn-{ch.strip()}", beat=1)
        leg.authorize(eid, "syn", "tok")
        cand = dict(_consented())
        cand["source"] = {"channel": ch, "source_id": "owner"}
        r = leg.may_release(eid, cand, gate=gate)
        assert r["allow"] is False, (repr(ch), r)      # هرگز allow
        assert "synthetic" in r["reason"] or "market_signal" in r["reason"], (repr(ch), r)


if __name__ == "__main__":
    checks = [(n, f) for n, f in sorted(globals().items()) if n.startswith("t_")]
    failed = harness.run(checks)
    print(f"\n{'✅' if not failed else '❌'} test_lead_effect_gate: "
          f"{len(checks) - failed}/{len(checks)}")
    sys.exit(1 if failed else 0)
