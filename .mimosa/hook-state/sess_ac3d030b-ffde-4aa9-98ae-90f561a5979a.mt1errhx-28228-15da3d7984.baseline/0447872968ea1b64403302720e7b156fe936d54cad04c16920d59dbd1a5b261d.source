#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_spine_multidomain.py — LIMITED MULTI-DOMAIN SHADOW coverage of the Event Spine.

Wave1-C: spine از lead-only به سه دامنهٔ اثبات‌شده می‌رسد — با producerِ واقعیِ production:
  lead   → wiring._record_lead_decisions (decided→delivered، از قبل؛ این‌جا re-verified)
  doctor → self_knowledge.run (نسخهٔ نوی فهم → outcome-recorded)
  ziman  → ZimanLeg.emit_proposal (propose-only → proposal-issued)
قیودِ اثبات‌شده: سه callerِ واقعی به spine می‌رسند · suppress تکرار · زنجیرهٔ correlation
پایدار (proposal-issued و owner-verdict-recorded روی همان prop_<pid>) · سازگاریِ
schema-version/replay (نام‌های قدیمی + canonical کنارِ هم) · flag-off = no-op parity ·
reopen + replayِ قطعی · غیابِ PII/متنِ خام · شکستِ spine مسیرِ propose-only را نمی‌کشد ·
صفر شبکه/پول/اثرِ بیرونی (ast). $0 آفلاین؛ state ایزوله (harness)؛ LLM دکتر mock (بدونِ socket).
"""
import ast
import json
import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import harness  # noqa: E402
ENV = harness.setup("spine-multidomain")

_OPS = Path(__file__).resolve().parents[1]          # کدِ زیرِ تست = همین tree
for _p in (str(_OPS), str(_OPS / "budget"), str(_OPS / "spine"), str(_OPS / "outcomes"),
           str(_OPS / "legs"), str(_OPS / "doctor"), str(_OPS / "memory")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import opslib                    # noqa: E402
import taxonomy as tax           # noqa: E402
import event_spine as esx        # noqa: E402
import spine_adapters as sad     # noqa: E402
import self_knowledge as sk      # noqa: E402
import wiring                    # noqa: E402
from ziman_leg import ZimanLeg   # noqa: E402
from leg import Proposal         # noqa: E402

_SPINE_DB = opslib.STATE_DIR / "spine" / "spine.db"

STRATA = {"description": ("Remedial works to common property including rendering and "
                          "repainting of external facade to residential flat building "
                          "of 24 units."),
          "address": "12 Wattle Crescent, Pyrmont NSW 2009",
          "cost_of_development": 820000, "lat": -33.87, "lng": 151.195,
          "applicant": "Pyrmont Owners Corp", "expected_aud": 8000}


class _Flags:
    """context manager: ست/برگرداندنِ envهای flag — نشتِ صفر بینِ تست‌ها."""
    def __init__(self, **flags):
        self.flags = flags
        self.prev = {}

    def __enter__(self):
        for k, v in self.flags.items():
            self.prev[k] = os.environ.get(k)
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
        return self

    def __exit__(self, *a):
        for k, p in self.prev.items():
            if p is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = p


def _events(**kw):
    s = esx.EventSpine(path=_SPINE_DB)
    try:
        return s.events(**kw)
    finally:
        s.close()


def _metrics():
    s = esx.EventSpine(path=_SPINE_DB)
    try:
        return s.metrics()
    finally:
        s.close()


def _clear_doctor():
    import shutil
    shutil.rmtree(opslib.STATE_DIR / "doctor", ignore_errors=True)


def _mock_llm_off():
    """LLM دکتر را ساختاراً خاموش کن (هیچ socket حتی به localhost) → مسیرِ heuristic."""
    prev = sk._ask_llm
    sk._ask_llm = lambda p, s, max_tokens=700: (None, "mocked-off")
    return prev


def _ziman_leg():
    return ZimanLeg(organ_table={"ZIMAN": {"floor": 1}}, capacity_ceiling=30)


def t_a_taxonomy_canonical_additive_compat():
    """۵ نامِ canonical در taxonomy معتبرند و نام‌های قدیمی دست‌نخورده می‌مانند (compat)."""
    for et in sad.CANONICAL_EVENTS:
        assert tax.is_event_type(et), f"canonical {et!r} باید معتبر باشد"
    for legacy in ("delivered", "decided", "accepted-measurement", "rejected",
                   "deferred", "failed", "reviewed", "verified", "settled"):
        assert tax.is_event_type(legacy), f"legacy {legacy!r} باید معتبر بماند"
    assert tax.is_event_type("nope") is False


def t_b_three_production_callers_reach_spine():
    """سه callerِ واقعیِ production (lead/doctor/ziman) با flag روشن به spine می‌رسند."""
    with _Flags(OCTOPUS_WIRE_SPINE="1", OCTOPUS_WIRE_LEAD_OUTCOME="1"):
        # (۱) lead — همان producerِ beat (decided→delivered؛ LEG-07 از قبل، این‌جا re-verified)
        out = wiring._record_lead_decisions([(dict(STRATA), "SPM-001")])
        assert out["recorded"] == 1 and out.get("spine_events") == 2, out
        lead_evs = _events(correlation_id="lead_SPM-001")
        assert {e["event_type"] for e in lead_evs} == {"decided", "delivered"}, lead_evs
        assert all(e["domain"] == "lead" for e in lead_evs)
        # (۲) doctor — نسخهٔ نوی فهم → outcome-recorded (domain=doctor)
        _clear_doctor()
        prev_ask = _mock_llm_off()
        try:
            rec = sk.run(persist=True)
        finally:
            sk._ask_llm = prev_ask
        assert rec["version"] == 1 and rec["source"] == "heuristic", rec
        dev = _events(domain="doctor")
        assert len(dev) == 1 and dev[0]["event_type"] == "outcome-recorded", dev
        assert dev[0]["correlation_id"] == "selfknow_" + rec["snapshot_hash"], dev[0]
        assert dev[0]["producer"] == "doctor_self_knowledge" and dev[0]["trust"] == "ADVISORY"
        # (۳) ziman — inventory_report (propose-only) → proposal-issued (domain=ziman)
        leg = _ziman_leg()
        p = leg.inventory_report()
        assert isinstance(p, Proposal), p
        zev = _events(domain="ziman")
        assert len(zev) == 1 and zev[0]["event_type"] == "proposal-issued", zev
        assert zev[0]["subject"] == p.proposal_id and zev[0]["trust"] == "ADVISORY", zev[0]
        # جمع: دستِ‌کم سه دامنهٔ متمایز در SoT
        doms = set(_metrics()["by_domain"])
        assert {"lead", "doctor", "ziman"} <= doms, doms


def t_c_duplicate_event_suppression():
    """تکرارِ همان رویداد (adapter و producer) → suppressed؛ شمارِ spine ثابت می‌ماند."""
    with _Flags(OCTOPUS_WIRE_SPINE="1"):
        r1 = sad.proposal_issued(proposal_id="P-dup1", domain="ziman", leg_id="ziman-gallery")
        r2 = sad.proposal_issued(proposal_id="P-dup1", domain="ziman", leg_id="ziman-gallery")
        assert r1["published"] is True and r2["published"] is False, (r1, r2)
        assert r2["reason"] == "duplicate", r2
        # producerِ doctor: چرخهٔ cached (بدونِ تغییرِ فهم) رویدادِ نو نمی‌سازد
        n_before = len(_events(domain="doctor"))
        prev_ask = _mock_llm_off()
        try:
            rec = sk.run(persist=True)
        finally:
            sk._ask_llm = prev_ask
        assert rec["source"] == "cached:no-change", rec
        assert len(_events(domain="doctor")) == n_before, "cached نباید رویدادِ نو بسازد"


def t_d_stable_correlation_chain():
    """proposal-issued و owner-verdict-recorded روی همان prop_<pid> = یک زنجیرهٔ correlation."""
    with _Flags(OCTOPUS_WIRE_SPINE="1"):
        pid = "P-chain1"
        r1 = sad.proposal_issued(proposal_id=pid, domain="ziman", leg_id="ziman-gallery",
                                 kind="draft_content")
        r2 = sad.owner_verdict_recorded(proposal_id=pid, verdict_event="accepted-measurement",
                                        leg_id="ziman-gallery")
        assert r1["published"] and r2["published"], (r1, r2)
        chain = _events(correlation_id="prop_" + pid)
        assert [e["event_type"] for e in chain] == ["proposal-issued", "owner-verdict-recorded"], chain
        assert all(e["correlation_id"] == "prop_" + pid for e in chain)
        v = chain[1]
        assert v["trust"] == "OWNER_CONFIRMED" and v["domain"] == "proposal", v
        assert json.loads(v["payload_json"])["measurement_only"] is True, v
        # رأیِ غیرِ measurement ساختاراً رد می‌شود (هرگز delivered/settled از رأی)
        bad = sad.owner_verdict_recorded(proposal_id=pid, verdict_event="delivered")
        assert bad["published"] is False and "non-measurement" in bad["reason"], bad


def t_e_flag_off_noop_parity():
    """flag خاموش → صفر I/O: هیچ spine.db؛ adapter=no-op؛ ziman/doctor رفتارِ قبلی."""
    with tempfile.TemporaryDirectory() as td:
        prev_state = opslib.STATE_DIR
        opslib.STATE_DIR = Path(td)          # sandboxِ تازه — هر ساختِ db قابلِ دیدن
        try:
            with _Flags(OCTOPUS_WIRE_SPINE=None):
                r = sad.proposal_issued(proposal_id="P-off", domain="ziman")
                assert r == {"published": False, "reason": "flag-off"}, r
                leg = _ziman_leg()
                p = leg.emit_proposal("inventory_report", {"draft_only": True})
                assert isinstance(p, Proposal) and p.leg_id == "ziman-gallery", p
                _clear_doctor()
                prev_ask = _mock_llm_off()
                try:
                    rec = sk.run(persist=True)
                finally:
                    sk._ask_llm = prev_ask
                assert rec["version"] == 1 and rec["understanding"], rec
                assert not (Path(td) / "spine").exists(), "flag خاموش نباید spine بسازد"
        finally:
            opslib.STATE_DIR = prev_state
            _clear_doctor()                  # حالتِ دکترِ sandboxِ اصلی دست‌نخورده بماند


def t_f_reopen_and_deterministic_replay():
    """write → close → reopen → replayِ قطعی؛ زنجیرهٔ canonical با mission_id مشترک."""
    with tempfile.TemporaryDirectory() as td:
        db = Path(td) / "spine.db"
        with _Flags(OCTOPUS_WIRE_SPINE="1"):
            s = esx.EventSpine(path=db)
            try:
                assert sad.mission_created(mission_id="MIS-R1", domain="mission",
                                           correlation_id="tr-r1", spine=s)["published"]
                assert sad.decision_recorded(receipt_id="dr_r1", domain="lead",
                                             correlation_id="tr-r1", mission_id="MIS-R1",
                                             effect_class="E1", spine=s)["published"]
                assert sad.outcome_recorded(domain="lead", correlation_id="tr-r1",
                                            subject="o1", mission_id="MIS-R1",
                                            spine=s)["published"]
                # سازگاری: نامِ قدیمی کنارِ canonical در همان store/schema
                assert s.publish({"event_type": "decided", "domain": "lead",
                                  "correlation_id": "tr-r1", "mission_id": "MIS-R1",
                                  "idempotency_key": "legacy-r1"})
                first = s.replay_mission("MIS-R1")
            finally:
                s.close()
        s2 = esx.EventSpine(path=db)         # reopen (writer/store)
        try:
            again = s2.replay_mission("MIS-R1")
            assert again == first and again["n_events"] == 4, (first, again)
            assert again["correlation_ids"] == ["tr-r1"]
            assert {t["type"] for t in again["timeline"]} == {
                "mission-created", "decision-recorded", "outcome-recorded", "decided"}
            for e in s2.events(mission_id="MIS-R1"):     # schema-version compat
                assert e["schema_version"] == esx.SCHEMA_VERSION == 1, e
        finally:
            s2.close()


def t_g_pii_and_raw_text_absent():
    """متنِ خام/PII هرگز واردِ spine نمی‌شود — صافیِ ساختاریِ آداپتور + hookهای producer."""
    with _Flags(OCTOPUS_WIRE_SPINE="1"):
        r = sad.proposal_issued(
            proposal_id="P-pii1", domain="ziman", leg_id="ziman-gallery",
            payload={"description": "raw lead body should never land",
                     "customer_email": "x@example.com", "caption_text": "long caption",
                     "notes": "secret-ish", "blob": "A" * 500,
                     "units": 3, "ok_short": "id-77"})
        assert r["published"] is True, r
        ev = _events(correlation_id="prop_P-pii1")[0]
        pj = ev["payload_json"]
        for marker in ("raw lead body", "example.com", "long caption", "secret-ish", "AAAA"):
            assert marker not in pj, f"{marker!r} نباید در spine باشد: {pj}"
        assert json.loads(pj).get("units") == 3 and json.loads(pj).get("ok_short") == "id-77"
        # producerهای واقعی: رویدادهای ziman/doctor فقط شناسه/عدد — نه متنِ خامِ vault/فهم
        for e in _events(domain="ziman") + _events(domain="doctor"):
            payload = json.loads(e["payload_json"])
            for k, v in payload.items():
                assert not isinstance(v, (list, dict)), (k, v)
                assert not (isinstance(v, str) and len(v) > 80), (k, v)
            assert "focus" not in payload and "description" not in payload, payload
        # رویدادِ lead (از beat): آدرس/شرحِ خامِ لید در payload نیست
        for e in _events(correlation_id="lead_SPM-001"):
            assert "Wattle" not in e["payload_json"] and "Remedial" not in e["payload_json"], e


def t_h_spine_failure_does_not_break_propose_flow():
    """شکستِ spine (raise) → proposal/فهم همچنان تولید می‌شود (fail-soft در hookها)."""
    def _boom(**kw):
        raise RuntimeError("simulated spine failure")

    with _Flags(OCTOPUS_WIRE_SPINE="1"):
        prev_pi, prev_or = sad.proposal_issued, sad.outcome_recorded
        sad.proposal_issued = _boom
        sad.outcome_recorded = _boom
        try:
            leg = _ziman_leg()
            p = leg.emit_proposal("inventory_report", {"draft_only": True})
            assert isinstance(p, Proposal), "شکستِ spine نباید proposal را بکشد"
            _clear_doctor()
            prev_ask = _mock_llm_off()
            try:
                rec = sk.run(persist=True)
            finally:
                sk._ask_llm = prev_ask
            assert rec["version"] == 1, "شکستِ spine نباید حلقهٔ دکتر را بکشد"
        finally:
            sad.proposal_issued, sad.outcome_recorded = prev_pi, prev_or
            _clear_doctor()
        # شکستِ لایهٔ پایین (dual_write) → emit_canonical فقط reason برمی‌گرداند، raise نه
        prev_dw = esx.dual_write
        esx.dual_write = lambda *a, **k: (_ for _ in ()).throw(RuntimeError("db down"))
        try:
            r = sad.emit_canonical(event="outcome-recorded", domain="doctor",
                                   correlation_id="c-fail")
            assert r["published"] is False and r["reason"].startswith("failsoft:"), r
        finally:
            esx.dual_write = prev_dw


def t_i_zero_external_effect_structural():
    """ast: آداپتور صفر شبکه/پول/effector؛ hookهای producer پشتِ try/except و lazy import."""
    forbidden_imports = {"requests", "socket", "urllib", "http", "telegram", "tg_api",
                         "approval_channel", "effector", "mission_runner", "organism", "wiring"}
    forbidden_names = {"EffectorGate", "settle", "sendMessage", "send_message", "mark_paid",
                       "pay", "self_apply"}
    src = (_OPS / "spine" / "spine_adapters.py").read_text("utf-8")
    tree = ast.parse(src)
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for a in node.names:
                assert a.name.split(".")[0] not in forbidden_imports, a.name
        elif isinstance(node, ast.ImportFrom):
            assert (node.module or "").split(".")[0] not in forbidden_imports, node.module
        elif isinstance(node, ast.Name):
            assert node.id not in forbidden_names, node.id
        elif isinstance(node, ast.Attribute):
            assert node.attr not in forbidden_names, node.attr
    # gating از مرجعِ واحد: آداپتور flag را از event_spine می‌خواند — نه envِ مستقیم، نه fork
    assert "event_spine.flag_on()" in src, "flag باید delegate شود"
    assert "os.environ" not in src, "آداپتور نباید env را مستقیم بخواند (ضدِ fork)"
    # hookهای producer واقعاً سیم شده‌اند (reachability ساختاری) و fail-soft‌اند
    zsrc = (_OPS / "legs" / "ziman_leg.py").read_text("utf-8")
    dsrc = (_OPS / "doctor" / "self_knowledge.py").read_text("utf-8")
    assert "spine_adapters.proposal_issued" in zsrc and "except Exception" in zsrc
    assert "spine_adapters.outcome_recorded" in dsrc and "_spine_outcome(rec)" in dsrc


if __name__ == "__main__":
    checks = [(n, f) for n, f in sorted(globals().items()) if n.startswith("t_")]
    failed = harness.run(checks)
    print(f"\n{'OK' if not failed else 'FAIL'} test_spine_multidomain: "
          f"{len(checks) - failed}/{len(checks)}")
    sys.exit(1 if failed else 0)
