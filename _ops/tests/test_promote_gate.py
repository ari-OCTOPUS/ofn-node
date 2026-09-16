#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Promote/merge gate: refuse without test pass + evidence + rollback plan."""
from __future__ import annotations

import importlib
import json
import os
import sys
import tempfile
from pathlib import Path

_OPS = Path(__file__).resolve().parents[1]
_DOC = _OPS / "doctor"
for _p in (str(_OPS), str(_DOC)):
    if _p not in sys.path:
        sys.path.insert(0, _p)


def t_a_gate_refuses_missing_proofs():
    from self_upgrade_lab import promoter
    promoter = importlib.reload(promoter)
    g = promoter.gate_promote(test_ok=False, evidence_path=None, rollback_plan=None)
    assert g["ok"] is False
    assert "test-not-pass" in g["reasons"]
    assert "missing-evidence-path" in g["reasons"]
    assert "missing-rollback-plan" in g["reasons"]


def t_b_gate_refuses_missing_evidence_file():
    from self_upgrade_lab import promoter
    promoter = importlib.reload(promoter)
    g = promoter.gate_promote(
        test_ok=True,
        evidence_path=str(Path(tempfile.gettempdir()) / "no-such-evo-evidence.json"),
        rollback_plan={"plan": "git checkout -- files"},
    )
    assert g["ok"] is False
    assert "evidence-path-missing-file" in g["reasons"]


def t_c_gate_allows_when_all_present():
    from self_upgrade_lab import promoter
    promoter = importlib.reload(promoter)
    root = Path(tempfile.mkdtemp(prefix="promote-gate-"))
    ev = root / "evidence.json"
    ev.write_text("{}", encoding="utf-8")
    g = promoter.gate_promote(
        test_ok=True,
        evidence_path=str(ev),
        rollback_plan={"plan": "git checkout -- allowlist", "tag": "pre-merge/x"},
    )
    assert g["ok"] is True
    assert g["reasons"] == []


def t_d_promote_refuses_without_gate():
    from self_upgrade_lab import promoter
    promoter = importlib.reload(promoter)
    os.environ["OCTOPUS_SUL_STATE_DIR"] = str(Path(tempfile.mkdtemp(prefix="sul-promo-")))
    # force STATE_DIR via env if contracts use it — promotions append uses module STATE_DIR
    out = promoter.promote(
        experiment_id="exp-gate-refuse",
        verifier={"confirmed": True},
        test_ok=False,
        evidence_path=None,
        rollback_plan=None,
    )
    assert out.get("refused") is True
    assert out.get("level") == "NONE"
    assert out.get("production") is False
    assert "test-not-pass" in (out.get("gate") or {}).get("reasons", [])


def t_e_promote_allows_lab_pass_with_proofs():
    from self_upgrade_lab import promoter
    promoter = importlib.reload(promoter)
    root = Path(tempfile.mkdtemp(prefix="promote-ok-"))
    ev = root / "evidence.json"
    ev.write_text(json.dumps({"ok": True}), encoding="utf-8")
    out = promoter.promote(
        experiment_id="exp-gate-ok",
        verifier={"confirmed": True},
        test_ok=True,
        evidence_path=str(ev),
        rollback_plan={"plan": "git checkout -- files", "worktree_only": True},
    )
    assert out.get("refused") is False
    assert out.get("level") == "LAB_PASS"
    assert out.get("production") is False


def t_f_lab_bridge_gate_merge_wires_promoter():
    import lab_bridge
    lab_bridge = importlib.reload(lab_bridge)
    g = lab_bridge.gate_merge(test_ok=False, evidence_path=None, rollback_plan=None)
    assert g["ok"] is False
    r = lab_bridge.refuse_merge_without_proofs(
        test_ok=False, evidence_path=None, rollback_plan=None)
    assert r["allowed"] is False
    assert r["live_promote"] is False


def main() -> int:
    tests = [v for k, v in sorted(globals().items()) if k.startswith("t_") and callable(v)]
    failed = []
    for fn in tests:
        try:
            fn()
            print("  OK  " + fn.__name__)
        except Exception as exc:
            failed.append(fn.__name__)
            print("  FAIL " + fn.__name__ + ": " + type(exc).__name__ + ": " + str(exc))
    print("\ntest_promote_gate: %d/%d" % (len(tests) - len(failed), len(tests)))
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
