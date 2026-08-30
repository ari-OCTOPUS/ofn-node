#!/usr/bin/env python3
"""test_scenarios.py — scenario S0–S8 setup validation"""
from __future__ import annotations

import sys
from pathlib import Path

_experiments = Path(__file__).resolve().parent.parent / "hypothesis_engine" / "experiments"
_impl = _experiments.parent / "impl"
sys.path.insert(0, str(_experiments))
sys.path.insert(0, str(_impl))

from scenarios import (
    ALL_SCENARIOS, get_scenario_by_id, ScenarioSpec,
    S0_reference, S0_benign, S1_unseen,
    S2_reversed, S2_swapped, S2_budget_trap,
    S3_grid_variation, S3_sparse_reward, S3_two_step,
    S4_mixed_noise, S4_high_noise,
    S5_all_budgets,
    S6_trivial, S6_honest, S6_random,
    S7_ablation,
    S8_provenance,
    RED_TEAM_INJECTIONS,
)

FAILED = 0


def check(name: str, cond: bool, detail: str = ""):
    global FAILED
    if cond:
        print(f"  ✅ {name}")
    else:
        FAILED += 1
        print(f"  ❌ {name}: {detail}")


def test_all_scenarios_instantiate():
    """All 9 scenario families (S0–S8) instantiate without error."""
    expected_ids = {"S0", "S0_benign", "S1", "S2_reversed", "S2_swapped",
                    "S2_budget_trap", "S3_grid", "S3_sparse", "S3_twostep",
                    "S4_noise", "S4_high_noise", "S5_budget",
                    "S6_trivial", "S6_honest", "S6_random", "S7", "S8"}
    instantiated = set()
    for factory in ALL_SCENARIOS:
        spec = factory()
        check(f"{spec.scenario_id} is ScenarioSpec", isinstance(spec, ScenarioSpec))
        check(f"{spec.scenario_id} has description",
              len(spec.description) > 0)
        check(f"{spec.scenario_id} has env_factory",
              callable(spec.env_factory))
        check(f"{spec.scenario_id} has agents",
              len(spec.agents) > 0)
        check(f"{spec.scenario_id} has n_seeds > 0", spec.n_seeds > 0)
        check(f"{spec.scenario_id} has budget > 0", spec.budget > 0)
        check(f"{spec.scenario_id} has tags",
              len(spec.tags) > 0)
        instantiated.add(spec.scenario_id)

    check("All expected scenarios present",
          expected_ids.issubset(instantiated),
          f"missing: {expected_ids - instantiated}")


def test_S0_acceptance_criteria():
    """S0 reference has correct acceptance criteria."""
    spec = S0_reference()
    ac = spec.acceptance_criteria
    check("S0 B_discovery_rate_min", "B_discovery_rate_min" in ac)
    check("S0 B threshold ≥ 0.90", ac["B_discovery_rate_min"] >= 0.90)
    check("S0 A_discovery_rate_max", "A_discovery_rate_max" in ac)
    check("S0 A threshold ≤ 0.05", ac["A_discovery_rate_max"] <= 0.05)


def test_S8_acceptance_criteria():
    """S8 provenance scenario has trigger_source == telemetry."""
    spec = S8_provenance()
    ac = spec.acceptance_criteria
    check("S8 has trigger_source", "trigger_source" in ac)
    check("S8 trigger_source == telemetry", ac["trigger_source"] == "telemetry")
    check("S8 has complete_trace", "complete_trace" in ac)
    check("S8 has no_human_prompt_post_start", "no_human_prompt_post_start" in ac)
    check("S8 has no_external_side_effects", "no_external_side_effects" in ac)


def test_S7_ablation_agents():
    """S7 ablation scenario has B_hyp as the only base agent."""
    spec = S7_ablation()
    check("S7 agents == [B_hyp]", spec.agents == ["B_hyp"])


def test_scenario_env_factories():
    """Each scenario's env_factory returns a valid DeceptiveGrid."""
    for factory in ALL_SCENARIOS:
        spec = factory()
        env = spec.env_factory(seed=42)
        check(f"{spec.scenario_id} env is DeceptiveGrid",
              hasattr(env, 'grid_size') and hasattr(env, 'budget'))


def test_get_scenario_by_id():
    """get_scenario_by_id returns correct scenario or None."""
    spec = get_scenario_by_id("S0")
    check("get S0", spec is not None and spec.scenario_id == "S0")
    spec = get_scenario_by_id("S8")
    check("get S8", spec is not None and spec.scenario_id == "S8")
    spec = get_scenario_by_id("NONEXISTENT")
    check("get nonexistent returns None", spec is None)


def test_red_team_injections():
    """Red-team fault injections are callable and modify correct targets."""
    check("red_team registry has all injections",
          set(RED_TEAM_INJECTIONS.keys()) == {
              "prompt_contamination", "registry_corruption_kill",
              "registry_corruption_forbidden", "evidence_laundering",
              "stale_hypothesis_leak", "reward_hacking_check",
              "seed_leakage_check",
          })

    # Test prompt_contamination
    result = RED_TEAM_INJECTIONS["prompt_contamination"]("normal observation")
    check("prompt_contamination injects text",
          "SYSTEM NOTE" in result and "normal observation" in result)

    # Test evidence_laundering
    result = RED_TEAM_INJECTIONS["evidence_laundering"]("valid-id")
    check("evidence_laundering returns fake ID",
          result == "EVIDENCE-NONEXISTENT-FAKE")

    # Test reward_hacking_check
    check("reward_hacking no hack",
          RED_TEAM_INJECTIONS["reward_hacking_check"](0.1, 100, True) is False)
    check("reward_hacking detected",
          RED_TEAM_INJECTIONS["reward_hacking_check"](50.0, 100, False) is True)

    # Test seed_leakage_check
    check("seed_leakage no leak",
          RED_TEAM_INJECTIONS["seed_leakage_check"](False) is False)
    check("seed_leakage detected",
          RED_TEAM_INJECTIONS["seed_leakage_check"](True) is True)

    # Test registry_corruption
    hyp = {"record": {"kill_condition": "3 fails"}}
    corrupted = RED_TEAM_INJECTIONS["registry_corruption_kill"](hyp)
    check("registry_corruption_kill removes kill_condition",
          corrupted["record"]["kill_condition"] is None)

    hyp2 = {"record": {"may_mutate_ledger": False}}
    corrupted2 = RED_TEAM_INJECTIONS["registry_corruption_forbidden"](hyp2)
    check("registry_corruption_forbidden sets forbidden flag",
          corrupted2["record"]["may_mutate_ledger"] is True)

    # Test stale_hypothesis_leak
    hyp3 = {"record": {"_origin_env_hash": ""}}
    leaked = RED_TEAM_INJECTIONS["stale_hypothesis_leak"](
        hyp3, "hash_current", "hash_original")
    check("stale_hypothesis_leak sets origin",
          leaked["record"]["_origin_env_hash"] == "hash_original")
    check("stale_hypothesis_leak sets stale flag", leaked["_stale"] is True)


if __name__ == "__main__":
    print("test_scenarios.py")
    test_all_scenarios_instantiate()
    test_S0_acceptance_criteria()
    test_S8_acceptance_criteria()
    test_S7_ablation_agents()
    test_scenario_env_factories()
    test_get_scenario_by_id()
    test_red_team_injections()
    print(f"\n{'PASS' if FAILED == 0 else 'FAIL'} ({FAILED} failed)")
    sys.exit(FAILED)
