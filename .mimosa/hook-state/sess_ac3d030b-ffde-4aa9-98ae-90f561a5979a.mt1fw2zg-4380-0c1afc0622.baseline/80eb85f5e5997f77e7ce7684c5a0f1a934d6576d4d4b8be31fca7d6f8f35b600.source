#!/usr/bin/env python3
"""Phase 1 — behavioral tests for B5/B7/B8/C9/C10.

ویFY هر فیکس واقعاً در کد زنده است و داده جریان دارد.
$0 آفلاین.
"""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import harness  # noqa: E402
ENV = harness.setup("phase1-wiring")

_OPS = (harness.SELF_OPS)
for _p in [str(_OPS), str(_OPS / "budget"), str(_OPS / "doctor"),
           str(_OPS / "doctor" / "box"), str(_OPS / "neural")]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

import chrono  # noqa: E402
import wiring  # noqa: E402
from doctor import Doctor  # noqa: E402

ORGANISM_SRC = (_OPS / "organism.py").read_text("utf-8")
DOCTOR_SRC = (_OPS / "doctor" / "doctor.py").read_text("utf-8")


# ════════════════════════════════════════════════════════════════════════════════
# B5 — doctor در pacemaker + circuit-breaker
# ════════════════════════════════════════════════════════════════════════════════

def t_b5_doctor_param_in_start_pacemaker():
    """start_pacemaker_thread اکنون doctor را می‌پذیرد."""
    import inspect
    sig = inspect.signature(chrono.start_pacemaker_thread)
    assert "doctor" in sig.parameters


def t_b5_organism_passes_doctor():
    """organism.py باید doctor=_doctor_inst را به start_pacemaker_thread پاس بدهد."""
    assert "doctor=_doctor_inst" in ORGANISM_SRC, \
        "organism باید doctor را به start_pacemaker_thread پاس بدهد"


def t_b5_selfheal_behind_flag():
    """self-heal باید پشتِ OCTOPUS_WIRE_SELFHEAL باشد."""
    chrono_src = (_OPS / "chrono.py").read_text("utf-8")
    assert "OCTOPUS_WIRE_SELFHEAL" in chrono_src


def t_b5_circuit_breaker_exists():
    """circuit-breaker برای ضدِ restart-storm."""
    chrono_src = (_OPS / "chrono.py").read_text("utf-8")
    assert "circuit-breaker" in chrono_src.lower() or "max_restarts" in chrono_src


def t_b5_pacemaker_with_doctor():
    """Pacemaker با doctor نباید None باشد."""
    db = chrono.ChronoDB(ENV["ops"] / "state" / "chrono-b5.db")
    doc = Doctor(state_dir=str(ENV["ops"] / "state"))
    pm = chrono.Pacemaker(db=db, doctor=doc)
    assert pm.doctor is not None, "Pacemaker با doctor باید doctor داشته باشد"


# ════════════════════════════════════════════════════════════════════════════════
# B7 — chamber trace backfill
# ════════════════════════════════════════════════════════════════════════════════

def t_b7_chamber_uses_gather_trace():
    """run_chamber باید از self._gather_trace() استفاده کند وقتی trace خالی است."""
    assert "trace or self._gather_trace()" in DOCTOR_SRC, \
        "B7: chamber باید از _gather_trace backfill کند"


def t_b7_chamber_not_empty_trace():
    """وقتی trace=None، chamber نباید trace={} خالی بگیرد."""
    assert "trace=trace or {}" not in DOCTOR_SRC, \
        "B7: نباید trace or {} باشد (باید _gather_trace)"


# ════════════════════════════════════════════════════════════════════════════════
# B8 — phi_to_novelty وصل شد
# ════════════════════════════════════════════════════════════════════════════════

def t_b8_phi_to_novelty_called():
    """phi_to_novelty باید در doctor.py صدا زده شود."""
    assert "phi_to_novelty" in DOCTOR_SRC


def t_b8_last_phi_t_stored():
    """phi_t باید برای cycle بعد نگه‌داشته شود (self._last_phi_t)."""
    assert "_last_phi_t" in DOCTOR_SRC


def t_b8_novelty_in_report():
    """novelty_from_phi باید در گزارشِ box cycle باشد."""
    assert "novelty_from_phi" in DOCTOR_SRC


# ════════════════════════════════════════════════════════════════════════════════
# C9 — dead stack entries removed
# ════════════════════════════════════════════════════════════════════════════════

def t_c9_no_dead_hooks_in_stack():
    """stack نباید hooks/nociceptor/reflex داشته باشد."""
    os.environ["OCTOPUS_WIRE_NEURAL"] = "1"
    stack = wiring.make_neural_stack()
    os.environ.pop("OCTOPUS_WIRE_NEURAL")
    if stack is None:
        return
    assert "hooks" not in stack, "C9: hooks نباید در stack باشد"
    assert "nociceptor" not in stack, "C9: nociceptor نباید در stack باشد"
    assert "reflex" not in stack, "C9: reflex نباید در stack باشد"


def t_c9_stack_has_core():
    """stack همچنان driver/hebbian/consolidation دارد."""
    os.environ["OCTOPUS_WIRE_NEURAL"] = "1"
    stack = wiring.make_neural_stack()
    os.environ.pop("OCTOPUS_WIRE_NEURAL")
    if stack is None:
        return
    assert "driver" in stack
    assert "hebbian" in stack
    assert "consolidation" in stack


# ════════════════════════════════════════════════════════════════════════════════
# C10 — spectral_result حذف شد
# ════════════════════════════════════════════════════════════════════════════════

def t_c10_no_hardcoded_spectral_none():
    """spectral_result=None نباید در organism.py سخت‌کد باشد."""
    assert "spectral_result=None" not in ORGANISM_SRC, \
        "C10: spectral_result=None نباید سخت‌کد باشد"


if __name__ == "__main__":
    failed = harness.run([
        # B5
        ("B5: doctor param در start_pacemaker", t_b5_doctor_param_in_start_pacemaker),
        ("B5: organism doctor را پاس می‌دهد", t_b5_organism_passes_doctor),
        ("B5: self-heal پشتِ flag", t_b5_selfheal_behind_flag),
        ("B5: circuit-breaker", t_b5_circuit_breaker_exists),
        ("B5: Pacemaker با doctor", t_b5_pacemaker_with_doctor),
        # B7
        ("B7: chamber از _gather_trace", t_b7_chamber_uses_gather_trace),
        ("B7: نه trace or {}", t_b7_chamber_not_empty_trace),
        # B8
        ("B8: phi_to_novelty صدا زده", t_b8_phi_to_novelty_called),
        ("B8: _last_phi_t ذخیره", t_b8_last_phi_t_stored),
        ("B8: novelty در report", t_b8_novelty_in_report),
        # C9
        ("C9: dead stack حذف", t_c9_no_dead_hooks_in_stack),
        ("C9: core باقی", t_c9_stack_has_core),
        # C10
        ("C10: spectral_result حذف", t_c10_no_hardcoded_spectral_none),
    ])
    sys.exit(1 if failed else 0)
