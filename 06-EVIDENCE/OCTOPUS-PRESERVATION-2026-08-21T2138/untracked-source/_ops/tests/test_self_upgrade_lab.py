#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Lab unit tests: priority score, secret scan, splice allowlist. Not registered in run_all."""
from __future__ import annotations

import sys
from pathlib import Path

_OPS = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_OPS))

from self_upgrade_lab.contracts import priority_score, secret_scan  # noqa: E402


def t_score_memory_outranks_low_severity():
    mem = priority_score(severity=9, user_impact=9, evidence_confidence=0.95,
                         repairability=0.9, dependency_value=9,
                         estimated_risk=1.2, estimated_runtime=1.0)
    low = priority_score(severity=2, user_impact=2, evidence_confidence=0.4,
                         repairability=0.3, dependency_value=2,
                         estimated_risk=3.0, estimated_runtime=4.0)
    assert mem > low, (mem, low)
    assert mem > 100


def t_secret_scan_names_only():
    hits = secret_scan("the api_key field must be rejected")
    assert "api_key" in hits


if __name__ == "__main__":
    failed = 0
    for n, f in sorted((n, f) for n, f in globals().items() if n.startswith("t_")):
        try:
            f(); print(f"  OK  {n}")
        except Exception as e:
            failed += 1
            print(f"  FAIL {n}: {e}")
    sys.exit(1 if failed else 0)
