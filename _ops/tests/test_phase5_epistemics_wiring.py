#!/usr/bin/env python3
"""Phase 5 — Epistemics wiring: behavioral test.

epistemics_beat پشتِ OCTOPUS_WIRE_EPISTEMICS. advisory، non-enforcer.
flag on → fire هر N beat. flag off → inert. no-collision.
$0 آفلاین.
"""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import harness  # noqa: E402
ENV = harness.setup("phase5-epi-wiring")

_OPS = Path(r"F:\backup\_ops")
for _p in [str(_OPS), str(_OPS / "budget"), str(_OPS / "neural")]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

import wiring  # noqa: E402

ORGANISM_SRC = (_OPS / "organism.py").read_text("utf-8")


def t_flag_off_inert():
    """flag off → epistemics_beat None."""
    os.environ.pop("OCTOPUS_WIRE_EPISTEMICS", None)
    assert wiring.epistemics_beat() is None


def t_flag_on_beat_non_multiple():
    """flag on + beat غیرِ مضربِ N → None (هنوز نوبت نیست)."""
    os.environ["OCTOPUS_WIRE_EPISTEMICS"] = "1"
    try:
        assert wiring.epistemics_beat(beat=100) is None  # ۱۰۰ مضربِ ۷۲۰ نیست
    finally:
        os.environ.pop("OCTOPUS_WIRE_EPISTEMICS")


def t_flag_on_fire():
    """flag on + beat مضربِ N → fire (metrics_count > 0)."""
    os.environ["OCTOPUS_WIRE_EPISTEMICS"] = "1"
    try:
        r = wiring.epistemics_beat(beat=720)
        assert r is not None
        assert "metrics_count" in r
        assert r["metrics_count"] >= 1
        assert r["advisory_only"] is True
    finally:
        os.environ.pop("OCTOPUS_WIRE_EPISTEMICS")


def t_organism_calls_epistemics():
    """organism.py باید epistemics_beat را در tick صدا بزند."""
    assert "epistemics_beat" in ORGANISM_SRC


def t_advisory_only():
    """خروجی باید advisory_only=True داشته باشد (non-enforcer)."""
    os.environ["OCTOPUS_WIRE_EPISTEMICS"] = "1"
    try:
        r = wiring.epistemics_beat(beat=720)
        if r:
            assert r.get("advisory_only") is True
    finally:
        os.environ.pop("OCTOPUS_WIRE_EPISTEMICS")


def t_not_in_paper_full():
    """OCTOPUS_WIRE_EPISTEMICS نباید در PAPER_FULL_FLAGS باشد (merge ≠ enable)."""
    assert "OCTOPUS_WIRE_EPISTEMICS" not in wiring.PAPER_FULL_FLAGS


def t_wire_summary_has_epistemics():
    """wire_summary باید wire_epistemics را نشان دهد (پیش‌فرض خاموز)."""
    os.environ.pop("OCTOPUS_WIRE_EPISTEMICS", None)
    s = wiring.wire_summary()
    assert "wire_epistemics" in s
    assert s["wire_epistemics"] is False, "پیش‌فرض باید خاموز باشد"


def t_killswitch_blocks():
    """STOP فعال → None حتی با flag روشن."""
    import opslib
    os.environ["OCTOPUS_WIRE_EPISTEMICS"] = "1"
    opslib.STOP_ORGANISM.write_text("kill", "utf-8")
    try:
        r = wiring.epistemics_beat(beat=720)
    finally:
        try:
            opslib.STOP_ORGANISM.unlink()
        except OSError:
            pass
    os.environ.pop("OCTOPUS_WIRE_EPISTEMICS")
    assert r is None


if __name__ == "__main__":
    failed = harness.run([
        ("flag off → inert", t_flag_off_inert),
        ("beat غیرِ مضربِ N → None", t_flag_on_beat_non_multiple),
        ("flag on → fire", t_flag_on_fire),
        ("organism calls epistemics", t_organism_calls_epistemics),
        ("advisory_only=True", t_advisory_only),
        ("not in PAPER_FULL_FLAGS", t_not_in_paper_full),
        ("wire_summary epistemics", t_wire_summary_has_epistemics),
        ("kill-switch blocks", t_killswitch_blocks),
    ])
    sys.exit(1 if failed else 0)
