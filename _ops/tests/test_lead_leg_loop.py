#!/usr/bin/env python3
"""تستِ رفتاریِ P-L1: اتصالِ HLC + حلقهٔ خودمختار به LeadLeg.

گپِ recon (HIGH): پا حلقهٔ خودمختار نداشت؛ آبجکتِ Leg به LegHandle/HLC وصل نبود.
(P-W1 آن را در _leg نگه داشت ولی هنوز رانده نمی‌شد.) حالا پشتِ flagِ نو
OCTOPUS_WIRE_LEAD_TICK در tick سیم‌کشی شد.

این تست اثبات می‌کند:
  (الف) flag روشن → LeadLeg در حلقه HLC می‌زند و ack می‌دهد (hlc رشد می‌کند،
      events_this_beat > 0، leg_clock در pacemaker به‌روز می‌شود).
  (ب) propose-only مطلق: هیچ effector/settle — LegHandle فقط در حافظه بافر می‌کند،
      pacemaker تنها writer دیسک است (single-writer حفظ).
  (ج) flag خاموش → no-op (رفتارِ فعلی، leg_beat None).
  (د) kill-switch: STOP فعال → no-op.
  (هـ) organism.py سیم‌کشی واقعی دارد (structural).
$0 آفلاین، stdlib-only.
"""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import harness  # noqa: E402
ENV = harness.setup("lead-leg-loop")

_OPS = Path(r"F:\backup\_ops")
for _p in [str(_OPS), str(_OPS / "legs"), str(_OPS / "budget")]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

import chrono  # noqa: E402
import wiring  # noqa: E402
from leg import TaskPacket  # noqa: E402
from lead_leg import LeadLeg  # noqa: E402

ORGANISM_SRC = (_OPS / "organism.py").read_text("utf-8")


def _pacemaker_and_leg():
    """یک Pacemaker واقعی (با bus واقعی) + یک LeadLeg واقعی."""
    db = chrono.ChronoDB(ENV["ops"] / "state" / "chrono-l1.db")
    clock = chrono._utc_ms
    pm = chrono.Pacemaker(db=db, clock=clock)
    packet = TaskPacket(
        leg_id="lead-naghshi", organ="LEAD_PAINTING",
        read_allowlist=("03 - Projects/Lead-نقاشی/PROJECT.md",),
        tools=("draft_quote",), budget_aud=5.0)
    leg = LeadLeg(packet, organ_table={"LEAD_PAINTING": 100.0})
    return pm, leg


# ════════════════════════════════════════════════════════════════════════════════
# (الف) flag روشن → HLC می‌زند + ack + leg_clock به‌روز
# ════════════════════════════════════════════════════════════════════════════════

def t_flag_on_hlc_advances():
    """flag روشن → بعد از چند tick، hlcِ LegHandle رشد می‌کند."""
    os.environ["OCTOPUS_WIRE_LEAD_TICK"] = "1"
    try:
        pm, leg = _pacemaker_and_leg()
        r1 = wiring.leg_beat(leg, pacemaker=pm, beat=1)
        hlc1 = tuple(r1["hlc"])
        r2 = wiring.leg_beat(leg, pacemaker=pm, beat=2)
        hlc2 = tuple(r2["hlc"])
        assert hlc2 >= hlc1, f"hlc باید رشد کند: {hlc1} → {hlc2}"
        assert r2["events_this_beat"] >= 1, "events_this_beat باید > 0 باشد"
    finally:
        os.environ.pop("OCTOPUS_WIRE_LEAD_TICK", None)


def t_flag_on_ack_registered():
    """flag روشن → ack ثبت می‌شود (LegHandle در bus موجود، phi-accrual heard)."""
    os.environ["OCTOPUS_WIRE_LEAD_TICK"] = "1"
    try:
        pm, leg = _pacemaker_and_leg()
        wiring.leg_beat(leg, pacemaker=pm, beat=1)
        handle = pm.bus.legs.get("lead-naghshi")
        assert handle is not None, "LegHandle باید ثبت شده باشد"
        assert handle.events_this_beat >= 1
        # phi-accrual باید این leg را شنیده باشد
        assert "lead-naghshi" in pm.bus.phi
    finally:
        os.environ.pop("OCTOPUS_WIRE_LEAD_TICK", None)


def t_flag_on_leg_clock_persisted():
    """flag روشن → بعد از یک pacemaker beat، leg_clock در db نوشته می‌شود
    (single-writer: فقط pacemaker در سد ضربان می‌نویسد، نه leg)."""
    os.environ["OCTOPUS_WIRE_LEAD_TICK"] = "1"
    try:
        pm, leg = _pacemaker_and_leg()
        # leg یک event می‌زند (HLC + ack)
        wiring.leg_beat(leg, pacemaker=pm, beat=1)
        # pacemaker یک beat می‌زند (تنها writer) → leg_clock باید نوشته شود
        pm.beat_once()
        rows = pm.db.q("SELECT leg_id FROM leg_clock WHERE leg_id=?", ("lead-naghshi",))
        assert rows and rows[0][0] == "lead-naghshi", \
            "leg_clock باید در db نوشته شده باشد (توسط pacemaker، single-writer)"
    finally:
        os.environ.pop("OCTOPUS_WIRE_LEAD_TICK", None)


def t_flag_on_propose_only_flag():
    """flag روشن → گزارشِ leg_beat باید propose_only=True داشته باشد."""
    os.environ["OCTOPUS_WIRE_LEAD_TICK"] = "1"
    try:
        pm, leg = _pacemaker_and_leg()
        r = wiring.leg_beat(leg, pacemaker=pm, beat=1)
        assert r.get("propose_only") is True
    finally:
        os.environ.pop("OCTOPUS_WIRE_LEAD_TICK", None)


# ════════════════════════════════════════════════════════════════════════════════
# (ب) propose-only مطلق — هیچ effector/settle
# ════════════════════════════════════════════════════════════════════════════════

def t_no_settle_method_on_leg():
    """Leg نباید متدِ settle/send/pay داشته باشد (propose-only structural)."""
    assert not hasattr(LeadLeg, "settle"), "Leg نباید settle داشته باشد"
    assert not hasattr(LeadLeg, "send"), "Leg نباید send داشته باشد"
    assert not hasattr(LeadLeg, "pay"), "Leg نباید pay داشته باشد"


def t_leg_event_does_not_write_db():
    """leg_handle.event() فقط در حافظه بافر می‌کند، نه در db (single-writer).

    pacemaker تنها writer است. leg_beat نباید خودش چیزی در db بنویسد."""
    os.environ["OCTOPUS_WIRE_LEAD_TICK"] = "1"
    try:
        pm, leg = _pacemaker_and_leg()
        # قبل: leg_clock نباید باشد
        rows_before = pm.db.q("SELECT leg_id FROM leg_clock WHERE leg_id=?",
                              ("lead-naghshi",))
        wiring.leg_beat(leg, pacemaker=pm, beat=1)
        # بعد از leg_beat (بدون beat_onceِ pacemaker): هنوز نباید در db باشد
        rows_after = pm.db.q("SELECT leg_id FROM leg_clock WHERE leg_id=?",
                             ("lead-naghshi",))
        assert len(rows_after) == len(rows_before), \
            "leg_beat نباید در db بنویسد (single-writer = فقط pacemaker)"
    finally:
        os.environ.pop("OCTOPUS_WIRE_LEAD_TICK", None)


def t_leg_can_emit_proposal_only():
    """پا فقط proposal تولید می‌کند (propose-only). emit_proposal کار می‌کند،
    ولی هیچ متدِ effector نیست."""
    pm, leg = _pacemaker_and_leg()
    p = leg.emit_proposal("draft_quote", {"scope": "test"}, hlc=(1, 0))
    assert p.proposal_id and p.leg_id == "lead-naghshi"
    assert len(leg.proposals) == 1


# ════════════════════════════════════════════════════════════════════════════════
# (ج) flag خاموش → no-op
# ════════════════════════════════════════════════════════════════════════════════

def t_flag_off_noop():
    """flag خاموش → leg_beat None برمی‌گرداند (no-op)."""
    os.environ.pop("OCTOPUS_WIRE_LEAD_TICK", None)
    pm, leg = _pacemaker_and_leg()
    r = wiring.leg_beat(leg, pacemaker=pm, beat=1)
    assert r is None, "flag خاموز باید no-op باشد"


def t_flag_off_no_handle_registered():
    """flag خاموش → LegHandle ثبت نمی‌شود (leg در bus نیست)."""
    os.environ.pop("OCTOPUS_WIRE_LEAD_TICK", None)
    pm, leg = _pacemaker_and_leg()
    wiring.leg_beat(leg, pacemaker=pm, beat=1)
    assert "lead-naghshi" not in pm.bus.legs, \
        "flag خاموز نباید LegHandle ثبت کند"


def t_flag_off_in_summary():
    """wire_summary باید wire_leg_tick را نشان دهد (پیش‌فرض خاموز)."""
    os.environ.pop("OCTOPUS_WIRE_LEAD_TICK", None)
    s = wiring.wire_summary()
    assert "wire_leg_tick" in s
    assert s["wire_leg_tick"] is False


# ════════════════════════════════════════════════════════════════════════════════
# (د) kill-switch
# ════════════════════════════════════════════════════════════════════════════════

def t_killswitch_blocks_leg_beat():
    """STOP فعال → leg_beat None."""
    import opslib
    os.environ["OCTOPUS_WIRE_LEAD_TICK"] = "1"
    pm, leg = _pacemaker_and_leg()
    opslib.STOP_ORGANISM.write_text("kill", "utf-8")
    try:
        r = wiring.leg_beat(leg, pacemaker=pm, beat=1)
    finally:
        try:
            opslib.STOP_ORGANISM.unlink()
        except OSError:
            pass
    os.environ.pop("OCTOPUS_WIRE_LEAD_TICK", None)
    assert r is None, "kill-switch باید leg_beat را بلوک کند"


def t_no_leg_or_pacemaker_noop():
    """بدونِ leg یا pacemaker → leg_beat None."""
    os.environ["OCTOPUS_WIRE_LEAD_TICK"] = "1"
    pm, leg = _pacemaker_and_leg()
    try:
        assert wiring.leg_beat(None, pacemaker=pm, beat=1) is None
        assert wiring.leg_beat(leg, pacemaker=None, beat=1) is None
    finally:
        os.environ.pop("OCTOPUS_WIRE_LEAD_TICK", None)


# ════════════════════════════════════════════════════════════════════════════════
# (هـ) organism.py سیم‌کشی واقعی (structural)
# ════════════════════════════════════════════════════════════════════════════════

def t_organism_captures_pacemaker():
    """بوت باید pacemaker را در متغیر نگه دارد (برای HLC/ackِ leg)."""
    assert "_pacemaker = chrono.start_pacemaker_thread(" in ORGANISM_SRC, \
        "بوت باید _pacemaker را نگه دارد"


def t_organism_calls_leg_beat():
    """tick باید leg_beat را صدا بزند."""
    assert "leg_beat" in ORGANISM_SRC, "tick باید leg_beat را صدا بزند"


def t_organism_leg_beat_gated_on_protective():
    """leg_beat باید زیرِ گاردِ not _protective_skip باشد."""
    idx = ORGANISM_SRC.find("leg_beat(")
    assert idx > 0
    before = ORGANISM_SRC[max(0, idx - 500):idx]
    assert "_protective_skip" in before, \
        "leg_beat باید روی not _protective_skip گیت باشد"


def t_organism_leg_beat_alerts_on_error():
    """§۴: بلوکِ leg_beat نباید except بی‌صدا باشد — باید alert."""
    idx = ORGANISM_SRC.find("leg_beat(")
    assert idx > 0
    block = ORGANISM_SRC[idx:idx + 400]
    assert "opslib.alert" in block, "§۴: leg_beat error باید alert شود"


def t_organism_uses_held_leg():
    """leg_beat باید _leg (نگه‌داشته‌شده از P-W1) را استفاده کند، نه ساختنِ جدید."""
    idx = ORGANISM_SRC.find("leg_beat(")
    assert idx > 0
    snippet = ORGANISM_SRC[idx:idx + 200]
    assert "_leg" in snippet, "leg_beat باید از _leg استفاده کند"


if __name__ == "__main__":
    failed = harness.run([
        # (الف) flag on → HLC + ack + leg_clock
        ("flag on → HLC رشد می‌کند", t_flag_on_hlc_advances),
        ("flag on → ack ثبت می‌شود", t_flag_on_ack_registered),
        ("flag on → leg_clock در db (single-writer)", t_flag_on_leg_clock_persisted),
        ("flag on → propose_only=True", t_flag_on_propose_only_flag),
        # (ب) propose-only
        ("Leg متدِ effector ندارد (structural)", t_no_settle_method_on_leg),
        ("leg_beat در db نمی‌نویسد (single-writer)", t_leg_event_does_not_write_db),
        ("پا فقط proposal تولید می‌کند", t_leg_can_emit_proposal_only),
        # (ج) flag off
        ("flag off → no-op", t_flag_off_noop),
        ("flag off → LegHandle ثبت نمی‌شود", t_flag_off_no_handle_registered),
        ("wire_summary wire_leg_tick", t_flag_off_in_summary),
        # (د) kill-switch
        ("kill-switch → None", t_killswitch_blocks_leg_beat),
        ("بدونِ leg/pacemaker → None", t_no_leg_or_pacemaker_noop),
        # (هـ) structural
        ("بوت pacemaker را نگه می‌دارد", t_organism_captures_pacemaker),
        ("tick leg_beat صدا می‌زند", t_organism_calls_leg_beat),
        ("leg_beat روی not _protective_skip", t_organism_leg_beat_gated_on_protective),
        ("leg_beat error alert (§۴)", t_organism_leg_beat_alerts_on_error),
        ("leg_beat از _leg استفاده می‌کند", t_organism_uses_held_leg),
    ])
    sys.exit(1 if failed else 0)
