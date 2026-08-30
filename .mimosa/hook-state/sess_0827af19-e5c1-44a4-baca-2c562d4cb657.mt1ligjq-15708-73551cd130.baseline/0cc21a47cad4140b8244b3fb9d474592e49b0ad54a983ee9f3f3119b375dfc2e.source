# -*- coding: utf-8 -*-
"""Nervous recovery unit tests — registered in run_all.py (owner 2026-08-20)."""
import json
import sys
import tempfile
from pathlib import Path

_OPS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_OPS))

from nervous_recovery import (  # noqa: E402
    canary_restart,
    capability_immune,
    capability_parser,
    memory_continuity,
    reality_ledger,
    receipt_v2,
    repair_planner,
    shadow_adapter,
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
    # Callable sensors without receipts are DECLARED_UNOBSERVED, not DORMANT.
    assert inv["counts"]["DECLARED_UNOBSERVED"] >= 1
    dead = capability_immune.card("x", {"status": "dead-output", "actuator": None},
                                  observed_recently=False, receipt_backed=False)
    assert dead["truth_status"] == "DORMANT"
    observed = capability_immune.card(
        "z", {"status": "wired", "actuator": "foo"},
        observed_recently=False, receipt_backed=False)
    assert observed["truth_status"] == "DECLARED_UNOBSERVED"
    live = capability_immune.card("y", {"status": "wired", "actuator": "foo"},
                                  observed_recently=True, receipt_backed=True,
                                  tested=True)
    assert live["truth_status"] == "VERIFIED"
    incomplete = capability_immune.card(
        "y", {"status": "wired", "actuator": "foo"},
        observed_recently=True, receipt_backed=True, tested=False)
    assert incomplete["truth_status"] == "DEGRADED"


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
    gapped = [
        {"memory_reads_per_cycle": 3, "readback": "read_ok", "status": "OK",
         "executable": False, "beat": 10},
        {"memory_reads_per_cycle": 3, "readback": "read_ok", "status": "OK",
         "executable": False, "beat": 12},
    ]
    assert memory_continuity.consecutive_healthy(gapped) == 2
    dup = [gapped[1], gapped[1]]
    assert memory_continuity.consecutive_healthy(dup) == 1
    aud = memory_continuity.audit(samples[0], None)
    assert aud["gate_met"] is False  # single sample < 10
    assert "Wave 1" in aud["note"]


def test_memory_ten_observed_ticks_meet_gate():
    d = Path(tempfile.mkdtemp()) / "mem.jsonl"
    rows = []
    for i in range(10):
        rows.append({
            "memory_reads_per_cycle": 3,
            "readback": "read_ok",
            "status": "OK",
            "executable": False,
            "beat": 100 + i * 2,
            "observed_at": f"2026-08-20T12:{i:02d}:00+00:00",
        })
    d.write_text("\n".join(json.dumps(r) for r in rows) + "\n", encoding="utf-8")
    aud = memory_continuity.audit(rows[-1], d)
    assert aud["gate_met"] is True
    assert aud["consecutive_healthy"] == 10
    assert aud["unique_cycle_identities"] is True
    assert all(r.startswith("memory-obs:") for r in aud["trailing_cycle_receipts"])


def test_verifier_never_unlocks_wave1():
    from nervous_recovery import wave0_verifier
    rep = wave0_verifier.verify()
    assert rep["wave1_unlocked"] is False
    names = {c["name"]: c["ok"] for c in rep["checks"]}
    assert names["wave1_unlocked_live"] is True
    assert names["canary_execute_false"] is True


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


def test_shadow_does_not_rewrite_source_and_never_guesses():
    d = Path(tempfile.mkdtemp())
    src = d / "orig.jsonl"
    dest = d / "shadow.jsonl"
    rows = [
        {"task_id": "tsk_real", "run_id": "run_a", "trace_id": "t1",
         "created_at": "2026-08-20T12:00:00Z", "process_id": 99999},
        {"task_id": "", "run_id": "run_unknown", "trace_id": "t2",
         "created_at": "2026-08-20T12:01:00Z", "process_id": 111},
        {"task_id": "", "run_id": "run_ctx", "trace_id": "t3",
         "created_at": "2026-08-20T12:02:00Z"},
    ]
    src.write_text("\n".join(json.dumps(r) for r in rows) + "\n", encoding="utf-8")
    before = src.read_bytes()
    rep = shadow_adapter.scan_to_shadow(
        src, dest, since_iso="2026-08-20",
        run_to_task={"run_ctx": "tsk_from_map"})
    after = src.read_bytes()
    assert before == after
    assert src.read_text(encoding="utf-8").count("task_id") >= 1
    assert dest.exists()
    shadows = [json.loads(x) for x in dest.read_text(encoding="utf-8").splitlines() if x.strip()]
    assert len(shadows) == 3
    assert shadows[0]["task_id"] == "tsk_real" and shadows[0]["task_id_source"] == "caller"
    assert shadows[1]["task_id"] is None and shadows[1]["attribution_status"] == "unresolved"
    assert shadows[1]["task_id_source"] == "legacy_missing"
    assert shadows[2]["task_id"] == "tsk_from_map" and shadows[2]["task_id_source"] == "context"
    assert all(s["original_receipt_hash"] for s in shadows)
    assert all(s["adapter_version"] == "v2" for s in shadows)
    assert "99999" not in str(shadows[1].get("task_id"))
    assert rep["criteria"]["duplicate_receipts"] == 0
    assert rep["criteria"]["fabricated_task_ids"] == 0
    assert rep["criteria"]["schema_validation"] == 1.0
    assert rep["criteria"]["original_receipt_hash_coverage"] == 1.0
    assert rep["shadow_pass"] is True
    # second pass is idempotent on hash, source still untouched
    rep2 = shadow_adapter.scan_to_shadow(
        src, dest, since_iso="2026-08-20",
        run_to_task={"run_ctx": "tsk_from_map"})
    assert before == src.read_bytes()
    assert rep2["n_written"] == 0
    assert rep2["n_skipped_duplicate_hash"] == 3


def test_shadow_pid_timestamp_capability_are_not_task_ids():
    env = shadow_adapter.shadow_one({
        "process_id": 43210,
        "created_at": "2026-08-20T00:00:00Z",
        "capability_id": "model.call.paid",
        "exact_model": "glm-5.3",
    })
    assert env["task_id"] is None
    assert env["attribution_status"] == "unresolved"
    assert env["task_id_source"] == "legacy_missing"


def test_task_context_never_infers():
    from nervous_recovery import task_context
    r = task_context.resolve(caller_task="", run_id="", environ={})
    assert r["task_id"] is None and r["attribution_status"] == "unresolved"
    r2 = task_context.resolve(caller_task="think", run_id="run_1", environ={})
    assert r2["task_id"] == "think" and r2["task_id_source"] == "caller"
    r3 = task_context.resolve(
        caller_task="", run_id="run_x",
        environ={"OCTOPUS_TASK_ID": "tsk_env", "OCTOPUS_RUN_ID": "run_x"})
    assert r3["task_id"] == "tsk_env" and r3["task_id_source"] == "context"
    r4 = task_context.resolve(
        caller_task="", run_id="run_other",
        environ={"OCTOPUS_TASK_ID": "tsk_env", "OCTOPUS_RUN_ID": "run_x"})
    assert r4["task_id"] is None  # foreign run — do not bind


def test_canary_execute_is_false_and_order_is_cortex_only():
    assert canary_restart.EXECUTE is False
    assert canary_restart.canary_order() == ["cortex"]
    pl = canary_restart.plan()
    assert pl["execute"] is False
    assert pl["wave1_unlocked"] is False
    assert "paid_call_or_actuator_or_wave_state_change" in pl["stop"]


def test_run_all_registers_this_file():
    names = test_discovery.registered_from_run_all()
    assert "test_nervous_recovery.py" in names


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
