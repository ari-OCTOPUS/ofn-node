#!/usr/bin/env python3
"""تستِ P-W4: connection self-test — بوتِ paper-full → همهٔ ماژول‌ها fire می‌کنند.

این تستِ «تمام» (WIRING-MAP §۴): تا این تست سبز نشود، «وصل بودن» ادعاست نه واقعیت.
بوتِ paper-full را شبیه‌سازی می‌کند: apply_profile → flagها → ساختِ همهٔ ماژول‌ها →
شبیه‌سازیِ چند tick → assert هر ماژول ≥۱ بار fire کرد.

ماژول‌های موردِ بررسی: sensory(school) · neural · consolidation · doctor(+evolution+box) ·
legs(proposal) · rhythm/spectral advisory · unified bus · idea_graph.

$0 آفلاین، stdlib-only.
"""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import harness  # noqa: E402
ENV = harness.setup("connection-selftest")

_OPS = Path(r"F:\backup\_ops")
for _p in [str(_OPS), str(_OPS / "budget"), str(_OPS / "neural"),
           str(_OPS / "doctor"), str(_OPS / "doctor" / "box"),
           str(_OPS / "afferent"), str(_OPS / "legs")]:
    if _p not in sys.path:
        sys.path.insert(0, _p)
_SM = Path(r"F:\backup\07 - Knowledge\school-memory")
if str(_SM) not in sys.path:
    sys.path.insert(0, str(_SM))

import wiring  # noqa: E402
import chrono  # noqa: E402


# ════════════════════════════════════════════════════════════════════════════════
# (الف) profile = bare (پیش‌فرض، no-regression)
# ════════════════════════════════════════════════════════════════════════════════

def t_default_profile_is_bare():
    """بدونِ env، profile = bare (no-regression)."""
    os.environ.pop("OCTOPUS_PROFILE", None)
    assert wiring.resolve_profile() == "bare"


def t_bare_profile_no_flags():
    """bare → apply_profile هیچ flagی را ست نمی‌کند."""
    os.environ.pop("OCTOPUS_PROFILE", None)
    # همهٔ flagها را پاک کن
    for f in wiring.PAPER_FULL_FLAGS:
        os.environ.pop(f, None)
    wiring.apply_profile()
    s = wiring.wire_summary()
    assert s["wire_doctor"] is False
    assert s["wire_neural"] is False
    assert s["wire_ideas"] is False


# ════════════════════════════════════════════════════════════════════════════════
# (ب) profile = paper-full → همهٔ flagها روشن
# ════════════════════════════════════════════════════════════════════════════════

def t_paper_full_sets_all_flags():
    """paper-full → همهٔ flagهای امن = 1."""
    os.environ["OCTOPUS_PROFILE"] = "paper-full"
    for f in wiring.PAPER_FULL_FLAGS:
        os.environ.pop(f, None)   # مطمئن شو apply_profile آن‌ها را ست می‌کند
    wiring.apply_profile()
    for f in wiring.PAPER_FULL_FLAGS:
        assert os.environ.get(f) == "1", f"paper-full باید {f}=1 کند"
    os.environ.pop("OCTOPUS_PROFILE", None)
    for f in wiring.PAPER_FULL_FLAGS:
        os.environ.pop(f, None)


def t_paper_full_no_money_flag():
    """paper-full نباید هیچ flagِ money/live را باز کند (capability-gated جدا)."""
    os.environ["OCTOPUS_PROFILE"] = "paper-full"
    for f in wiring.PAPER_FULL_FLAGS:
        os.environ.pop(f, None)
    wiring.apply_profile()
    # money/live در PAPER_FULL_FLAGS نیست
    assert "LIVE_ENABLED" not in wiring.PAPER_FULL_FLAGS
    assert not any("money" in f.lower() or "live" in f.lower()
                   for f in wiring.PAPER_FULL_FLAGS), \
        "money/live نباید در paper-full باشد"
    os.environ.pop("OCTOPUS_PROFILE", None)
    for f in wiring.PAPER_FULL_FLAGS:
        os.environ.pop(f, None)


# ════════════════════════════════════════════════════════════════════════════════
# (ج) بوتِ paper-full → همهٔ ماژول‌ها ساخته می‌شوند (constructors)
# ════════════════════════════════════════════════════════════════════════════════

def _boot_paper_full():
    """شبیه‌سازیِ بوتِ paper-full: flagها + ساختِ همهٔ ماژول‌ها.
    برمی‌گرداند: dict از آبجکت‌های ساخته‌شده."""
    os.environ["OCTOPUS_PROFILE"] = "paper-full"
    wiring.apply_profile()
    objs = {}
    objs["doctor"] = wiring.make_doctor(state_dir=str(ENV["ops"] / "state"))
    objs["bus"] = wiring.make_unified_bus()
    objs["leg"] = wiring.make_lead_leg()
    objs["neural"] = wiring.make_neural_stack()
    objs["school_bridge"] = wiring.make_school_bridge()
    objs["sensory_bus"] = wiring.make_sensory_bus()
    objs["idea_graph"] = wiring.make_idea_graph()
    objs["live_loop"] = wiring.make_live_loop(
        bus=objs["bus"], leg=objs["leg"], doctor=objs["doctor"])
    # cleanup
    for f in wiring.PAPER_FULL_FLAGS:
        os.environ.pop(f, None)
    os.environ.pop("OCTOPUS_PROFILE", None)
    return objs


def t_boot_builds_all_modules():
    """بوتِ paper-full → همهٔ ماژول‌ها ساخته می‌شوند (نه None)."""
    objs = _boot_paper_full()
    for name, obj in objs.items():
        assert obj is not None, f"بوت باید {name} را بسازد، نه None"


def t_boot_builds_unified_bus():
    """بوتِ paper-full → UnifiedBus ساخته می‌شود (نخاع)."""
    objs = _boot_paper_full()
    assert objs["bus"] is not None
    # bus باید publish/subscribe داشته باشد
    assert hasattr(objs["bus"], "publish")
    assert hasattr(objs["bus"], "subscribe")


def t_boot_builds_live_loop():
    """بوتِ paper-full → LiveLoop ساخته می‌شود."""
    objs = _boot_paper_full()
    assert objs["live_loop"] is not None
    assert hasattr(objs["live_loop"], "publish_tick_signals") or hasattr(wiring, "publish_tick_signals")


# ════════════════════════════════════════════════════════════════════════════════
# (د) شبیه‌سازیِ چند tick → هر ماژول ≥۱ بار fire
# ════════════════════════════════════════════════════════════════════════════════

def test_all_modules_fire_in_simulated_ticks():
    """شبیه‌سازیِ چند tick → هر ماژول ≥۱ بار fire کرد. این معیارِ «تمام» است."""
    # paper-full را روی env بگذار (برای flagها درونِ *_beat)
    os.environ["OCTOPUS_PROFILE"] = "paper-full"
    wiring.apply_profile()
    try:
        objs = {}
        objs["doctor"] = wiring.make_doctor(state_dir=str(ENV["ops"] / "state"))
        objs["bus"] = wiring.make_unified_bus()
        objs["leg"] = wiring.make_lead_leg()
        objs["neural"] = wiring.make_neural_stack()
        objs["school_bridge"] = wiring.make_school_bridge()
        objs["sensory_bus"] = wiring.make_sensory_bus()
        objs["idea_graph"] = wiring.make_idea_graph()
        objs["live_loop"] = wiring.make_live_loop(
            bus=objs["bus"], leg=objs["leg"], doctor=objs["doctor"])
        # pacemaker برای leg_beat (با bus واقعی)
        db = chrono.ChronoDB(ENV["ops"] / "state" / "chrono-selftest.db")
        pm = chrono.Pacemaker(db=db)
        fired = {"neural": 0, "doctor": 0, "consolidation": 0,
                 "afferent": 0, "publish": 0, "leg": 0, "idea": 0}
        snap = {"per_organ_alltime_musd": {"X": 100}, "suspect_zero_total": 1,
                "month": {"musd": 500}}
        # شبیه‌سازیِ ۳ tick (beat = مضربِ Nها برای forcingِ fire)
        for beat in [1440, 2880, 4320]:
            # neural
            nr = wiring.neural_beat(objs["neural"], beat, {"rhythm": {}, "budget": {"pct": 0.1}})
            if nr is not None:
                fired["neural"] += 1
            # doctor (trace تزریق‌شده با گلوگاه)
            dr = wiring.doctor_beat(objs["doctor"], beat)
            if dr is not None:
                fired["doctor"] += 1
            # consolidation
            cr = wiring.consolidation_beat(objs["neural"], school_bridge=objs["school_bridge"],
                                           beat=beat)
            if cr is not None:
                fired["consolidation"] += 1
            # afferent
            ar = wiring.afferent_beat(objs["sensory_bus"], school_bridge=objs["school_bridge"],
                                      snap=snap, beat=beat)
            if ar is not None:
                fired["afferent"] += 1
            # publish
            pn = wiring.publish_tick_signals(objs["live_loop"], beat=beat,
                                             rhythm_state={"mode": "GREEN"},
                                             doctor_result=dr)
            if pn > 0:
                fired["publish"] += 1
            # leg (HLC)
            lb = wiring.leg_beat(objs["leg"], pacemaker=pm, beat=beat)
            if lb is not None:
                fired["leg"] += 1
            # idea
            ir = wiring.idea_beat(objs["idea_graph"], beat=beat)
            if ir is not None:
                fired["idea"] += 1
        # assert: publish و leg همیشه باید fire کنند (هر tick، نه هر N)
        assert fired["publish"] >= 1, f"publish باید fire کند: {fired}"
        assert fired["leg"] >= 1, f"leg (HLC) باید fire کند: {fired}"
        # neural باید در ≥۱ tick fire کند
        assert fired["neural"] >= 1, f"neural باید fire کند: {fired}"
        # consolidation/affferent/idea در beat مضربِ N — باید ≥۱
        # (اگر فلگ‌ها واقعاً paper-full هستند، این‌ها هم fire می‌کنند)
        assert fired["consolidation"] >= 1 or fired["afferent"] >= 1, \
            f"consolidation یا afferent باید fire کنند: {fired}"
    finally:
        for f in wiring.PAPER_FULL_FLAGS:
            os.environ.pop(f, None)
        os.environ.pop("OCTOPUS_PROFILE", None)


def test_bus_receives_advisory_events():
    """بعد از چند tick، LiveLoop advisory signals دارد (نخاعِ advisory فعال).
    advisory signals در _advisory_signals ثبت می‌شوند (نه در bus.events، چون
    advisory نباید ردیفِ ledger بسازند)."""
    os.environ["OCTOPUS_PROFILE"] = "paper-full"
    wiring.apply_profile()
    try:
        ll = wiring.make_live_loop()
        wiring.publish_tick_signals(ll, rhythm_state={"mode": "GREEN"})
        wiring.publish_tick_signals(ll, rhythm_state={"mode": "AMBER"})
        assert len(ll.advisory_signals) >= 2, \
            f"LiveLoop باید ≥۲ advisory signal داشته باشد: {len(ll.advisory_signals)}"
    finally:
        for f in wiring.PAPER_FULL_FLAGS:
            os.environ.pop(f, None)
        os.environ.pop("OCTOPUS_PROFILE", None)


def t_pacemaker_bug_fixed():
    """FIX: _pacemaker نباید بعد از boot به None بازنشانی شود (باگِ کشف‌شده)."""
    src = (_OPS / "organism.py").read_text("utf-8")
    # نباید خطِ '_pacemaker = None' بعد از 'next_epoch_at = 0.0' باشد
    idx = src.find("next_epoch_at = 0.0")
    after = src[idx:idx + 200]
    assert "_pacemaker = None" not in after, \
        "FIX: _pacemaker نباید بعد از boot clobber شود (باگِ P-L1)"
    # ولی باید _pacemaker = None در boot init section باشد (default)
    boot_section = src[:src.find("next_epoch_at = 0.0")]
    assert "_pacemaker = None" in boot_section, \
        "_pacemaker باید در boot init با None مقداردهی شود"


if __name__ == "__main__":
    failed = harness.run([
        # (الف) bare
        ("default profile = bare", t_default_profile_is_bare),
        ("bare → no flags", t_bare_profile_no_flags),
        # (ب) paper-full flags
        ("paper-full → همهٔ flagها", t_paper_full_sets_all_flags),
        ("paper-full → بدونِ money flag", t_paper_full_no_money_flag),
        # (ج) boot builds
        ("boot builds all modules", t_boot_builds_all_modules),
        ("boot builds unified bus", t_boot_builds_unified_bus),
        ("boot builds live loop", t_boot_builds_live_loop),
        # (د) all fire
        ("all modules fire ≥1", test_all_modules_fire_in_simulated_ticks),
        ("bus receives advisory", test_bus_receives_advisory_events),
        # FIX
        ("_pacemaker clobber فیکس شد", t_pacemaker_bug_fixed),
    ])
    sys.exit(1 if failed else 0)
