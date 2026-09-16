#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""S-A03: improve must consume calibration-latest (propose-only, never auto)."""
import inspect
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
for _p in (str(_HERE.parent), str(_HERE.parent / "cortex"), str(_HERE.parent / "budget")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import harness  # noqa: E402
harness.setup("improve-calibration")
import improve  # noqa: E402


def t_a_generate_proposals_emits_calibration():
    signals = {
        "matrix": {"gaps": []},
        "doctor_rfcs": [],
        "smallest_fix": "",
        "synthesis": {},
        "idea": {},
        "calibration": {"n": 12, "brier": 0.21, "ungraded": 3, "ts": "t"},
    }
    props = improve.generate_proposals(signals)
    cal = [p for p in props if p.get("source") == "calibration"]
    assert cal, {"n": len(props), "sources": [p.get("source") for p in props[:8]]}
    assert cal[0].get("auto_applicable") is False
    assert cal[0].get("change_level") == "tune"
    assert "calibration-latest.json" in str(cal[0].get("evidence"))


def t_b_source_reads_calibration_latest():
    assert "calibration-latest.json" in inspect.getsource(improve.gather_signals)
    assert "calibration" in inspect.getsource(improve.generate_proposals)


if __name__ == "__main__":
    failed = 0
    for name, fn in sorted((n, f) for n, f in globals().items() if n.startswith("t_")):
        try:
            fn()
            print(f"  OK  {name}")
        except Exception as e:
            failed += 1
            print(f"  FAIL {name}: {type(e).__name__}: {e}")
    print(f"\ntest_improve_reads_calibration: {2 - failed}/2")
    sys.exit(1 if failed else 0)
