#!/usr/bin/env python3
"""Offline, hermetic test for M7 (now_moves/route_scorer_shadow_log).

Stdlib-only · no network · shadow log isolated to a tmp OPS_DIR. Uses the REAL
route_scorer to verify a shadow record is written with the right shape, a valid
scorer-tier, correct agree logic, and a readable summary — all WITHOUT changing
routing. Standalone (exit 0/1) per run_all.py.
"""
import os
import sys
import tempfile
from pathlib import Path

_TMP = tempfile.mkdtemp(prefix="m7_route_")
os.environ["ORG_ROOT"] = _TMP
os.environ["OPS_DIR"] = str(Path(_TMP) / "_ops")
os.environ.pop("OCTOPUS_WIRE_ROUTE_SHADOW", None)

HERE = Path(__file__).resolve().parent
OPS = HERE.parent
for _p in (str(OPS / "now_moves"), str(OPS / "cortex"), str(OPS / "budget"), str(OPS)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import route_scorer_shadow_log as P                        # noqa: E402

_TIERS = (None, "local", "secondary", "primary")


def test_log_writes_record():
    rec = P.log_decision("classify", "local")
    assert rec is not None, rec
    assert set(rec) >= {"task", "dict_tier", "scorer_tier", "agree"}, rec
    assert rec["dict_tier"] == "local" and rec["task"] == "classify", rec
    p = P._log_path()
    assert p and p.exists() and len(p.read_text("utf-8").splitlines()) >= 1
    print("  ok log_decision          -> one shadow record written to jsonl")


def test_scorer_tier_valid():
    rec = P.log_decision("orchestrate a complex risky migration", "primary")
    assert rec["scorer_tier"] in _TIERS, rec
    print("  ok scorer tier           -> valid tier from real route_scorer")


def test_agree_logic():
    rec = P.log_decision("classify", "local")
    assert rec["agree"] == (rec["scorer_tier"] is not None and rec["scorer_tier"] == "local"), rec
    print("  ok agree flag            -> True iff scorer_tier == dict_tier")


def test_summary_reads():
    P.log_decision("t1", "local")
    P.log_decision("t2", "primary")
    s = P.summary()
    assert s["n"] >= 2 and isinstance(s["agree_pct"], float), s
    print("  ok summary               -> agreement rate over recent records")


def test_failsoft_never_raises():
    rec = P.log_decision("", "local")             # bizarre input must not raise
    assert rec is None or "agree" in rec
    print("  ok fail-soft             -> never raises, never blocks ask()")


def _run():
    tests = [test_log_writes_record, test_scorer_tier_valid, test_agree_logic,
             test_summary_reads, test_failsoft_never_raises]
    print("test_route_scorer_shadow_log (M7) — offline, hermetic")
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
