#!/usr/bin/env python3
"""test_d1_outbound_halt — D1: canonical hard-halt is supreme at the outbound worker entry.

Before D1, outbound_worker.send_one had ZERO explicit halt refs (GLOBAL-HALT-MATRIX RISK) —
its safety relied on the downstream settle-gate + the NOT_ARMED transport stub. D1 adds an
explicit master_halted() gate at the TOP of send_one, so under HALT-ALL / architect STOP it
refuses (status='halted', zero send) BEFORE any gate/transport, and halt is supreme over the
enable flag. Hermetic, no live DB, no network.

Run: python -X utf8 test_d1_outbound_halt.py
"""
import os
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE.parent))
sys.path.insert(0, str(_HERE.parent / "budget"))
sys.path.insert(0, str(_HERE.parent / "legs"))
import harness   # noqa: E402
ENV = harness.setup("d1-outbound-halt")
import opslib          # noqa: E402
import outbound_worker  # noqa: E402

_FAILED = 0


def check(name, cond):
    global _FAILED
    print(("PASS" if cond else "FAIL"), "-", name)
    if not cond:
        _FAILED += 1


class _ExplodingGate:
    """اگر send_one زیرِ halt به gate برسد، این منفجر می‌شود — اثباتِ عدمِ عبور."""
    def __getattr__(self, _n):
        raise AssertionError("gate reached under halt — halt gate FAILED to short-circuit")


def _set(path, on):
    path.parent.mkdir(parents=True, exist_ok=True)
    if on:
        path.write_text("test", "utf-8")
    else:
        path.unlink(missing_ok=True)


CAND = {"contact": {"preferred_channel": "email"}}


def t_a_halt_all_refuses_before_gate():
    os.environ["OCTOPUS_WIRE_LEAD_OUTBOUND"] = "1"      # flag ON
    _set(opslib.HALT_ALL, True)
    try:
        r = outbound_worker.send_one("e1", CAND, gate=_ExplodingGate())
        check("HALT-ALL + flag-on → 'halted', zero send, gate NOT reached",
              r["status"] == "halted" and r["sent"] is False and r["ok"] is False)
    finally:
        _set(opslib.HALT_ALL, False)


def t_b_architect_stop_refuses():
    os.environ["OCTOPUS_WIRE_LEAD_OUTBOUND"] = "1"
    _set(opslib.STOP_ARCHITECT, True)
    try:
        r = outbound_worker.send_one("e1", CAND, gate=_ExplodingGate())
        check("architect STOP + flag-on → 'halted'", r["status"] == "halted")
    finally:
        _set(opslib.STOP_ARCHITECT, False)


def t_c_halt_supreme_over_flag_off():
    os.environ["OCTOPUS_WIRE_LEAD_OUTBOUND"] = "0"      # flag OFF
    _set(opslib.HALT_ALL, True)
    try:
        r = outbound_worker.send_one("e1", CAND, gate=_ExplodingGate())
        check("HALT-ALL + flag-off → 'halted' (halt supreme over flag)",
              r["status"] == "halted")
    finally:
        _set(opslib.HALT_ALL, False)


def t_d_no_halt_does_not_false_trigger():
    os.environ["OCTOPUS_WIRE_LEAD_OUTBOUND"] = "1"
    _set(opslib.HALT_ALL, False)
    _set(opslib.STOP_ARCHITECT, False)
    # not halted → passes the halt gate (proceeds downstream; gate/leg denies or errors,
    # but the status must NOT be 'halted' — proving the gate does not false-trigger).
    r = outbound_worker.send_one("e1", CAND, gate=None)
    check("no halt + flag-on → status != 'halted' (no false trigger)",
          r.get("status") != "halted" and r["sent"] is False)


def t_e_flag_off_no_halt_is_flag_off():
    os.environ["OCTOPUS_WIRE_LEAD_OUTBOUND"] = "0"
    _set(opslib.HALT_ALL, False)
    _set(opslib.STOP_ARCHITECT, False)
    r = outbound_worker.send_one("e1", CAND, gate=_ExplodingGate())
    check("no halt + flag-off → 'flag_off' (gate not reached)", r["status"] == "flag_off")


if __name__ == "__main__":
    for n, f in sorted(globals().items()):
        if n.startswith("t_"):
            try:
                f()
            except Exception as e:  # noqa: BLE001
                _FAILED += 1
                print("FAIL -", n, repr(e))
    print(f"\n== {_FAILED} failure(s) ==")
    print("OK test_d1_outbound_halt" if _FAILED == 0 else "FAIL test_d1_outbound_halt")
    sys.exit(1 if _FAILED else 0)
