#!/usr/bin/env python3
"""Focused DARK inventory contracts on synthetic and real scanner output."""
from __future__ import annotations

import json
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_OPS = _HERE.parent
for _p in (_OPS, _OPS / "budget"):
    sys.path.insert(0, str(_p))

import harness  # noqa: E402
harness.setup("ti-dark-inventory")

import dark_capabilities as dc  # noqa: E402
from test_intelligence.dark_inventory import FOCUS_FLAGS, focused_rows, inventory  # noqa: E402


def t_a_missing_focus_flag_is_unknown_not_dark():
    result = {"live_source": "absent", "processes": [], "rows": []}
    row = focused_rows(result, ["OCTOPUS_WIRE_NOT_PRESENT"])[0]
    assert row["classification"] == "UNKNOWN"
    assert row["reason"] == "not-found-by-static-scanner"


def t_b_absent_live_source_is_structural_only():
    result = {
        "live_source": "absent", "processes": [],
        "rows": [{"flag": "OCTOPUS_WIRE_COLLAB", "state": "DARK",
                  "armed_in_file": False, "profile_on": False,
                  "n_readers": 2, "readers": ["a.py", "b.py"]}],
    }
    row = focused_rows(result, ["OCTOPUS_WIRE_COLLAB"])[0]
    assert row["classification"] == "DARK"
    assert row["live_confidence"] == "STRUCTURAL_ONLY"
    assert row["tracked_or_profile_on"] is False


def t_c_tuning_remains_distinct_from_dark():
    result = {
        "live_source": "live", "processes": ["center"],
        "rows": [{"flag": "CORTEX_ROUTE_SCORER", "state": "TUNING",
                  "armed_in_file": False, "profile_on": False,
                  "n_readers": 1, "readers": ["cortex/model_router.py"]}],
    }
    row = focused_rows(result, ["CORTEX_ROUTE_SCORER"])[0]
    assert row["classification"] == "TUNING"
    assert row["live_confidence"] == "HIGH"


def t_d_real_inventory_has_expected_counts_and_no_values():
    result = dc.scan(_OPS)
    artifact = inventory(result)
    summary = artifact["summary"]
    assert summary["n_flags"] > 0
    assert summary["n_dark"] >= 0
    assert summary["n_tuning"] >= 0
    assert len(artifact["focus"]) == len(FOCUS_FLAGS)
    assert {row["flag"] for row in artifact["focus"]} == set(FOCUS_FLAGS)
    raw = json.dumps(artifact, ensure_ascii=False, sort_keys=True)
    assert "super-secret-value" not in raw
    assert all("value" not in row for row in artifact["focus"])


if __name__ == "__main__":
    checks = [(n, f) for n, f in sorted(globals().items()) if n.startswith("t_")]
    failed = harness.run(checks)
    print(f"\n{'OK' if not failed else 'FAIL'} test_ti_dark_inventory: "
          f"{len(checks) - failed}/{len(checks)}")
    sys.exit(1 if failed else 0)
