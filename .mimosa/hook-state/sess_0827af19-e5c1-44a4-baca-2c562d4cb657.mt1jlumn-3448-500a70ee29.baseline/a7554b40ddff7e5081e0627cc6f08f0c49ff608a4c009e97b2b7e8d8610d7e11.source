#!/usr/bin/env python3
"""Offline, hermetic test for M3 (now_moves/cortex_symmetric_revive).

Stdlib-only · no network · no real process launch (launch_fn/incident_fn/clock/
port are all injected; history isolated to a tmp OPS_DIR). Verifies the decision
contract (dead/alive/STOP/never-born), dry-run + flag-OFF = no launch, actual
revive when enabled, and the two crash-safety belts (backoff + restart-cap→alert).
Standalone (exit 0/1) per run_all.py; also exposes test_*.
"""
import os
import sys
import tempfile
from pathlib import Path

_TMP = tempfile.mkdtemp(prefix="m3_cortex_revive_")
os.environ["ORG_ROOT"] = _TMP
os.environ["OPS_DIR"] = str(Path(_TMP) / "_ops")
os.environ.pop("OCTOPUS_WIRE_CORTEX_REVIVE", None)

HERE = Path(__file__).resolve().parent
OPS = HERE.parent
for _p in (str(OPS / "now_moves"), str(OPS / "budget"), str(OPS)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import cortex_symmetric_revive as P                       # noqa: E402

T = 1_000_000.0


class _Rec:
    def __init__(self, ret=True):
        self.n = 0; self.ret = ret; self.args = []

    def __call__(self, *a):
        self.n += 1; self.args.append(a); return self.ret


def _clear():
    os.environ.pop("OCTOPUS_WIRE_CORTEX_REVIVE", None)
    p = P._hist_path()
    if p and p.exists():
        p.unlink()


def test_decision_dead():
    assert P.should_revive_cortex(port_alive=False, stop_reason="", state_exists=True)[0] is True
    print("  ok decision: dead+born+no-STOP -> revive")


def test_decision_alive():
    assert P.should_revive_cortex(port_alive=True, stop_reason="", state_exists=True)[0] is False
    print("  ok decision: alive            -> no revive")


def test_decision_stop_senior():
    ok, why = P.should_revive_cortex(port_alive=False, stop_reason="STOP-CORTEX", state_exists=True)
    assert ok is False and "STOP" in why, why
    print("  ok decision: STOP present     -> no revive (senior)")


def test_decision_never_born():
    ok, why = P.should_revive_cortex(port_alive=False, stop_reason="", state_exists=False)
    assert ok is False and "never born" in why, why
    print("  ok decision: never born       -> no revive")


def test_dry_run_no_launch():
    _clear()
    launch = _Rec()
    r = P.revive_cortex(dry_run=True, port_alive=False, stop_reason="", state_exists=True,
                        now=T, launch_fn=launch)
    assert r["launched"] is False and launch.n == 0 and "dry-run" in r["action"], r
    print("  ok dry-run                    -> reports, no launch")


def test_flag_off_no_launch():
    _clear()
    launch = _Rec()
    r = P.revive_cortex(dry_run=False, port_alive=False, stop_reason="", state_exists=True,
                        now=T, launch_fn=launch)
    assert r["launched"] is False and launch.n == 0 and "flag OFF" in r["action"], r
    print("  ok flag OFF + --revive        -> would-revive, no launch")


def test_acts_when_enabled():
    _clear()
    os.environ["OCTOPUS_WIRE_CORTEX_REVIVE"] = "1"
    launch = _Rec(True)
    r = P.revive_cortex(dry_run=False, port_alive=False, stop_reason="", state_exists=True,
                        now=T, launch_fn=launch)
    assert r["launched"] is True and launch.n == 1 and r["action"] == "revived", r
    assert T in P._load_state()["revives"], "revive must be recorded"
    _clear()
    print("  ok flag ON + --revive         -> launches once, records history")


def test_backoff_blocks():
    _clear()
    os.environ["OCTOPUS_WIRE_CORTEX_REVIVE"] = "1"
    P._save_state({"revives": [T - 10], "last_incident": 0})   # 10s ago < 90s min-interval
    launch = _Rec()
    r = P.revive_cortex(dry_run=False, port_alive=False, stop_reason="", state_exists=True,
                        now=T, launch_fn=launch)
    assert launch.n == 0 and "backoff" in r["action"], r
    _clear()
    print("  ok backoff belt               -> refuses relaunch within 90s")


def test_cap_hit_alerts():
    _clear()
    os.environ["OCTOPUS_WIRE_CORTEX_REVIVE"] = "1"
    # 5 revives within the hour, newest 1000s ago (backoff passes, cap trips)
    P._save_state({"revives": [T - 3000, T - 2500, T - 2000, T - 1500, T - 1000],
                   "last_incident": 0})
    launch = _Rec(); inc = _Rec(True)
    r = P.revive_cortex(dry_run=False, port_alive=False, stop_reason="", state_exists=True,
                        now=T, launch_fn=launch, incident_fn=inc)
    assert launch.n == 0 and "cap hit" in r["action"], r
    assert r["alerted"] is True and inc.n == 1, r
    _clear()
    print("  ok restart-cap belt           -> >5/hr refuses + opens incident")


def _run():
    tests = [test_decision_dead, test_decision_alive, test_decision_stop_senior,
             test_decision_never_born, test_dry_run_no_launch, test_flag_off_no_launch,
             test_acts_when_enabled, test_backoff_blocks, test_cap_hit_alerts]
    print("test_cortex_symmetric_revive (M3) — offline, hermetic")
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
