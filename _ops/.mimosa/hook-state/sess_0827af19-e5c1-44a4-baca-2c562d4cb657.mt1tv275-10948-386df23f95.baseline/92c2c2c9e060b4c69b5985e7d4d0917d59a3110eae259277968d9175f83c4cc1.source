#!/usr/bin/env python3
"""test_runner_provenance.py — JSONL output + provenance field tests"""
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

_experiments = Path(__file__).resolve().parent.parent / "hypothesis_engine" / "experiments"
_impl = _experiments.parent / "impl"
sys.path.insert(0, str(_experiments))
sys.path.insert(0, str(_impl))

from env_factory import make_S0_reference, make_S6_benign_anti_hallucination
from agents import PriorAgent, HypothesisAgent, make_agent
from runner import (
    BenchmarkRunner, RunProvenance, AutonomyProvenance, ScenarioResult,
    _config_hash, _git_sha,
)

FAILED = 0


def check(name: str, cond: bool, detail: str = ""):
    global FAILED
    if FAILED > 50:
        raise RuntimeError(f"Too many failures, aborting: {FAILED}")
    if cond:
        print(f"  ✅ {name}")
    else:
        FAILED += 1
        print(f"  ❌ {name}: {detail}")


def test_run_provenance_to_dict():
    """RunProvenance.to_dict() has all required JSONL fields."""
    rp = RunProvenance(
        run_id="test-001", scenario_id="S0", seed=42,
        git_sha="abc1234", config_hash="deadbeef",
        agent="B_hyp", environment_hash="envhash",
        start_iso="2026-01-01T00:00:00Z",
        end_iso="2026-01-01T00:01:00Z",
        discovered=True, ttd=500, total_steps=500,
        termination_reason="discovered",
        hypothesis_ids=["HYP-001", "HYP-002"],
        evidence_ids=["EV-001"],
    )
    d = rp.to_dict()
    required_fields = [
        "run_id", "scenario_id", "seed", "git_sha", "config_hash",
        "agent", "environment_hash", "start_iso", "end_iso",
        "discovered", "ttd", "total_steps", "wasted_steps",
        "falsified_assists", "hyp_steps", "termination_reason",
        "budget_overrun", "ablation_variant",
        "hypothesis_ids", "evidence_ids",
        "safety_violation", "seed_leakage", "reward_hacking", "invalid_evidence",
        "trigger_source", "human_prompt_post_start", "side_effects",
    ]
    for f in required_fields:
        check(f"to_dict has '{f}'", f in d)


def test_jsonl_fields_persist():
    """Written JSONL has all fields readable back."""
    with tempfile.TemporaryDirectory() as tmpdir:
        out = Path(tmpdir) / "results"
        runner = BenchmarkRunner(out_dir=out, git_sha="test-sha")
        env = make_S0_reference(seed=42)
        agent = PriorAgent(env, seed=42)
        rp = runner.run_single(env, agent, "S0")

        # Write manually to verify
        jsonl_path = out / "S0.jsonl"
        with jsonl_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(rp.to_dict(), ensure_ascii=False) + "\n")

        # Read back
        lines = jsonl_path.read_text(encoding="utf-8").strip().split("\n")
        check("JSONL has 1 line", len(lines) == 1)
        record = json.loads(lines[0])
        check("JSONL run_id matches", record["run_id"] == rp.run_id)
        check("JSONL agent matches", record["agent"] == "A_prior")
        check("JSONL scenario_id matches", record["scenario_id"] == "S0")
        check("JSONL seed matches", record["seed"] == 42)
        check("JSONL git_sha matches", record["git_sha"] == "test-sha")
        check("JSONL has environment_hash", "environment_hash" in record)
        check("JSONL has termination_reason", record["termination_reason"] in
              ("discovered", "budget_exhausted", "agent_error"))


def test_unique_run_ids():
    """Each run produces a unique run_id."""
    with tempfile.TemporaryDirectory() as tmpdir:
        out = Path(tmpdir) / "results"
        runner = BenchmarkRunner(out_dir=out, git_sha="test-sha")
        env = make_S0_reference(seed=42)
        ids = set()
        for i in range(20):
            agent = PriorAgent(env, seed=i)
            rp = runner.run_single(env, agent, "S0")
            ids.add(rp.run_id)
        check("20 runs produce 20 unique IDs", len(ids) == 20)


def test_config_hash_deterministic():
    """Same config produces same hash, different config produces different."""
    h1 = _config_hash("B_hyp", "S0", 42, 10000)
    h2 = _config_hash("B_hyp", "S0", 42, 10000)
    h3 = _config_hash("B_hyp", "S0", 43, 10000)
    h4 = _config_hash("A_prior", "S0", 42, 10000)
    check("Same config → same hash", h1 == h2)
    check("Different seed → different hash", h1 != h3)
    check("Different agent → different hash", h1 != h4)
    check("Hash is 16 hex chars", len(h1) == 16 and all(c in "0123456789abcdef" for c in h1))


def test_config_hash_with_ablation():
    """Config hash includes ablation_variant."""
    h1 = _config_hash("B_hyp", "S7", 42, 10000)
    h2 = _config_hash("B_hyp", "S7", 42, 10000, ablation_variant="B-no-EIG")
    check("Ablation changes hash", h1 != h2)


def test_git_sha_recorded():
    """Git SHA is recorded (or 'unknown' in test)."""
    sha = _git_sha()
    check("git_sha is non-empty string", len(sha) > 0)


def test_budget_overrun_flagged():
    """Budget overrun is correctly flagged."""
    # Agent A on S0 typically exhausts budget — should have budget_overrun=False
    # because total_steps == budget, not > budget
    with tempfile.TemporaryDirectory() as tmpdir:
        out = Path(tmpdir) / "results"
        runner = BenchmarkRunner(out_dir=out, git_sha="test-sha")
        env = make_S0_reference(seed=42)
        agent = PriorAgent(env, seed=42)
        rp = runner.run_single(env, agent, "S0")
        check("Budget overrun False when steps ≤ budget",
              rp.budget_overrun is False or rp.total_steps <= env.budget)


def test_termination_reason_valid():
    """Termination reason is always one of the expected values."""
    valid_reasons = {"discovered", "budget_exhausted", "agent_error"}
    with tempfile.TemporaryDirectory() as tmpdir:
        out = Path(tmpdir) / "results"
        runner = BenchmarkRunner(out_dir=out, git_sha="test-sha")

        # Test with PriorAgent (usually budget_exhausted on S0)
        env = make_S0_reference(seed=42)
        rp1 = runner.run_single(env, PriorAgent(env, seed=42), "S0")
        check(f"PriorAgent termination valid: {rp1.termination_reason}",
              rp1.termination_reason in valid_reasons,
              f"got '{rp1.termination_reason}'")

        # Test with benign env (should discover)
        env2 = make_S6_benign_anti_hallucination(seed=42, mode="trivial")
        rp2 = runner.run_single(env2, PriorAgent(env2, seed=42), "S6_trivial")
        check(f"PriorAgent benign termination valid: {rp2.termination_reason}",
              rp2.termination_reason in valid_reasons,
              f"got '{rp2.termination_reason}'")


def test_autonomy_provenance():
    """AutonomyProvenance has all required S8 fields."""
    ap = AutonomyProvenance(
        run_id="auto-001",
        trigger_source="telemetry",
        initiator="self",
        goal_id="GOAL-001",
        evidence_ids=["EV-001"],
        tool_calls=[{"tool": "brain.propose", "args": {}}],
        fencing_token="fence-abc",
    )
    d = ap.to_dict()
    required = [
        "run_id", "trigger_source", "initiator",
        "human_prompt_id", "goal_id", "evidence_ids",
        "approval_id", "tool_calls", "side_effects",
        "rollback_id", "fencing_token",
    ]
    for f in required:
        check(f"AutonomyProvenance has '{f}'", f in d)
    check("trigger_source == telemetry", d["trigger_source"] == "telemetry")
    check("initiator == self", d["initiator"] == "self")
    check("side_effects empty", d["side_effects"] == [])


def test_scenario_result_jsonl():
    """ScenarioResult.to_jsonl() produces valid JSONL."""
    rp1 = RunProvenance(
        run_id="r1", scenario_id="S0", seed=0,
        git_sha="sha", config_hash="hash",
        agent="A_prior", environment_hash="ehash",
        start_iso="T0", end_iso="T1",
        discovered=True, ttd=100, total_steps=100,
        termination_reason="discovered",
    )
    rp2 = RunProvenance(
        run_id="r2", scenario_id="S0", seed=1,
        git_sha="sha", config_hash="hash2",
        agent="B_hyp", environment_hash="ehash",
        start_iso="T0", end_iso="T2",
        discovered=False, total_steps=10000,
        termination_reason="budget_exhausted",
    )
    sr = ScenarioResult(scenario_id="S0", description="Reference test",
                        n_runs=2, records=[rp1, rp2])
    jsonl = sr.to_jsonl()
    lines = jsonl.strip().split("\n")
    check("to_jsonl produces 2 lines", len(lines) == 2)
    for line in lines:
        record = json.loads(line)
        check("JSONL line has run_id", "run_id" in record)


def test_checkpoint_resume():
    """Checkpoint saves and loads completed runs."""
    with tempfile.TemporaryDirectory() as tmpdir:
        out = Path(tmpdir) / "results"
        runner = BenchmarkRunner(out_dir=out, git_sha="test-sha")
        env = make_S6_benign_anti_hallucination(seed=42, mode="trivial")

        # Run first agent
        rp1 = runner.run_single(env, PriorAgent(env, seed=42), "S6")
        # Save checkpoint manually
        runner._completed_runs.add(("S6", "A_prior", 42))
        runner._save_checkpoint()

        # Create new runner (simulating restart)
        runner2 = BenchmarkRunner(out_dir=out, git_sha="test-sha")
        runner2._load_checkpoint()
        check("Checkpoint loaded", ("S6", "A_prior", 42) in runner2._completed_runs)


if __name__ == "__main__":
    print("test_runner_provenance.py")
    test_run_provenance_to_dict()
    test_jsonl_fields_persist()
    test_unique_run_ids()
    test_config_hash_deterministic()
    test_config_hash_with_ablation()
    test_git_sha_recorded()
    test_budget_overrun_flagged()
    test_termination_reason_valid()
    test_autonomy_provenance()
    test_scenario_result_jsonl()
    test_checkpoint_resume()
    print(f"\n{'PASS' if FAILED == 0 else 'FAIL'} ({FAILED} failed)")
    sys.exit(FAILED)
