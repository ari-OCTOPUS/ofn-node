#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""W8: improve must consume MemoryContext hold_and_revise (propose-only)."""
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
for _p in (str(_HERE.parent), str(_HERE.parent / "cortex"), str(_HERE.parent / "budget")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import harness  # noqa: E402
harness.setup("improve-memory-context")
import improve  # noqa: E402


def test_hold_and_revise_emits_propose_only_card():
    signals = {
        "matrix": {"gaps": []},
        "doctor_rfcs": [],
        "smallest_fix": "",
        "synthesis": {},
        "idea": {},
        "memory_context": {
            "decision": {
                "action": "hold_and_revise",
                "reason": "prior_failure",
                "context_id": "mctx-testfixture",
            }
        },
    }
    props = improve.generate_proposals(signals)
    hit = [p for p in props if p.get("source") == "memory_context"]
    assert hit, {"sources": [p.get("source") for p in props[:12]]}
    assert hit[0].get("auto_applicable") is False
    assert hit[0].get("memory_context_id") == "mctx-testfixture"
