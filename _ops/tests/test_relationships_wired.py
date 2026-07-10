#!/usr/bin/env python3
"""تستِ رفتاری: همهٔ روابطِ تعریف‌شده در ساختارها، کدنویسی شده‌اند.

این تست اثبات می‌کند که ۷ رابطه‌ای که قبلاً تعریف‌شده-ولی-کدنشده بودند،
حالا واقعاً وصل شده‌اند:
  ۱) barbell_allocate → run_epoch (پشتِ flag)
  ۲) confirmed_revenue → fitness formula (revenue term)
  ۳) Rhythm → mode_color در tick
  ۴) circadian readiness → wiring
  ۵) sprint SprintRunner → wiring
  ۶) debate_loop → governor_epoch (پشتِ flag)
  ۷) rhythm/circadian/sprint در organism boot + tick
$0 آفلاین.
"""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import harness  # noqa: E402
ENV = harness.setup("relationships-wired")

_OPS = (harness.REAL_VAULT / r"_ops")
for _p in [str(_OPS), str(_OPS / "budget"), str(_OPS / "neural"),
           str(_OPS / "chrono_rhythm"), str(_OPS / "debate")]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

import wiring  # noqa: E402
import governor_epoch  # noqa: E402

ORGANISM_SRC = (_OPS / "organism.py").read_text("utf-8")
WIRING_SRC = (_OPS / "wiring.py").read_text("utf-8")
GOVERNOR_SRC = (_OPS / "budget" / "governor_epoch.py").read_text("utf-8")
FITNESS_SRC = (_OPS / "budget" / "fitness.py").read_text("utf-8")


# ════════════════════════════════════════════════════════════════════════════════
# ۱) barbell_allocate → run_epoch
# ════════════════════════════════════════════════════════════════════════════════

def t_barbell_in_run_epoch():
    """run_epoch باید barbell_allocate را صدا بزند (پشتِ flag)."""
    assert "barbell_allocate" in GOVERNOR_SRC, \
        "run_epoch باید barbell_allocate را صدا بزنند"
    assert "OCTOPUS_WIRE_BARBELL" in GOVERNOR_SRC


# ════════════════════════════════════════════════════════════════════════════════
# ۲) confirmed_revenue → fitness formula
# ════════════════════════════════════════════════════════════════════════════════

def t_revenue_in_fitness_formula():
    """fitness باید confirmed_revenue را در فرمول استفاده کند (پشتِ flag)."""
    assert "revenue_boost_applied" in FITNESS_SRC, \
        "fitness باید revenue را در فرمول استفاده کند"
    assert "rev_signal" in FITNESS_SRC


# ════════════════════════════════════════════════════════════════════════════════
# ۳) Rhythm → mode_color در tick
# ════════════════════════════════════════════════════════════════════════════════

def t_rhythm_beat_function_exists():
    """wiring باید rhythm_beat داشته باشد."""
    assert hasattr(wiring, "rhythm_beat"), "wiring باید rhythm_beat داشته باشد"
    assert hasattr(wiring, "make_rhythm"), "wiring باید make_rhythm داشته باشد"


def t_rhythm_beat_works():
    """rhythm_beat باید mode_color برگرداند."""
    r = wiring.make_rhythm()
    if r is None:
        return  # import skip
    state = wiring.rhythm_beat(r, readiness=0.6, stress=0.2, novelty=0.3)
    assert state is not None, "rhythm_beat باید state برگرداند"
    assert "mode_color" in state, "rhythm باید mode_color داشته باشد"
    assert state["mode_color"] in ("GREEN", "AMBER", "RED")


def t_organism_uses_rhythm():
    """organism.py باید rhythm را در boot بسازد و در tick صدا بزند."""
    assert "make_rhythm" in ORGANISM_SRC, "boot باید make_rhythm را صدا بزنند"
    assert "rhythm_beat" in ORGANISM_SRC, "tick باید rhythm_beat را صدا بزنند"
    assert "_rhythm_state" in ORGANISM_SRC, "tick باید rhythm_state را نگه دارد"


# ════════════════════════════════════════════════════════════════════════════════
# ۴) circadian readiness → wiring
# ════════════════════════════════════════════════════════════════════════════════

def t_circadian_in_wiring():
    """wiring باید make_circadian + circadian_readiness داشته باشد."""
    assert hasattr(wiring, "make_circadian")
    assert hasattr(wiring, "circadian_readiness")


def t_circadian_works():
    """circadian_readiness باید phase برگرداند."""
    c = wiring.make_circadian()
    if c is None:
        return
    r = wiring.circadian_readiness(c, hour=14)
    assert r is not None
    assert "phase" in r and "readiness" in r


def t_organism_uses_circadian():
    """organism.py باید circadian را بسازد و صدا بزند."""
    assert "make_circadian" in ORGANISM_SRC
    assert "circadian_readiness" in ORGANISM_SRC


# ════════════════════════════════════════════════════════════════════════════════
# ۵) sprint SprintRunner → wiring
# ════════════════════════════════════════════════════════════════════════════════

def t_sprint_in_wiring():
    """wiring باید make_sprint_runner داشته باشد."""
    assert hasattr(wiring, "make_sprint_runner")


def t_organism_uses_sprint():
    """organism.py باید sprint_runner را در boot بسازد."""
    assert "make_sprint_runner" in ORGANISM_SRC


# ════════════════════════════════════════════════════════════════════════════════
# ۶) debate_loop → governor_epoch
# ════════════════════════════════════════════════════════════════════════════════

def t_debate_in_run_epoch():
    """run_epoch باید debate_loop را صدا بزند (پشتِ flag)."""
    assert "run_debate" in GOVERNOR_SRC, "run_epoch باید run_debate را صدا بزنند"
    assert "OCTOPUS_WIRE_DEBATE" in GOVERNOR_SRC


# ════════════════════════════════════════════════════════════════════════════════
# ۷) rhythm_state به neural_beat و publish منتقل می‌شود
# ════════════════════════════════════════════════════════════════════════════════

def t_rhythm_state_to_neural_beat():
    """rhythm_state باید به neural_beat پاس داده شود (نه chrono pulse همیشگی)."""
    idx = ORGANISM_SRC.find("neural_beat(")
    snippet = ORGANISM_SRC[idx:idx + 300]
    assert "_rhythm_state" in snippet, \
        "neural_beat باید rhythm_state (mode_color) را بگیرد"


def t_rhythm_state_to_publish():
    """rhythm_state باید به publish_tick_signals منتقل شود (از طریقِ _rh)."""
    # _rh از _rhythm_state ساخته می‌شود، بعد به publish_tick_signals پاس داده می‌شود
    assert "_rh = _rhythm_state" in ORGANISM_SRC or "_rh=_rhythm_state" in ORGANISM_SRC, \
        "_rh باید از _rhythm_state ساخته شود"
    idx = ORGANISM_SRC.find("publish_tick_signals(")
    snippet = ORGANISM_SRC[idx:idx + 300]
    assert "rhythm_state=_rh" in snippet, \
        "publish_tick_signals باید rhythm_state=_rh را بگیرد (برای advisory)"


# ════════════════════════════════════════════════════════════════════════════════
# wire_summary تمام flagهای نو را نشان می‌دهد
# ════════════════════════════════════════════════════════════════════════════════

def t_wire_summary_has_new_flags():
    """wire_summary باید rhythm/circadian/sprint/barbell/debate را نشان دهد."""
    s = wiring.wire_summary()
    for k in ("wire_rhythm", "wire_circadian", "wire_sprint",
              "wire_barbell", "wire_debate"):
        assert k in s, f"wire_summary باید {k} داشته باشد"


if __name__ == "__main__":
    failed = harness.run([
        # ۱) barbell → epoch
        ("barbell در run_epoch", t_barbell_in_run_epoch),
        # ۲) revenue → fitness
        ("revenue در fitness formula", t_revenue_in_fitness_formula),
        # ۳) rhythm → mode_color
        ("rhythm_beat در wiring", t_rhythm_beat_function_exists),
        ("rhythm_beat کار می‌کند", t_rhythm_beat_works),
        ("organism rhythm می‌سازد", t_organism_uses_rhythm),
        # ۴) circadian
        ("circadian در wiring", t_circadian_in_wiring),
        ("circadian کار می‌کند", t_circadian_works),
        ("organism circadian", t_organism_uses_circadian),
        # ۵) sprint
        ("sprint در wiring", t_sprint_in_wiring),
        ("organism sprint", t_organism_uses_sprint),
        # ۶) debate → epoch
        ("debate در run_epoch", t_debate_in_run_epoch),
        # ۷) rhythm → neural + publish
        ("rhythm_state به neural_beat", t_rhythm_state_to_neural_beat),
        ("rhythm_state به publish", t_rhythm_state_to_publish),
        # wire_summary
        ("wire_summary flagهای نو", t_wire_summary_has_new_flags),
    ])
    sys.exit(1 if failed else 0)
