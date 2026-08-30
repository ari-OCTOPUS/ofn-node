#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_verdict_outcome.py — بستنِ قوسِ رأیِ مالک → outcomeِ پایدار (Sol T2).

قوسِ شکسته: رأیِ دکمهٔ کارت فقط in-memory می‌نشست (با restart گم). اثبات (unit + wiring):
  (الف) نگاشتِ measurement + هرگز delivered/settled؛ verdict field='measurement'.
  (ب)  value فقط CLAIMِ accepted؛ صفر روی رد/تعویق (بدونِ استنتاجِ درآمد).
  (ج)  idempotent: همان (proposal, رأی) دوباره → recorded=False، یک رویداد.
  (د)  restart-replay: ثبت → close → reopen → پایدار.
  (ه)  wiring flag-off parity: بدونِ OCTOPUS_WIRE_VERDICT_OUTCOME، تپِ دکمه صفر نوشتِ durable.
  (و)  wiring flag-on: تپِ دکمه → رویدادِ measurement در outcomes.db با correlation/leg درست.
  (ز)  ساختاری: verdict_recorder صفر import از effector/ledger/approval/settle.
$0 آفلاین؛ storeهای temp؛ wiring روی opslib.STATE_DIR (مسیرِ واقعیِ helper).
"""
import ast
import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import harness  # noqa: E402
harness.setup("verdict-outcome")

_OPS = harness.SELF_OPS
for _p in (str(_OPS), str(_OPS / "outcomes"), str(_OPS / "spine")):
    if _p not in sys.path:
        sys.path.insert(0, _p)
import opslib                     # noqa: E402
import outcome_store as osx       # noqa: E402
import verdict_recorder as vr     # noqa: E402
import event_spine as esx         # noqa: E402
import live_loop as ll           # noqa: E402


def _tmp():
    try:
        return tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
    except TypeError:
        return tempfile.TemporaryDirectory()


def t_a_measurement_mapping_never_delivered():
    assert vr.event_type_for("approved") == "accepted-measurement"
    assert vr.event_type_for("no") == "rejected"
    assert vr.event_type_for("later") == "deferred"
    assert vr.event_type_for("weird") is None
    with _tmp() as td:
        o = osx.OutcomeStore(path=Path(td) / "o.db")
        try:
            r = vr.record_owner_verdict(o, proposal_id="P1", verdict="approved", value_aud_claimed=800.0)
            assert r["recorded"] and r["event_type"] == "accepted-measurement", r
            ev = o.events(proposal_id="P1")[0]
            assert ev["event_type"] not in ("delivered", "settled", "failed"), ev   # هرگز
            assert ev["verdict"] == "measurement", ev                                # رأی سنجش است
        finally:
            o.close()


def t_b_value_only_on_accepted():
    with _tmp() as td:
        o = osx.OutcomeStore(path=Path(td) / "o.db")
        try:
            a = vr.record_owner_verdict(o, proposal_id="Pa", verdict="approved", value_aud_claimed=500.0)
            n = vr.record_owner_verdict(o, proposal_id="Pn", verdict="rejected", value_aud_claimed=500.0)
            d = vr.record_owner_verdict(o, proposal_id="Pd", verdict="later", value_aud_claimed=500.0)
            assert a["value_aud_claimed"] == 500.0, a
            assert n["value_aud_claimed"] == 0.0 and d["value_aud_claimed"] == 0.0, (n, d)
        finally:
            o.close()


def t_c_idempotent():
    with _tmp() as td:
        o = osx.OutcomeStore(path=Path(td) / "o.db")
        try:
            r1 = vr.record_owner_verdict(o, proposal_id="P2", verdict="approved")
            r2 = vr.record_owner_verdict(o, proposal_id="P2", verdict="approved")
            assert r1["recorded"] is True and r2["recorded"] is False, (r1, r2)
            assert len(o.events(proposal_id="P2")) == 1
        finally:
            o.close()


def t_d_restart_replay():
    with _tmp() as td:
        p = Path(td) / "o.db"
        o = osx.OutcomeStore(path=p)
        vr.record_owner_verdict(o, proposal_id="P3", verdict="rejected")
        o.close()
        o2 = osx.OutcomeStore(path=p)   # reopen = restart
        try:
            evs = o2.events(proposal_id="P3")
            assert evs and evs[0]["event_type"] == "rejected", evs
        finally:
            o2.close()


def t_e_wiring_flag_off_parity():
    os.environ.pop(vr.FLAG, None)
    dbp = opslib.STATE_DIR / "outcomes" / "outcomes.db"
    pre = dbp.exists()
    loop = ll.LiveLoop()
    loop._proposal_cb["tok1"] = {"proposal_id": "PW", "amount": 900.0, "kind": "quote",
                                 "leg_id": "lead", "correlation_id": None, "mission_id": None}
    loop.record_proposal_outcome_by_token("tok1", "ok")
    assert dbp.exists() == pre, "flag خاموش نباید outcomes.db بسازد (parity)"


def t_f_wiring_flag_on_durable():
    os.environ[vr.FLAG] = "1"
    try:
        loop = ll.LiveLoop()
        loop._proposal_cb["tok2"] = {"proposal_id": "PON", "amount": 700.0, "kind": "quote",
                                     "leg_id": "lead", "correlation_id": "corr-x", "mission_id": "m1"}
        loop.record_proposal_outcome_by_token("tok2", "ok")
        dbp = opslib.STATE_DIR / "outcomes" / "outcomes.db"
        assert dbp.exists(), "flag روشن باید outcomes.db بسازد"
        o = osx.OutcomeStore(path=dbp)
        try:
            evs = o.events(proposal_id="PON")
            assert evs and evs[0]["event_type"] == "accepted-measurement", evs
            assert evs[0]["correlation_id"] == "corr-x" and evs[0]["leg_id"] == "lead", evs[0]
            assert evs[0]["verdict"] == "measurement", evs[0]   # هرگز settled/delivered
        finally:
            o.close()
    finally:
        os.environ.pop(vr.FLAG, None)


def t_h_spine_second_domain_proposal():
    """Sol-T4: با SPINE روشن، رأی به دامنهٔ دومِ spine (proposal) هم dual-write می‌شود — نه فقط lead."""
    os.environ[vr.FLAG] = "1"
    os.environ[esx.FLAG] = "1"
    try:
        loop = ll.LiveLoop()
        loop._proposal_cb["tokS"] = {"proposal_id": "PSPINE", "amount": 300.0, "kind": "quote",
                                     "leg_id": "lead", "correlation_id": "corr-s", "mission_id": "mS"}
        loop.record_proposal_outcome_by_token("tokS", "ok")
        sp = opslib.STATE_DIR / "spine" / "spine.db"
        assert sp.exists(), "flag روشن باید spine.db بسازد"
        s = esx.EventSpine(path=sp)
        try:
            evs = s.events(correlation_id="corr-s")
            assert evs and evs[0]["domain"] == "proposal", evs   # دامنهٔ دوم (نه lead)
            assert evs[0]["event_type"] == "accepted-measurement", evs
            assert evs[0]["producer"] == "owner_verdict", evs[0]
        finally:
            s.close()
    finally:
        os.environ.pop(vr.FLAG, None)
        os.environ.pop(esx.FLAG, None)


def t_g_structural_no_effector():
    src = (_OPS / "outcomes" / "verdict_recorder.py").read_text("utf-8")
    tree = ast.parse(src)
    banned = {"effector", "approval_channel", "ledger_core", "budget_gate", "tg_api"}
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for a in node.names:
                assert a.name.split(".")[0] not in banned, a.name
        elif isinstance(node, ast.ImportFrom):
            assert (node.module or "").split(".")[0] not in banned, node.module
        elif isinstance(node, ast.Attribute):
            assert node.attr not in {"settle", "EffectorGate", "mark_paid", "send_message"}, node.attr


if __name__ == "__main__":
    checks = [(n, f) for n, f in sorted(globals().items()) if n.startswith("t_")]
    failed = harness.run(checks)
    print(f"\n{'OK' if not failed else 'FAIL'} test_verdict_outcome: "
          f"{len(checks) - failed}/{len(checks)}")
    sys.exit(1 if failed else 0)
