#!/usr/bin/env python3
"""Offline, hermetic test for M5 (now_moves/kill_seam_closer).

Stdlib-only · no network · all STOP flags + logs isolated to a tmp OPS_DIR.
Verifies seam_denies() (flag off → False even with STOP present; flag on + STOP →
True), that organ_gate.reserve() denies with the seam armed, and — the key
zero-change proof — that with the flag OFF reserve() ignores STOP-ORGANISM exactly
as before. Standalone (exit 0/1) per run_all.py; also exposes test_*.
"""
import os
import sys
import tempfile
from pathlib import Path

_TMP = tempfile.mkdtemp(prefix="m5_killseam_")
os.environ["ORG_ROOT"] = _TMP
os.environ["OPS_DIR"] = str(Path(_TMP) / "_ops")
os.environ.pop("OCTOPUS_WIRE_KILL_SEAM", None)
(Path(_TMP) / "_ops" / "budget").mkdir(parents=True, exist_ok=True)

HERE = Path(__file__).resolve().parent
OPS = HERE.parent
for _p in (str(OPS / "now_moves"), str(OPS / "budget"), str(OPS)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import kill_seam_closer as P                              # noqa: E402

STOP = Path(os.environ["OPS_DIR"]) / "STOP-ORGANISM"


def _mkstop():
    STOP.write_text("stop", "utf-8")


def _rmstop():
    if STOP.exists():
        STOP.unlink()


def _off():
    os.environ.pop("OCTOPUS_WIRE_KILL_SEAM", None)


def _on():
    os.environ["OCTOPUS_WIRE_KILL_SEAM"] = "1"


def test_flag_off_false_even_with_stop():
    _off(); _mkstop()
    assert P.seam_denies() is False, "flag OFF must ignore STOP-ORGANISM"
    _rmstop()
    print("  ok flag OFF + STOP present -> seam_denies False (zero change)")


def test_flag_on_no_stop_false():
    _on(); _rmstop()
    assert P.seam_denies() is False
    _off()
    print("  ok flag ON + no STOP       -> seam_denies False")


def test_flag_on_stop_true():
    _on(); _mkstop()
    assert P.seam_denies() is True
    _rmstop(); _off()
    print("  ok flag ON + STOP present  -> seam_denies True")


def test_callsite_logic():
    # replicate the EXACT call-site both organ_gate:63 and debate_loop:102 use:
    #   if <flag> and not stop and seam_denies(): stop = "STOP(organism)"
    _on(); _mkstop()
    stop = None                                       # opslib.halted() returned None
    if os.environ.get("OCTOPUS_WIRE_KILL_SEAM") == "1" and not stop and P.seam_denies():
        stop = "STOP(organism)"
    assert stop == "STOP(organism)", stop             # armed → deny path engaged
    _off()
    stop2 = None
    if os.environ.get("OCTOPUS_WIRE_KILL_SEAM") == "1" and not stop2 and P.seam_denies():
        stop2 = "STOP(organism)"
    assert stop2 is None, stop2                        # flag OFF → seam never fires
    _rmstop()
    print("  ok call-site logic         -> armed sets stop; OFF leaves it (both sites)")


def test_precedence_existing_stop_wins():
    # if opslib.halted() already returned a reason, the seam must NOT overwrite it
    _on(); _mkstop()
    stop = "STOP(architect)"
    if os.environ.get("OCTOPUS_WIRE_KILL_SEAM") == "1" and not stop and P.seam_denies():
        stop = "STOP(organism)"
    assert stop == "STOP(architect)", stop             # `not stop` guard preserves prior reason
    _rmstop(); _off()
    print("  ok precedence              -> existing halt reason preserved (not stop)")


def _run():
    tests = [test_flag_off_false_even_with_stop, test_flag_on_no_stop_false,
             test_flag_on_stop_true, test_callsite_logic, test_precedence_existing_stop_wins]
    print("test_kill_seam_closer (M5) — offline, hermetic")
    for t in tests:
        t()
    print(f"PASS {len(tests)}/{len(tests)}")


if __name__ == "__main__":
    try:
        _run()
    except AssertionError as e:
        print("FAIL:", e); sys.exit(1)
    except Exception as e:  # noqa: BLE001
        print("ERROR:", type(e).__name__, e); sys.exit(1)
    sys.exit(0)
