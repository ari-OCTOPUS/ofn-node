#!/usr/bin/env python3
"""تستِ رفتاریِ P-W2: آورانِ واقعی — sensory_bus → school_bridge در حلقهٔ زنده.

گپِ audit: sensory_bus و school_bridge فقط در اسکریپتِ ingest_raw صدا می‌شدند نه
حلقهٔ زنده → «کلاس درس» از جریانِ زندهٔ سیستم یاد نمی‌گرفت. حالا در حلقهٔ زنده
سیم‌کشی شد (هر N beat، پشتِ flag).

این تست اثبات می‌کند:
  (الف) afferent در حلقه → mean_awareness تغییر می‌کند + afferent event روی bus.
  (ب) PII هرگز واردِ school نمی‌شود — حتی اگر snapshot حاوی PII باشد، classifier
      آن را رد می‌کند (afferent=False → learn_from نادیده می‌گیرد).
  (ج) flag خاموش → no-op (None).
  (د) snapshot بدونِ دادهٔ مفید → None (هیچ آورانِ ساختگی).
  (هـ) organism.py سیم‌کشی واقعی دارد (structural).
$0 آفلاین، stdlib-only.
"""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import harness  # noqa: E402
ENV = harness.setup("afferent-path-w2")

_OPS = (harness.REAL_VAULT / r"_ops")
for _p in [str(_OPS), str(_OPS / "neural"), str(_OPS / "afferent"), str(_OPS / "budget")]:
    if _p not in sys.path:
        sys.path.insert(0, _p)
_SM = (harness.REAL_VAULT / r"07 - Knowledge\school-memory")
if str(_SM) not in sys.path:
    sys.path.insert(0, str(_SM))

import wiring  # noqa: E402
from sensory_bus import SensoryBus, Observation, AfferentEvent  # noqa: E402
from school_bridge import SchoolBridge  # noqa: E402
from live_loop import LiveLoop, _InMemoryBus  # noqa: E402

ORGANISM_SRC = (_OPS / "organism.py").read_text("utf-8")


def _real_sensory_bus():
    return SensoryBus()


def _real_bridge():
    return SchoolBridge(state_path=str(Path(ENV["root"]) / "aw-w2.json"))


def _snapshot_with_activity():
    """یک snapshotِ شبیه‌سازی‌شده با فعالیت (منبعِ observation)."""
    return {"per_organ_alltime_musd": {"PROJECT_F": 100, "ARCHITECT_SYS": 50},
            "suspect_zero_total": 2,
            "month": {"musd": 1500, "aud": 2.4}}


# ════════════════════════════════════════════════════════════════════════════════
# (الف) afferent در حلقه → mean_awareness تغییر + bus event
# ════════════════════════════════════════════════════════════════════════════════

def t_afferent_changes_awareness():
    """afferent_beat با snapshotِ فعال → mean_awareness افزایش می‌یابد."""
    os.environ["OCTOPUS_WIRE_SCHOOL"] = "1"
    sb = _real_sensory_bus()
    bridge = _real_bridge()
    mean_before = bridge.mean_awareness()
    snap = _snapshot_with_activity()
    wiring._EPOCH_STATE.clear()   # epoch-gate: هر تست پنجرهٔ تازه
    result = wiring.afferent_beat(sb, school_bridge=bridge, snap=snap, beat=1440)
    os.environ.pop("OCTOPUS_WIRE_SCHOOL")
    assert result is not None, "afferent_beat باید نتیجه بدهد (flag on + beat مضرب + داده)"
    school = result["school_report"]
    assert school is not None, "school_report باید پر باشد"
    assert school["taught_signals"] > 0, "باید چیزی یاد گرفته باشد"
    assert bridge.mean_awareness() > mean_before, \
        f"mean_awareness باید افزایش یابد: {mean_before} → {bridge.mean_awareness()}"


def t_afferent_status_published_to_bus():
    """afferent_status از afferent_beat → advisory signal در LiveLoop.
    advisory signals در _advisory_signals ثبت می‌شوند (نه bus.events، چون advisory
    نباید ردیفِ ledger بسازند)."""
    os.environ["OCTOPUS_WIRE_SCHOOL"] = "1"
    sb = _real_sensory_bus()
    bridge = _real_bridge()
    snap = _snapshot_with_activity()
    # afferent_beat → status
    wiring._EPOCH_STATE.clear()   # epoch-gate: هر تست پنجرهٔ تازه
    result = wiring.afferent_beat(sb, school_bridge=bridge, snap=snap, beat=1440)
    status = result.get("sensory_status")
    os.environ.pop("OCTOPUS_WIRE_SCHOOL")
    # حالا status را به advisory publish کن (شبیه‌سازیِ organism tick)
    bus = _InMemoryBus()
    ll = LiveLoop(bus=bus)
    n = wiring.publish_tick_signals(ll, afferent_status=status)
    assert n == 1, "باید یک AFFERENT advisory publish شود"
    assert len(ll.advisory_signals) == 1
    assert ll.advisory_signals[0]["type"] == "AFFERENT"


def t_afferent_observation_count():
    """با snapshotِ فعال → چند observation ساخته می‌شود (organs + suspect + month)."""
    os.environ["OCTOPUS_WIRE_SCHOOL"] = "1"
    sb = _real_sensory_bus()
    wiring._EPOCH_STATE.clear()   # epoch-gate: هر تست پنجرهٔ تازه
    result = wiring.afferent_beat(sb, school_bridge=_real_bridge(),
                                   snap=_snapshot_with_activity(), beat=1440)
    os.environ.pop("OCTOPUS_WIRE_SCHOOL")
    assert result["n_observations"] >= 1, "باید حداقل یک observation باشد"


# ════════════════════════════════════════════════════════════════════════════════
# (ب) PII هرگز واردِ school نمی‌شود
# ════════════════════════════════════════════════════════════════════════════════

def t_pii_observation_rejected_by_classifier():
    """اگر observation حاوی PII باشد، classifier آن را رد می‌کند (afferent=False)."""
    from sensory_bus import classify
    obs = Observation(source="test", obs_type="status",
                      label="invoice# INV-12345 abn: 12345678901")
    ev = classify(obs)
    assert ev.afferent is False, "PII باید رد شود (afferent=False)"
    assert ev.topic_ids == [], "PII-رد نباید topic بگیرد"


def t_pii_never_learned_by_school():
    """اگر فقط PII observation باشد، school چیزی یاد نمی‌گیرد (taught=0)."""
    os.environ["OCTOPUS_WIRE_SCHOOL"] = "1"
    sb = _real_sensory_bus()
    bridge = _real_bridge()
    # مستقیماً یک PII observation ingest کن
    obs = Observation(source="test", obs_type="status", label="credit card 4532-xxxx")
    ev = sb.ingest(obs)
    assert ev.afferent is False
    # school از این event یاد نگیرد
    report = bridge.learn_from([ev], persist=False)
    os.environ.pop("OCTOPUS_WIRE_SCHOOL")
    assert report["taught_signals"] == 0, "PII نباید یاد گرفته شود"


def t_snapshot_observations_are_abstract():
    """_observations_from_snapshot فقط لیبلِ انتزاعی تولید می‌کند — هیچ PII."""
    obs = wiring._observations_from_snapshot(_snapshot_with_activity())
    assert len(obs) >= 1
    for o in obs:
        # هر لیبل باید کاملاً انتزاعی باشد — هیچ نام/مقدارِ خام
        blob = str(o.label).lower()
        for pii in ("invoice", "abn", "credit card", "name", "email", "phone"):
            assert pii not in blob, f"PII در observation: {pii}"


def test_no_raw_data_in_events():
    """AfferentEvent فقط metadata دارد — هیچ رکوردِ خام."""
    os.environ["OCTOPUS_WIRE_SCHOOL"] = "1"
    sb = _real_sensory_bus()
    wiring._EPOCH_STATE.clear()   # epoch-gate: هر تست پنجرهٔ تازه
    result = wiring.afferent_beat(sb, school_bridge=_real_bridge(),
                                   snap=_snapshot_with_activity(), beat=1440)
    os.environ.pop("OCTOPUS_WIRE_SCHOOL")
    # eventها فقط topic_ids/source/intensity دارند، نه رکوردِ خام
    for ev in sb._events:
        assert not hasattr(ev, "raw_data"), "AfferentEvent نباید raw_data داشته باشد"


# ════════════════════════════════════════════════════════════════════════════════
# (ج) flag خاموش → no-op
# ════════════════════════════════════════════════════════════════════════════════

def t_flag_off_is_noop():
    """flag خاموش → afferent_beat None برمی‌گرداند (no-op)."""
    os.environ.pop("OCTOPUS_WIRE_SCHOOL", None)
    sb = _real_sensory_bus()
    wiring._EPOCH_STATE.clear()   # epoch-gate: هر تست پنجرهٔ تازه
    result = wiring.afferent_beat(sb, school_bridge=_real_bridge(),
                                   snap=_snapshot_with_activity(), beat=1440)
    assert result is None, "flag خاموز باید no-op باشد"


def t_non_multiple_beat_is_noop():
    """beat غیرِ مضربِ N → no-op (حتی با flag روشن)."""
    os.environ["OCTOPUS_WIRE_SCHOOL"] = "1"
    sb = _real_sensory_bus()
    wiring._EPOCH_STATE.clear()   # epoch-gate: هر تست پنجرهٔ تازه
    result = wiring.afferent_beat(sb, school_bridge=_real_bridge(),
                                   snap=_snapshot_with_activity(), beat=100)
    os.environ.pop("OCTOPUS_WIRE_SCHOOL")
    assert result is None, "beat غیرِ مضربِ N نباید fire شود"


def t_zero_beat_is_noop():
    """beat=0 → no-op."""
    os.environ["OCTOPUS_WIRE_SCHOOL"] = "1"
    sb = _real_sensory_bus()
    wiring._EPOCH_STATE.clear()   # epoch-gate: هر تست پنجرهٔ تازه
    result = wiring.afferent_beat(sb, beat=0)
    os.environ.pop("OCTOPUS_WIRE_SCHOOL")
    assert result is None


# ════════════════════════════════════════════════════════════════════════════════
# (د) snapshot بدونِ داده → None (هیچ آورانِ ساختگی)
# ════════════════════════════════════════════════════════════════════════════════

def t_empty_snapshot_no_school():
    """snapshotِ خالی → ۰ observation → school_report=None (هیچ چیزِ ساختگی)."""
    os.environ["OCTOPUS_WIRE_SCHOOL"] = "1"
    sb = _real_sensory_bus()
    wiring._EPOCH_STATE.clear()   # epoch-gate: هر تست پنجرهٔ تازه
    result = wiring.afferent_beat(sb, school_bridge=_real_bridge(),
                                   snap={}, beat=1440)
    os.environ.pop("OCTOPUS_WIRE_SCHOOL")
    assert result is not None   # همچنان status برمی‌گرداند
    assert result["n_observations"] == 0
    assert result["school_report"] is None, "بدونِ observation نباید چیزی یاد بگیرد"


def t_no_sensory_bus_noop():
    """بدونِ SensoryBus → afferent_beat None."""
    os.environ["OCTOPUS_WIRE_SCHOOL"] = "1"
    wiring._EPOCH_STATE.clear()   # epoch-gate: هر تست پنجرهٔ تازه
    result = wiring.afferent_beat(None, snap=_snapshot_with_activity(), beat=1440)
    os.environ.pop("OCTOPUS_WIRE_SCHOOL")
    assert result is None


# ════════════════════════════════════════════════════════════════════════════════
# (هـ) kill-switch + organism سیم‌کشی واقعی (structural)
# ════════════════════════════════════════════════════════════════════════════════

def t_killswitch_blocks_afferent():
    """STOP فعال → afferent_beat None."""
    import opslib
    os.environ["OCTOPUS_WIRE_SCHOOL"] = "1"
    sb = _real_sensory_bus()
    opslib.STOP_ORGANISM.write_text("kill", "utf-8")
    try:
        wiring._EPOCH_STATE.clear()   # epoch-gate: هر تست پنجرهٔ تازه
        result = wiring.afferent_beat(sb, snap=_snapshot_with_activity(), beat=1440)
    finally:
        try:
            opslib.STOP_ORGANISM.unlink()
        except OSError:
            pass
    os.environ.pop("OCTOPUS_WIRE_SCHOOL")
    assert result is None


def t_organism_builds_sensory_bus():
    """organism باید SensoryBus را در boot بسازد وقتی flag روشن است."""
    assert "make_sensory_bus" in ORGANISM_SRC, \
        "organism باید make_sensory_bus را در boot صدا بزند"


def t_organism_calls_afferent_beat():
    """tick باید afferent_beat را صدا بزند."""
    assert "afferent_beat" in ORGANISM_SRC, "tick باید afferent_beat را صدا بزند"


def t_organism_feeds_afferent_to_publish():
    """afferent_status باید به publish_tick_signals پاس داده شود (نه None همیشگی)."""
    idx = ORGANISM_SRC.find("publish_tick_signals(")
    assert idx > 0
    snippet = ORGANISM_SRC[idx:idx + 250]
    assert "_afferent_status" in snippet, \
        "publish_tick_signals باید afferent_status را بگیرد (نه None همیشگی)"


def t_organism_afferent_gated_on_protective():
    """afferent باید زیرِ گاردِ not _protective_skip باشد."""
    idx = ORGANISM_SRC.find("afferent_beat(")
    assert idx > 0
    before = ORGANISM_SRC[max(0, idx - 400):idx]
    assert "_protective_skip" in before


if __name__ == "__main__":
    failed = harness.run([
        # (الف) afferent → awareness + bus
        ("afferent → mean_awareness افزایش", t_afferent_changes_awareness),
        ("afferent_status → bus event", t_afferent_status_published_to_bus),
        ("afferent observation count", t_afferent_observation_count),
        # (ب) PII هرگز
        ("PII observation رد می‌شود", t_pii_observation_rejected_by_classifier),
        ("PII هرگز یاد گرفته نمی‌شود", t_pii_never_learned_by_school),
        ("observationها انتزاعی‌اند (هیچ PII)", t_snapshot_observations_are_abstract),
        ("AfferentEvent بدونِ raw_data", test_no_raw_data_in_events),
        # (ج) flag خاموش
        ("flag off → no-op", t_flag_off_is_noop),
        ("beat غیرِ مضربِ N → no-op", t_non_multiple_beat_is_noop),
        ("beat=0 → no-op", t_zero_beat_is_noop),
        # (د) snapshot خالی
        ("snapshot خالی → no school", t_empty_snapshot_no_school),
        ("بدونِ SensoryBus → None", t_no_sensory_bus_noop),
        # (هـ) kill-switch + structural
        ("kill-switch → None", t_killswitch_blocks_afferent),
        ("organism make_sensory_bus", t_organism_builds_sensory_bus),
        ("organism afferent_beat در tick", t_organism_calls_afferent_beat),
        ("afferent_status به publish", t_organism_feeds_afferent_to_publish),
        ("afferent روی not _protective_skip", t_organism_afferent_gated_on_protective),
    ])
    sys.exit(1 if failed else 0)
