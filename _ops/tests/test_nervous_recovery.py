# -*- coding: utf-8 -*-
"""Nervous recovery unit tests — isolated; not registered in run_all.py (WORKLOCK)."""
import json
import sys
import tempfile
from pathlib import Path

_OPS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_OPS))

from nervous_recovery import (  # noqa: E402
    capability_immune,
    capability_parser,
    memory_continuity,
    reality_ledger,
    receipt_v2,
    repair_planner,
    test_discovery,
    wave0_governor,
)


def test_ledger_dedupe_and_no_fake_resolve():
    d = Path(tempfile.mkdtemp()) / "ledger.jsonl"
    lg = reality_ledger.RealityLedger(d)
    ev = [{"type": "file", "ref": "x", "hash": "abc"}]
    r1 = lg.append({"kind": "finding", "finding_id": "S-B01", "status": "candidate",
                    "evidence": ev, "confidence": 0.9})
    r2 = lg.append({"kind": "finding", "finding_id": "S-B01", "status": "candidate",
                    "evidence": ev, "confidence": 0.9})
    assert r1["appended"] is True
    assert r2["appended"] is False and r2["reason"] == "duplicate"


def test_receipt_never_fabricates_task_id():
    env = receipt_v2.adapt_legacy({"trace_id": "t1", "run_id": ""})
    assert env["task_id"] == ""
    assert env["outcome"] == "unattributed"
    assert env["schema_version"] == 2
    env2 = receipt_v2.adapt_legacy({"task_id": "tsk_a", "run_id": "run_a", "status": "ok"})
    assert env2["outcome"] == "ok" and env2["task_id"] == "tsk_a"
    env3 = receipt_v2.adapt_legacy({"run_id": "run_x"}, run_to_task={"run_x": "tsk_from_ctx"})
    assert env3["task_id"] == "tsk_from_ctx"
    env4 = receipt_v2.adapt_legacy({"run_id": "run_unknown"}, run_to_task={})
    assert env4["task_id"] == "" and env4["outcome"] == "unattributed"


def test_discovery_fixture_ci_predicate():
    root = Path(tempfile.mkdtemp())
    tests = root / "tests"
    tests.mkdir()
    (tests / "test_alpha.py").write_text("# a\n", encoding="utf-8")
    (tests / "test_beta.py").write_text("# b\n", encoding="utf-8")
    run_all = tests / "run_all.py"
    run_all.write_text('TESTS = ["test_alpha.py"]\nEXTRA_TESTS = []\nPYTEST_TESTS = set()\n',
                       encoding="utf-8")
    rep = test_discovery.report(tests_dir=tests, run_all=run_all)
    assert rep["discovered"] == 2 and rep["registered"] == 1 and rep["gap"] == 1
    assert test_discovery.gap_is_ci_failure(rep["gap"]) is True
    assert test_discovery.gap_is_ci_failure(0) is False


def test_effectors_ast_parse_nonzero():
    caps = capability_parser.parse_effectors_py(_OPS / "effector_registry.py")
    assert isinstance(caps, dict) and len(caps) > 0
    assert "bcm.learned_pressure" in caps
    inv = capability_immune.inventory(caps, observed_recently=False, receipt_backed=False)
    assert inv["parse_ok"] is True and inv["total"] == len(caps)
    assert inv["counts"]["VERIFIED"] == 0  # no receipts → not VERIFIED
    dead = capability_immune.card("x", {"status": "dead-output", "actuator": None},
                                  observed_recently=False, receipt_backed=False)
    assert dead["truth_status"] == "BLOCKED"
    live = capability_immune.card("y", {"status": "wired", "actuator": "foo"},
                                  observed_recently=True, receipt_backed=True)
    assert live["truth_status"] == "VERIFIED"


def test_yaml_json_parsers():
    d = Path(tempfile.mkdtemp())
    (d / "c.json").write_text(json.dumps({"capabilities": {"mem.read": {"actuator": None}}}),
                              encoding="utf-8")
    js = capability_parser.parse_capability_file(d / "c.json")
    assert "mem.read" in js


def test_memory_continuity_is_streak_not_sum():
    samples = [
        {"memory_reads_per_cycle": 3, "readback": "read_ok", "status": "OK", "executable": False},
        {"memory_reads_per_cycle": 0, "readback": "read_ok", "status": "OK", "executable": False},
        {"memory_reads_per_cycle": 3, "readback": "read_ok", "status": "OK", "executable": False},
    ]
    assert memory_continuity.consecutive_healthy(samples) == 1
    ten = [samples[0]] * 10
    assert memory_continuity.consecutive_healthy(ten) == 10
    aud = memory_continuity.audit(samples[0], None)
    assert aud["gate_met"] is False  # single sample < 10
    assert "Wave 1" in aud["note"]


def test_governor_does_not_unlock_wave1():
    rep = wave0_governor.audit_wave0()
    assert rep["wave1_unlocked"] is False
    assert rep["verdict"] in (
        wave0_governor.Wave0Verdict.PASS,
        wave0_governor.Wave0Verdict.PARTIAL,
        wave0_governor.Wave0Verdict.BLOCKED,
    )
    assert rep["gates"]["capability_inventory"]["pass"] is True
    dag = repair_planner.dag()
    assert dag["applies_patches"] is False
    assert dag["wave1_unlocked"] is False


def test_ledger_resolved_requires_evidence():
    d = Path(tempfile.mkdtemp()) / "l.jsonl"
    lg = reality_ledger.RealityLedger(d)
    try:
        lg.append({"kind": "verification", "finding_id": "X", "status": "resolved",
                   "evidence": []})
        raise AssertionError("should have failed")
    except ValueError:
        pass


if __name__ == "__main__":
    tests = [v for k, v in list(globals().items()) if k.startswith("test_") and callable(v)]
    failed = 0
    for fn in tests:
        try:
            fn()
            print("PASS", fn.__name__)
        except Exception as e:
            failed += 1
            print("FAIL", fn.__name__, type(e).__name__, e)
    if failed:
        raise SystemExit(1)
    print(f"{len(tests)} passed")
