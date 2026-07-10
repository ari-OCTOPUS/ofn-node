#!/usr/bin/env python3
"""تستِ رفتاریِ P-W1 (نخاع): اتصالِ مغز (organism) به بدن (LiveLoop/UnifiedBus).

گپِ recon 🔴: organism حلقهٔ لخت می‌زد؛ LiveLoop (ارکستراسیونِ غنی: bus+legs+
doctor+advisory) هیچ‌جا instantiate/run نمی‌شد = shelfware. مغز و بدن دو نیمهٔ جدا
بودند. بوت make_unified_bus()/make_lead_leg() صدا می‌زد ولی return دور ریخته می‌شد.

این تست اثبات می‌کند:
  (الف) publish_tick_signals سیگنال‌ها را به bus می‌فرستد → bus event دارد و
      LiveLoop.advisory_signals پُر است (نه خالی) — با LiveLoop واقعی.
  (ب) صفر effector: بعد از publish، هیچ settle/effect در bus رخ نمی‌دهد (advisory).
  (ج) kill-switch: STOP فعال → publish صفر.
  (د) سازگاری عقب‌رو: flag‌های wiring خاموز → make_unified_bus=None → make_live_loop
      یک busِ in-memory می‌سازد (تشخیصِ bare، نه crash).
  (هـ) organism.py واقعاً returnهای bus/leg را نگه می‌دارد و LiveLoop می‌سازد
      (structural: built-and-discarded فیکس شد) و در tick publish می‌کند.
$0 آفلاین، stdlib-only.
"""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import harness  # noqa: E402
ENV = harness.setup("spinal-cord-w1")

_OPS = (harness.REAL_VAULT / r"_ops")
for _p in [str(_OPS), str(_OPS / "neural"), str(_OPS / "budget")]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

import wiring  # noqa: E402
from live_loop import LiveLoop, _InMemoryBus  # noqa: E402

ORGANISM_SRC = (_OPS / "organism.py").read_text("utf-8")


# ════════════════════════════════════════════════════════════════════════════════
# (الف) publish → bus events + LiveLoop.advisory_signals پُر
# ════════════════════════════════════════════════════════════════════════════════

def t_publish_fills_bus_and_advisory():
    """بعد از publish، LiveLoop.advisory_signals پُر است (نه خالی).
    advisory signals در _advisory_signals ثبت می‌شوند (نه bus.events، چون
    advisory نباید ردیفِ ledger بسازند)."""
    bus = _InMemoryBus()
    ll = LiveLoop(bus=bus)
    # قبل از publish: advisory_signals خالی
    assert len(ll.advisory_signals) == 0
    # شبیه‌سازیِ یک tick: rhythm + spectral + afferent + doctor
    n = wiring.publish_tick_signals(
        ll,
        rhythm_state={"mode_color": "GREEN", "readiness": 0.7},
        spectral_result={"sigma": 0.5, "cluster": "A"},
        afferent_status={"afferent_ratio": 0.6},
        doctor_result={"rfc": "fix-x", "lift": 0.1})
    assert n == 4, f"باید ۴ سیگنال publish شود، نه {n}"
    # advisory_signals باید پُر باشد
    assert len(ll.advisory_signals) == 4, \
        f"advisory_signals باید پُر باشد، نه {len(ll.advisory_signals)}"
    # event_typeها درست‌اند (از advisory_signals، نه bus.events)
    types = sorted(e["type"] for e in ll.advisory_signals)
    assert types == ["AFFERENT", "DOCTOR", "RHYTHM", "SPECTRAL"], types


def t_partial_publish():
    """اگر فقط بعضی سیگنال‌ها موجود باشند، فقط همان‌ها publish می‌شوند."""
    bus = _InMemoryBus()
    ll = LiveLoop(bus=bus)
    n = wiring.publish_tick_signals(ll, rhythm_state={"mode": "AMBER"})
    assert n == 1
    assert len(ll.advisory_signals) == 1
    assert ll.advisory_signals[0]["type"] == "RHYTHM"


def t_no_signals_no_publish():
    """اگر هیچ سیگنالی موجود نباشد، صفر publish."""
    bus = _InMemoryBus()
    ll = LiveLoop(bus=bus)
    n = wiring.publish_tick_signals(ll)
    assert n == 0
    assert len(ll.advisory_signals) == 0


def t_multiple_ticks_accumulate():
    """بعد از چند tick شبیه‌سازی‌شده، advisory_signals تجمعی پُر می‌شوند."""
    bus = _InMemoryBus()
    ll = LiveLoop(bus=bus)
    for i in range(3):
        wiring.publish_tick_signals(ll, rhythm_state={"tick": i})
    assert len(ll.advisory_signals) == 3


# ════════════════════════════════════════════════════════════════════════════════
# (ب) صفر effector — publish فقط advisory است
# ════════════════════════════════════════════════════════════════════════════════

def t_advisory_events_marked_advisory_only():
    """هر event باید advisory_only=True داشته باشد (هیچ effector)."""
    bus = _InMemoryBus()
    ll = LiveLoop(bus=bus)
    wiring.publish_tick_signals(ll, rhythm_state={"m": 1}, spectral_result={"s": 1})
    for e in ll.advisory_signals:
        payload = e.get("payload", {})
        assert payload.get("advisory_only") is True, \
            f"event {e['type']} باید advisory_only=True باشد"


def t_publish_does_not_settle():
    """publish نباید هیچ settle/effect صدا بزند. advisory-only، نه settle."""
    bus = _InMemoryBus()
    ll = LiveLoop(bus=bus)
    before = len(ll.advisory_signals)
    wiring.publish_tick_signals(ll, rhythm_state={"x": 1})
    after = len(ll.advisory_signals)
    # فقط یک advisory اضافه شد، نه settle
    assert after - before == 1


# ════════════════════════════════════════════════════════════════════════════════
# (ج) kill-switch
# ════════════════════════════════════════════════════════════════════════════════

def t_killswitch_blocks_publish():
    """STOP فعال → publish_tick_signals صفر برمی‌گرداند."""
    import opslib
    bus = _InMemoryBus()
    ll = LiveLoop(bus=bus)
    opslib.STOP_ORGANISM.write_text("kill", "utf-8")
    try:
        n = wiring.publish_tick_signals(ll, rhythm_state={"m": 1})
    finally:
        try:
            opslib.STOP_ORGANISM.unlink()
        except OSError:
            pass
    assert n == 0, "kill-switch باید publish را بلوک کند"
    assert len(ll.advisory_signals) == 0


# ════════════════════════════════════════════════════════════════════════════════
# (د) سازگاری عقب‌رو — flag‌های wiring خاموز = bare
# ════════════════════════════════════════════════════════════════════════════════

def t_bare_flags_off():
    """flag‌های wiring خاموز → make_unified_bus=None، make_lead_leg=None."""
    for k in ("OCTOPUS_WIRE_UNIFIED", "OCTOPUS_WIRE_LEAD", "OCTOPUS_WIRE_DOCTOR"):
        os.environ.pop(k, None)
    assert wiring.make_unified_bus() is None
    assert wiring.make_lead_leg() is None


def t_make_live_loop_without_bus_uses_inmemory():
    """make_live_loop با bus=None همیشه یک LiveLoop برمی‌گرداند (bus درون‌ساز)."""
    for k in ("OCTOPUS_WIRE_UNIFIED", "OCTOPUS_WIRE_DOCTOR"):
        os.environ.pop(k, None)
    ll = wiring.make_live_loop(bus=None, leg=None, doctor=None)
    assert ll is not None, "make_live_loop نباید None برگرداند (حتی در bare)"
    assert isinstance(ll, LiveLoop)
    # bus درون‌ساز باید in-memory باشد (نه None)
    assert ll.bus is not None


def t_bare_no_publish_in_tick():
    """در bare (LiveLoop=None)، publish_tick_signals صفر — no regression.

    این شبیه‌سازی می‌کند که اگر LiveLoop ساخته نشد (flag خاموز)، tick بدونِ
    publish ادامه می‌دهد — رفتارِ فعلیِ لخت."""
    n = wiring.publish_tick_signals(None, rhythm_state={"m": 1})
    assert n == 0


# ════════════════════════════════════════════════════════════════════════════════
# (هـ) organism.py سیم‌کشی واقعی (structural — built-and-discarded فیکس شد)
# ════════════════════════════════════════════════════════════════════════════════

def t_organism_keeps_bus_and_leg_returns():
    """بوت باید returnهای bus/leg را در متغیر نگه دارد، نه دور بریز (گپِ اصلی)."""
    # نباید الگویِ «make_unified_bus()\n        make_lead_leg()» بدونِ assign باشد
    assert "_bus = _w.make_unified_bus()" in ORGANISM_SRC, \
        "boot باید bus را در _bus نگه دارد (نه discard)"
    assert "_leg = _w.make_lead_leg()" in ORGANISM_SRC, \
        "boot باید leg را در _leg نگه دارد (نه discard)"


def t_organism_builds_live_loop():
    """بوت باید LiveLoop بسازد و نگه دارد."""
    assert "_live_loop = _w.make_live_loop(" in ORGANISM_SRC, \
        "boot باید make_live_loop را صدا بزند و در _live_loop نگه دارد"


def t_organism_publishes_in_tick():
    """tick باید publish_tick_signals را صدا بزند (نخاعِ فعال)."""
    assert "publish_tick_signals" in ORGANISM_SRC, \
        "tick باید publish_tick_signals را صدا بزند"


def t_organism_publish_gated_on_protective():
    """publish باید زیرِ گاردِ not _protective_skip باشد (مانندِ doctor)."""
    idx = ORGANISM_SRC.find("publish_tick_signals")
    assert idx > 0
    before = ORGANISM_SRC[max(0, idx - 500):idx]
    assert "_protective_skip" in before, \
        "publish باید روی not _protective_skip گیت باشد"


def t_organism_publish_alerts_on_error():
    """§۴: بلوکِ publish نباید except بی‌صدا باشد — باید alert."""
    idx = ORGANISM_SRC.find("publish_tick_signals")
    assert idx > 0
    block = ORGANISM_SRC[idx:idx + 600]   # پنجرهٔ بزرگ‌تر (مستعد shift با افزودنِ پارامتر)
    assert "opslib.alert" in block, \
        "§۴: publish error باید alert شود (خطای خاموش ممنون)"


def t_organism_publish_reuses_same_bus():
    """LiveLoop باید همان bus ساخته‌شده در بوت را بگیرد (نه یک busِ جدا)."""
    # make_live_loop باید bus=_bus را پاس بدهد
    idx = ORGANISM_SRC.find("make_live_loop(")
    assert idx > 0
    snippet = ORGANISM_SRC[idx:idx + 120]
    assert "bus=_bus" in snippet, \
        "make_live_loop باید bus=_bus را پاس بدهد (همان نخاع، نه bus جدا)"


if __name__ == "__main__":
    failed = harness.run([
        # (الف) publish → bus + advisory پُر
        ("publish → bus events + advisory پُر", t_publish_fills_bus_and_advisory),
        ("publish جزئی", t_partial_publish),
        ("بدونِ سیگنال → صفر publish", t_no_signals_no_publish),
        ("چند tick → تجمعی", t_multiple_ticks_accumulate),
        # (ب) صفر effector
        ("advisory_only=True", t_advisory_events_marked_advisory_only),
        ("publish settle نمی‌کند", t_publish_does_not_settle),
        # (ج) kill-switch
        ("kill-switch → publish صفر", t_killswitch_blocks_publish),
        # (د) سازگاری عقب‌رو
        ("bare: flags off → None", t_bare_flags_off),
        ("bare: make_live_loop in-memory bus", t_make_live_loop_without_bus_uses_inmemory),
        ("bare: LiveLoop=None → صفر publish", t_bare_no_publish_in_tick),
        # (هـ) organism wiring structural
        ("boot bus/leg را نگه می‌دارد (discard فیکس)", t_organism_keeps_bus_and_leg_returns),
        ("boot LiveLoop می‌سازد", t_organism_builds_live_loop),
        ("tick publish می‌کند", t_organism_publishes_in_tick),
        ("publish روی not _protective_skip", t_organism_publish_gated_on_protective),
        ("publish error alert (§۴)", t_organism_publish_alerts_on_error),
        ("LiveLoop همان bus را می‌گیرد", t_organism_publish_reuses_same_bus),
    ])
    sys.exit(1 if failed else 0)
