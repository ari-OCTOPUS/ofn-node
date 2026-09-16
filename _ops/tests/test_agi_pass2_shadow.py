#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Pass 2 SHADOW pins. Not registered in run_all.py. No live send. No Wave 1 unlock."""
from __future__ import annotations

import ast
import inspect
import sys
from pathlib import Path

_OPS = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_OPS))
sys.path.insert(0, str(_OPS / "cortex"))
sys.path.insert(0, str(_OPS / "budget"))

import importlib  # noqa: E402
import harness  # noqa: E402
harness.setup("agi-pass2-shadow")

import improve  # noqa: E402
importlib.reload(improve)
from loops import pass2_shadow  # noqa: E402


def t_improve_emits_calibration_proposal():
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
    assert cal, [p.get("source") for p in props[:8]]
    assert cal[0].get("auto_applicable") is False
    assert "calibration-latest.json" in inspect.getsource(improve.gather_signals)


def t_self_knowledge_has_no_confidence_assign_0_4():
    src = (_OPS / "doctor" / "self_knowledge.py").read_text(encoding="utf-8")
    tree = ast.parse(src)
    hits = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            targets = [a.id for a in node.targets if isinstance(a, ast.Name)]
            if "confidence" in targets and isinstance(node.value, ast.Constant):
                if node.value.value == 0.4:
                    hits.append(node.lineno)
        if isinstance(node, ast.Dict):
            for k, v in zip(node.keys, node.values):
                if isinstance(k, ast.Constant) and k.value == "confidence":
                    if isinstance(v, ast.Constant) and v.value == 0.4:
                        hits.append(getattr(v, "lineno", 0))
    assert not hits, f"hardcoded 0.4 at lines {hits}"
    assert "_accuracy_ema" in src


def t_pass2_shadow_bundle():
    r = pass2_shadow.run()
    assert "wave1_unlocked" in r
    assert r["S-A03_calibration_in_improve"] is True
    assert r["S-A01_ema_present"] is True
    assert r["S-A01_literal_0_4_assign"] is False
    assert (r.get("S-D01_doctor_copy") or {}).get("live_written") is False
    assert (r.get("S-T03_outbox_digest") or {}).get("ok") is True
    assert r["live_telegram"] is False
    assert r["paid_calls"] in ("NOT_GRANTED", "BUDGETED")


if __name__ == "__main__":
    failed = 0
    for n, f in sorted((n, f) for n, f in globals().items() if n.startswith("t_")):
        try:
            f(); print(f"  OK  {n}")
        except Exception as e:
            failed += 1
            print(f"  FAIL {n}: {type(e).__name__}: {e}")
    sys.exit(1 if failed else 0)
