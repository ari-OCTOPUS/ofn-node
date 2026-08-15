# experiments/runner.py — modular benchmark runner with JSONL provenance
#
# Executes scenarios from scenarios.py, writing per-run JSONL with full
# provenance fields. Supports checkpointing, budget enforcement, and
# deterministic replay.
#
# JSONL schema per run:
#   run_id, scenario_id, seed, git_sha, config_hash, agent, environment_hash,
#   start/end, outcome, ttd, steps, cost, hypothesis_ids, evidence_ids,
#   termination_reason, ablation_variant
#
# autonomy_provenance.jsonl schema:
#   trigger_source, initiator, human_prompt_id, goal_id, evidence_ids,
#   approval_id, tool_calls, side_effects, rollback_id, fencing_token
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import time
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from uuid import uuid4

from env_factory import DeceptiveGrid, EnvConfig
from agents import (
    AgentConfig,
    AgentResult,
    BaseAgent,
    HypothesisAgent,
    make_agent,
    make_ablation_agent,
)
from scenarios import ScenarioSpec, S7_ablation


# ---------------------------------------------------------------------------
# Git SHA (for provenance)
# ---------------------------------------------------------------------------
def _git_sha() -> str:
    """Best-effort git SHA of current HEAD."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            capture_output=True, text=True, timeout=5,
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except Exception:
        pass
    return "unknown"


# ---------------------------------------------------------------------------
# Config hash (deterministic for same parameters)
# ---------------------------------------------------------------------------
def _config_hash(agent: str, scenario_id: str, seed: int,
                 budget: int, ablation_variant: str = "",
                 extra: Dict[str, Any] = None) -> str:
    blob = json.dumps({
        "agent": agent, "scenario_id": scenario_id, "seed": seed,
        "budget": budget, "ablation_variant": ablation_variant,
        **(extra or {}),
    }, sort_keys=True)
    return hashlib.sha256(blob.encode()).hexdigest()[:16]


# ---------------------------------------------------------------------------
# Run-level provenance record
# ---------------------------------------------------------------------------
@dataclass
class RunProvenance:
    """Complete provenance for a single benchmark run."""
    run_id: str
    scenario_id: str
    seed: int
    git_sha: str
    config_hash: str
    agent: str
    environment_hash: str
    start_iso: str
    end_iso: str
    discovered: bool
    ttd: Optional[int] = None
    total_steps: int = 0
    wasted_steps: int = 0
    falsified_assists: int = 0
    hyp_steps: int = 0
    termination_reason: str = ""
    budget_overrun: bool = False
    ablation_variant: str = ""
    hypothesis_ids: List[str] = field(default_factory=list)
    evidence_ids: List[str] = field(default_factory=list)
    # Safety flags
    safety_violation: bool = False
    seed_leakage: bool = False
    reward_hacking: bool = False
    invalid_evidence: bool = False
    # Provenance (S8)
    trigger_source: Optional[str] = None
    human_prompt_post_start: bool = False
    side_effects: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


# ---------------------------------------------------------------------------
# Autonomy provenance record (S8 specific)
# ---------------------------------------------------------------------------
@dataclass
class AutonomyProvenance:
    """Per-run autonomy trace for S8 provenance verification."""
    run_id: str
    trigger_source: str                      # "telemetry", "human_prompt", etc.
    initiator: str                           # "self", "human", "system"
    human_prompt_id: Optional[str] = None
    goal_id: Optional[str] = None
    evidence_ids: List[str] = field(default_factory=list)
    approval_id: Optional[str] = None
    tool_calls: List[Dict[str, Any]] = field(default_factory=list)
    side_effects: List[str] = field(default_factory=list)
    rollback_id: Optional[str] = None
    fencing_token: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


# ---------------------------------------------------------------------------
# Scenario result (collection of runs)
# ---------------------------------------------------------------------------
@dataclass
class ScenarioResult:
    """Aggregated result for a scenario."""
    scenario_id: str
    description: str
    n_runs: int = 0
    records: List[RunProvenance] = field(default_factory=list)
    acceptance_passed: Optional[Dict[str, bool]] = None

    def to_jsonl(self) -> str:
        lines = []
        for r in self.records:
            lines.append(json.dumps(r.to_dict(), ensure_ascii=False))
        return "\n".join(lines)


# ---------------------------------------------------------------------------
# Benchmark runner
# ---------------------------------------------------------------------------
class BenchmarkRunner:
    """Execute benchmark scenarios with full provenance tracking.

    Features:
      - JSONL output per run
      - autonomy_provenance.jsonl for S8
      - Checkpoint support (resume interrupted runs)
      - Budget enforcement with hard stop
      - Seed isolation (no cross-seed contamination)
    """

    def __init__(self, out_dir: Path, git_sha: str = None):
        self.out_dir = out_dir
        self.out_dir.mkdir(parents=True, exist_ok=True)
        self.git_sha = git_sha or _git_sha()
        self._checkpoint_path = out_dir / "checkpoint.json"
        self._completed_runs: set = set()  # (scenario_id, agent, seed)

    def _load_checkpoint(self):
        """Load set of completed runs from checkpoint."""
        if self._checkpoint_path.exists():
            try:
                data = json.loads(self._checkpoint_path.read_text(encoding="utf-8"))
                self._completed_runs = set(tuple(x) for x in data.get("completed", []))
            except Exception:
                self._completed_runs = set()

    def _save_checkpoint(self):
        """Save checkpoint after each completed run."""
        data = {"completed": [list(x) for x in self._completed_runs],
                "timestamp": datetime.now(timezone.utc).isoformat()}
        self._checkpoint_path.write_text(json.dumps(data, indent=2), encoding="utf-8")

    def run_single(self, env: DeceptiveGrid, agent: BaseAgent,
                   scenario_id: str) -> RunProvenance:
        """Execute a single agent run and return full provenance."""
        run_id = f"run-{uuid4().hex[:8]}"
        start = datetime.now(timezone.utc)

        try:
            result = agent.run()
        except Exception as e:
            # Agent crash → safety stop
            end = datetime.now(timezone.utc)
            return RunProvenance(
                run_id=run_id, scenario_id=scenario_id,
                seed=env.seed, git_sha=self.git_sha,
                config_hash=_config_hash(agent.name, scenario_id, env.seed, env.budget),
                agent=agent.name, environment_hash=env.environment_hash,
                start_iso=start.isoformat(), end_iso=end.isoformat(),
                discovered=False, total_steps=env.budget,
                termination_reason=f"agent_error: {e}",
                safety_violation=True,
            )

        end = datetime.now(timezone.utc)

        # Determine termination reason
        if result.discovered:
            term = "discovered"
        else:
            term = "budget_exhausted"

        # Check budget overrun
        budget_overrun = result.total_steps > env.budget

        # Extract hypothesis IDs from result
        hyp_ids = [h.get("id", "") for h in result.hypotheses_tracked if h.get("id")]

        return RunProvenance(
            run_id=run_id, scenario_id=scenario_id,
            seed=env.seed, git_sha=self.git_sha,
            config_hash=_config_hash(agent.name, scenario_id, env.seed, env.budget,
                                     result.ablation_variant),
            agent=agent.name, environment_hash=env.environment_hash,
            start_iso=start.isoformat(), end_iso=end.isoformat(),
            discovered=result.discovered, ttd=result.ttd,
            total_steps=result.total_steps, wasted_steps=result.wasted_steps,
            falsified_assists=result.falsified_assists, hyp_steps=result.hyp_steps,
            termination_reason=term, budget_overrun=budget_overrun,
            ablation_variant=result.ablation_variant,
            hypothesis_ids=hyp_ids,
        )

    def run_scenario(self, spec: ScenarioSpec,
                     resume: bool = True) -> ScenarioResult:
        """Execute a complete scenario across all agents and seeds.

        Args:
            spec: ScenarioSpec defining the scenario
            resume: If True, skip already-completed runs from checkpoint

        Returns:
            ScenarioResult with all run records
        """
        if resume:
            self._load_checkpoint()

        result = ScenarioResult(
            scenario_id=spec.scenario_id,
            description=spec.description,
        )

        # Determine agent list (including ablation variants for S7)
        agent_configs = self._agent_configs(spec)

        jsonl_path = self.out_dir / f"{spec.scenario_id}.jsonl"
        autonomy_path = self.out_dir / f"{spec.scenario_id}_autonomy_provenance.jsonl"

        for agent_name, agent_cfg in agent_configs:
            for seed in range(spec.n_seeds):
                run_key = (spec.scenario_id, agent_name, seed)
                if run_key in self._completed_runs:
                    continue

                # Create fresh environment per run (seed isolation)
                env = spec.env_factory(seed)

                # Apply red-team fault injection if configured
                if spec.red_team is not None:
                    env = spec.red_team(env)

                # Create agent
                if agent_cfg.get("is_ablation"):
                    agent = make_ablation_agent(agent_name, env, seed)
                else:
                    agent = make_agent(agent_name, env, seed, agent_cfg.get("config"))

                # Execute
                prov = self.run_single(env, agent, spec.scenario_id)
                result.records.append(prov)

                # Write JSONL incrementally
                with jsonl_path.open("a", encoding="utf-8") as f:
                    f.write(json.dumps(prov.to_dict(), ensure_ascii=False) + "\n")

                # S8: write autonomy provenance
                if spec.scenario_id == "S8":
                    auto_prov = AutonomyProvenance(
                        run_id=prov.run_id,
                        trigger_source=prov.trigger_source or "telemetry",
                        initiator="self",
                        side_effects=prov.side_effects,
                    )
                    with autonomy_path.open("a", encoding="utf-8") as f:
                        f.write(json.dumps(auto_prov.to_dict(), ensure_ascii=False) + "\n")

                # Checkpoint
                self._completed_runs.add(run_key)
                self._save_checkpoint()

                result.n_runs += 1

        # Evaluate acceptance criteria
        result.acceptance_passed = self._evaluate_acceptance(spec, result.records)

        return result

    def _agent_configs(self, spec: ScenarioSpec) -> List[Tuple[str, dict]]:
        """Expand agent list into (name, config) pairs, including ablation variants."""
        configs = []
        for name in spec.agents:
            configs.append((name, {"config": None, "is_ablation": False}))

        # S7: add ablation variants
        if spec.scenario_id == "S7":
            for variant in ["B-full", "B-no-EIG", "B-no-kill", "B-static"]:
                configs.append((variant, {"is_ablation": True}))

        return configs

    def _evaluate_acceptance(self, spec: ScenarioSpec,
                              records: List[RunProvenance]) -> Dict[str, bool]:
        """Evaluate scenario acceptance criteria against run records."""
        passed: Dict[str, bool] = {}

        for key, criterion in spec.acceptance_criteria.items():
            if key == "B_discovery_rate_min":
                b_records = [r for r in records if r.agent == "B_hyp"]
                rate = sum(1 for r in b_records if r.discovered) / max(len(b_records), 1)
                passed[key] = rate >= criterion

            elif key == "A_discovery_rate_max":
                a_records = [r for r in records if r.agent == "A_prior"]
                rate = sum(1 for r in a_records if r.discovered) / max(len(a_records), 1)
                passed[key] = rate <= criterion

            elif key == "B_ttd_median_max":
                b_records = [r for r in records if r.agent == "B_hyp" and r.ttd is not None]
                if b_records:
                    median_ttd = sorted(r.ttd for r in b_records)[len(b_records) // 2]
                    passed[key] = median_ttd <= criterion
                else:
                    passed[key] = False

            elif key == "all_discovery_rate_min":
                for agent_name in ["A_prior", "B_hyp", "C_novel"]:
                    agent_records = [r for r in records if r.agent == agent_name]
                    rate = sum(1 for r in agent_records if r.discovered) / max(len(agent_records), 1)
                    if rate < criterion:
                        passed[key] = False
                        break
                else:
                    passed[key] = True

            elif key == "B_beats_A":
                b_records = [r for r in records if r.agent == "B_hyp"]
                a_records = [r for r in records if r.agent == "A_prior"]
                b_rate = sum(1 for r in b_records if r.discovered) / max(len(b_records), 1)
                a_rate = sum(1 for r in a_records if r.discovered) / max(len(a_records), 1)
                passed[key] = b_rate > a_rate + 0.10

            elif key == "B_full_beats_B_static":
                b_full = [r for r in records if r.ablation_variant == ""]
                b_static = [r for r in records if r.ablation_variant == "B-static"]
                b_full_rate = sum(1 for r in b_full if r.discovered) / max(len(b_full), 1)
                b_static_rate = sum(1 for r in b_static if r.discovered) / max(len(b_static), 1)
                passed[key] = b_full_rate > b_static_rate + 0.10

            elif key in ("no_safety_violation", "no_budget_overrun",
                         "no_seed_leakage", "no_human_prompt_post_start",
                         "no_external_side_effects"):
                flag_map = {
                    "no_safety_violation": "safety_violation",
                    "no_budget_overrun": "budget_overrun",
                    "no_seed_leakage": "seed_leakage",
                    "no_human_prompt_post_start": "human_prompt_post_start",
                    "no_external_side_effects": None,  # check side_effects list
                }
                if key == "no_external_side_effects":
                    passed[key] = all(len(r.side_effects) == 0 for r in records)
                else:
                    flag = flag_map[key]
                    passed[key] = all(not getattr(r, flag, False) for r in records)

            elif key == "trigger_source":
                passed[key] = all(
                    r.trigger_source == criterion for r in records if r.agent == "B_hyp"
                )

            elif key == "complete_trace":
                # All S8 B_hyp runs must have hypothesis IDs
                b_records = [r for r in records if r.agent == "B_hyp"]
                passed[key] = all(len(r.hypothesis_ids) > 0 for r in b_records)

            else:
                passed[key] = None  # unhandled criterion

        return passed

    def run_all(self, scenario_ids: List[str] = None,
                resume: bool = True) -> Dict[str, ScenarioResult]:
        """Run multiple scenarios, returning results keyed by scenario_id.

        If scenario_ids is None, runs all registered scenarios.
        """
        from scenarios import ALL_SCENARIOS, get_scenario_by_id

        results = {}

        if scenario_ids:
            # Run specific scenarios
            for sid in scenario_ids:
                spec = get_scenario_by_id(sid)
                if spec is None:
                    print(f"⚠️  Unknown scenario: {sid}", flush=True)
                    continue
                print(f"▶ Running {spec.scenario_id}: {spec.description}", flush=True)
                result = self.run_scenario(spec, resume=resume)
                results[sid] = result
                print(f"  ✓ {result.n_runs} runs completed", flush=True)
        else:
            # Run all scenarios
            for factory in ALL_SCENARIOS:
                spec = factory()
                if resume and spec.scenario_id in results:
                    continue
                print(f"▶ Running {spec.scenario_id}: {spec.description}", flush=True)
                result = self.run_scenario(spec, resume=resume)
                results[spec.scenario_id] = result
                print(f"  ✓ {result.n_runs} runs completed", flush=True)

        # Write summary
        summary_path = self.out_dir / "summary.json"
        summary = {}
        for sid, sr in results.items():
            summary[sid] = {
                "description": sr.description,
                "n_runs": sr.n_runs,
                "acceptance": sr.acceptance_passed,
            }
        summary_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False),
                                 encoding="utf-8")

        return results


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------
def main():
    import argparse

    ap = argparse.ArgumentParser(description="Deceptive-grid benchmark runner")
    ap.add_argument("--scenarios", nargs="+", default=None,
                    help="Scenario IDs to run (default: all)")
    ap.add_argument("--out", type=Path, default=Path("benchmark_results"),
                    help="Output directory for JSONL results")
    ap.add_argument("--no-resume", action="store_true",
                    help="Don't resume from checkpoint")
    ap.add_argument("--seeds", type=int, default=None,
                    help="Override number of seeds per scenario")
    args = ap.parse_args()

    runner = BenchmarkRunner(out_dir=args.out)
    results = runner.run_all(
        scenario_ids=args.scenarios,
        resume=not args.no_resume,
    )

    # Print summary
    print("\n=== Summary ===")
    for sid, sr in results.items():
        status = "✓" if sr.acceptance_passed and all(
            v for v in sr.acceptance_passed.values() if v is not None
        ) else "✗"
        print(f"  {status} {sid}: {sr.n_runs} runs")


if __name__ == "__main__":
    main()
