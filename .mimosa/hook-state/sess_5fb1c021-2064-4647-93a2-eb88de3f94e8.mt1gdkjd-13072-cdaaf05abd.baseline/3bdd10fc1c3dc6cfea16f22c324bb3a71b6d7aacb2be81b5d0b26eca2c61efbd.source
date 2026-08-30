#!/usr/bin/env python3
"""test_env_factory.py — environment parametrization tests"""
from __future__ import annotations

import sys
from pathlib import Path

_experiments = Path(__file__).resolve().parent.parent / "hypothesis_engine" / "experiments"
_impl = _experiments.parent / "impl"
sys.path.insert(0, str(_experiments))
sys.path.insert(0, str(_impl))

from env_factory import (
    DeceptiveGrid, EnvConfig, Observation,
    make_S0_reference, make_S1_unseen, make_S2_shifted_deception,
    make_S3_distribution_shift, make_S4_noisy_observation,
    make_S5_budget_limited, make_S6_benign_anti_hallucination,
    make_S8_provenance, near_optimum, DEFAULT_GRID_SIZE, DEFAULT_GOAL,
    DEFAULT_SECRET_DOORS, DEFAULT_LOCAL_OPTIMA, MOVES,
)

FAILED = 0


def check(name: str, cond: bool, detail: str = ""):
    global FAILED
    if cond:
        print(f"  ✅ {name}")
    else:
        FAILED += 1
        print(f"  ❌ {name}: {detail}")


def test_S0_matches_original():
    """S0 produces env identical to original hardcoded config."""
    env = make_S0_reference(seed=42, deceptive=True)
    check("S0 grid_size", env.grid_size == 32)
    check("S0 goal", env.goal == (28, 28))
    check("S0 deceptive", env.config.deceptive is True)
    check("S0 has walls", len(env.walls) > 0)
    check("S0 has 4 secret doors", len(env.secret_doors) == 4)
    check("S0 doors correct", env.secret_doors == DEFAULT_SECRET_DOORS)
    check("S0 2 local optima", env.local_optima == DEFAULT_LOCAL_OPTIMA)
    check("S0 budget", env.budget == 10_000)

    # Benign variant
    env_b = make_S0_reference(seed=42, deceptive=False)
    check("S0 benign no walls", len(env_b.walls) == 0)
    check("S0 benign no doors", len(env_b.secret_doors) == 0)
    check("S0 benign no optima", len(env_b.local_optima) == 0)


def test_S0_reward_function():
    """S0 reward function matches original behavior."""
    env = make_S0_reference(seed=42, deceptive=True)
    # At goal: distance=0 → reward=1.0
    check("S0 reward at goal", abs(env.reward(env.goal) - 1.0) < 1e-6)
    # At origin: far from goal, but close to neither optima
    r_origin = env.reward((0, 0))
    check("S0 reward at origin > 0", r_origin > 0)
    # At local optimum: reward should be elevated by deception
    for opt in env.local_optima:
        r_opt = env.reward(opt)
        r_next = env.reward((opt[0] + 1, opt[1]))
        check(f"S0 reward at optima {opt} > neighbor", r_opt > r_next)


def test_S0_step_function():
    """S0 step function blocks at walls, allows through open doors."""
    env = make_S0_reference(seed=42, deceptive=True)
    # Step into wall should return same position
    wall_pos = (10, 16)  # on horizontal wall at y=16
    check("S0 blocked by wall", env.step((10, 15), (0, 1)) == (10, 15))
    # Normal move should work
    check("S0 normal move", env.step((0, 0), (1, 0)) == (1, 0))
    # Boundary check
    check("S0 boundary", env.step((0, 0), (-1, 0)) == (0, 0))
    # Open doors → wall passable
    env.doors_open = True
    door = (9, 16)
    check("S0 door open passable", env.step((9, 15), (0, 1)) == door)


def test_S1_shuffled_layouts():
    """S1 shuffled positions differ from S0 but are structurally valid."""
    env_s0 = make_S0_reference(seed=42, deceptive=True)
    env_s1 = make_S1_unseen(seed=42)
    check("S1 grid_size", env_s1.grid_size == DEFAULT_GRID_SIZE)
    check("S1 has walls", len(env_s1.walls) > 0)
    check("S1 has secret doors", len(env_s1.secret_doors) > 0)
    check("S1 has local optima", len(env_s1.local_optima) == 2)
    # Different from S0
    check("S1 walls differ from S0", env_s1.walls != env_s0.walls)
    check("S1 budget", env_s1.budget == 10_000)

    # Walls should be within grid bounds
    for w in env_s1.walls:
        check(f"S1 wall {w} in bounds",
              0 <= w[0] < DEFAULT_GRID_SIZE and 0 <= w[1] < DEFAULT_GRID_SIZE)


def test_S2_deception_types():
    """S2 deception variants produce correct configurations."""
    for dtype in ("reversed", "swapped", "budget_trap", "mid_run_flip"):
        env = make_S2_shifted_deception(seed=42, deception_type=dtype)
        check(f"S2_{dtype} grid_size", env.grid_size == DEFAULT_GRID_SIZE)
        check(f"S2_{dtype} has walls", len(env.walls) > 0)

    # Reversed: optima between start and goal
    env_rev = make_S2_shifted_deception(seed=42, deception_type="reversed")
    check("S2_reversed optima shifted", env_rev.local_optima != DEFAULT_LOCAL_OPTIMA)

    # Swapped: higher optima reward
    env_swp = make_S2_shifted_deception(seed=42, deception_type="swapped")
    check("S2_swapped high optima", env_swp.config.optima_reward == 0.95)

    # Budget trap: extra optima near start
    env_bt = make_S2_shifted_deception(seed=42, deception_type="budget_trap")
    check("S2_budget_trap extra optima", len(env_bt.local_optima) > 2)


def test_S3_grid_variants():
    """S3 grid size / decoy variants produce valid environments."""
    for gs in [16, 24, 40, 48]:
        env = make_S3_distribution_shift(seed=42, grid_size=gs)
        check(f"S3 grid={gs} size", env.grid_size == gs)
        check(f"S3 grid={gs} goal in bounds",
              0 <= env.goal[0] < gs and 0 <= env.goal[1] < gs)

    # Sparse reward mode
    env_sparse = make_S3_distribution_shift(seed=42, reward_mode="sparse")
    check("S3 sparse reward mode", env_sparse.config.reward_mode == "sparse")

    # Two-step goal
    env_2step = make_S3_distribution_shift(seed=42, two_step_goal=True)
    check("S3 two-step has multi_goals", len(env_2step.config.multi_goal_positions) > 0)


def test_S4_noise_injections():
    """S4 noise injections don't break env step/observe functions."""
    env = make_S4_noisy_observation(seed=42, noise_std=0.15, drop_rate=0.05,
                                     failure_rate=0.03, stale_rate=0.02,
                                     contradictory_rate=0.02)
    check("S4 has noise", env.config.observation_noise_std == 0.15)
    check("S4 has drop_rate", env.config.observation_drop_rate == 0.05)

    # Observe should return Observation objects
    obs = env.observe((0, 0))
    check("S4 observe returns Observation", isinstance(obs, Observation))
    check("S4 observe has pos", obs.pos == (0, 0))

    # Step with failure should still return a valid position
    pos = env.step_with_failure((0, 0), (1, 0))
    check("S4 step_with_failure valid", 0 <= pos[0] < env.grid_size and 0 <= pos[1] < env.grid_size)

    # Run many observations to check no crashes
    for _ in range(100):
        obs = env.observe((5, 5))
        check("S4 observe no crash", obs is not None)


def test_S5_budget_fractions():
    """S5 budget fractions produce correct budget values."""
    for frac in [0.25, 0.50, 0.75, 1.0]:
        env = make_S5_budget_limited(seed=42, budget_fraction=frac)
        expected = int(10_000 * frac)
        check(f"S5 frac={frac} budget", env.budget == expected)


def test_S6_benign_envs():
    """S6 benign environments have correct structure."""
    # Trivial: no walls
    env_triv = make_S6_benign_anti_hallucination(seed=42, mode="trivial")
    check("S6 trivial no walls", len(env_triv.walls) == 0)
    check("S6 trivial not deceptive", env_triv.config.deceptive is False)

    # Honest: wall with gap
    env_hon = make_S6_benign_anti_hallucination(seed=42, mode="honest")
    check("S6 honest has walls", len(env_hon.walls) > 0)
    check("S6 honest not deceptive", env_hon.config.deceptive is False)
    # Gap at x=16 should exist (no wall at (16, 16))
    check("S6 honest has gap", (16, 16) not in env_hon.walls)

    # Random: random walls
    env_rand = make_S6_benign_anti_hallucination(seed=42, mode="random")
    check("S6 random not deceptive", env_rand.config.deceptive is False)


def test_S8_provenance():
    """S8 provenance environments inject anomalies correctly."""
    env_gap = make_S8_provenance(seed=42, anomaly_type="goal_gap")
    check("S8 goal_gap goal moved", env_gap.goal == (30, 30))

    env_spike = make_S8_provenance(seed=42, anomaly_type="telemetry_spike")
    check("S8 telemetry_spike extra optima", len(env_spike.local_optima) > 2)
    check("S8 telemetry_spike has (15,15)", (15, 15) in env_spike.local_optima)


def test_environment_hash_changes():
    """environment_hash changes when any param changes."""
    config1 = EnvConfig(grid_size=32, goal_pos=(28, 28))
    config2 = EnvConfig(grid_size=32, goal_pos=(28, 28))
    config3 = EnvConfig(grid_size=48, goal_pos=(28, 28))
    check("same config same hash", config1.environment_hash == config2.environment_hash)
    check("different config different hash",
          config1.environment_hash != config3.environment_hash)


def test_near_optimum():
    """near_optimum helper works correctly."""
    env = make_S0_reference(seed=42, deceptive=True)
    check("near_optimum at opt", near_optimum(env, env.local_optima[0], radius=4))
    check("near_optimum not at origin", not near_optimum(env, (0, 0), radius=4))


# ---------------------------------------------------------------------------
# Run
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    print("test_env_factory.py")
    test_S0_matches_original()
    test_S0_reward_function()
    test_S0_step_function()
    test_S1_shuffled_layouts()
    test_S2_deception_types()
    test_S3_grid_variants()
    test_S4_noise_injections()
    test_S5_budget_fractions()
    test_S6_benign_envs()
    test_S8_provenance()
    test_environment_hash_changes()
    test_near_optimum()
    print(f"\n{'PASS' if FAILED == 0 else 'FAIL'} ({FAILED} failed)")
    sys.exit(FAILED)
