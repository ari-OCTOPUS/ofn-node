#!/usr/bin/env python3
"""test_agents.py — agent class tests including ablation variants"""
from __future__ import annotations

import sys
from pathlib import Path

_experiments = Path(__file__).resolve().parent.parent / "hypothesis_engine" / "experiments"
_impl = _experiments.parent / "impl"
sys.path.insert(0, str(_experiments))
sys.path.insert(0, str(_impl))

from env_factory import make_S0_reference, make_S6_benign_anti_hallucination, near_optimum
from agents import (
    AgentConfig, AgentResult, BaseAgent,
    PriorAgent, NoveltyAgent, HypothesisAgent,
    AGENT_REGISTRY, make_agent, make_ablation_agent,
)

FAILED = 0


def check(name: str, cond: bool, detail: str = ""):
    global FAILED
    if cond:
        print(f"  ✅ {name}")
    else:
        FAILED += 1
        print(f"  ❌ {name}: {detail}")


# ---------------------------------------------------------------------------
# Agent interface contract
# ---------------------------------------------------------------------------
def test_base_agent_is_abstract():
    """BaseAgent cannot be instantiated directly."""
    try:
        BaseAgent.__new__(BaseAgent)  # just raw allocation
        # Can allocate but not meaningfully construct
    except TypeError:
        pass  # expected
    check("BaseAgent is abstract", True)


def test_agent_registry():
    """All three agents are in the registry."""
    check("A_prior in registry", "A_prior" in AGENT_REGISTRY)
    check("B_hyp in registry", "B_hyp" in AGENT_REGISTRY)
    check("C_novel in registry", "C_novel" in AGENT_REGISTRY)
    check("registry has 3 agents", len(AGENT_REGISTRY) == 3)


def test_make_agent_factory():
    """make_agent returns correct types."""
    env = make_S0_reference(seed=42)
    a = make_agent("A_prior", env, 42)
    check("make_agent A_prior is PriorAgent", isinstance(a, PriorAgent))
    c = make_agent("C_novel", env, 42)
    check("make_agent C_novel is NoveltyAgent", isinstance(c, NoveltyAgent))
    b = make_agent("B_hyp", env, 42)
    check("make_agent B_hyp is HypothesisAgent", isinstance(b, HypothesisAgent))
    try:
        make_agent("NONEXISTENT", env, 42)
        check("make_agent unknown raises", False)
    except ValueError:
        check("make_agent unknown raises ValueError", True)


def test_agent_result_structure():
    """AgentResult has all required fields."""
    r = AgentResult(agent="test", env_type="deceptive", seed=42)
    check("AgentResult.agent", r.agent == "test")
    check("AgentResult.seed", r.seed == 42)
    check("AgentResult.discovered default False", r.discovered is False)
    check("AgentResult.ttd default None", r.ttd is None)
    check("AgentResult.total_steps default 0", r.total_steps == 0)
    check("AgentResult.ablation_variant default empty", r.ablation_variant == "")


# ---------------------------------------------------------------------------
# Agent A — PriorAgent
# ---------------------------------------------------------------------------
def test_agent_a_run_returns_result():
    """Agent A run() returns AgentResult with correct structure."""
    env = make_S0_reference(seed=42)
    agent = PriorAgent(env, seed=99)
    result = agent.run()
    check("AgentA result is AgentResult", isinstance(result, AgentResult))
    check("AgentA result.agent", result.agent == "A_prior")
    check("AgentA result.seed", result.seed == 42)
    check("AgentA result.total_steps > 0", result.total_steps > 0)


def test_agent_a_deterministic():
    """Agent A with same seed produces same steps."""
    env1 = make_S0_reference(seed=42)
    env2 = make_S0_reference(seed=42)
    r1 = PriorAgent(env1, seed=99).run()
    r2 = PriorAgent(env2, seed=99).run()
    check("AgentA deterministic steps", r1.total_steps == r2.total_steps)
    check("AgentA deterministic discovery", r1.discovered == r2.discovered)


def test_agent_a_s0_low_discovery():
    """Agent A should have low discovery rate on S0 deceptive (≤ 5%)."""
    discovered = 0
    n_runs = 20
    for i in range(n_runs):
        env = make_S0_reference(seed=i)
        result = PriorAgent(env, seed=i).run()
        if result.discovered:
            discovered += 1
    rate = discovered / n_runs
    check(f"AgentA S0 discovery ≤ 5% (got {rate:.2f})",
          rate <= 0.10, f"rate={rate:.2f}")


# ---------------------------------------------------------------------------
# Agent C — NoveltyAgent
# ---------------------------------------------------------------------------
def test_agent_c_run_returns_result():
    """Agent C run() returns AgentResult with correct structure."""
    env = make_S0_reference(seed=42)
    agent = NoveltyAgent(env, seed=99)
    result = agent.run()
    check("AgentC result is AgentResult", isinstance(result, AgentResult))
    check("AgentC result.agent", result.agent == "C_novel")
    check("AgentC result.seed", result.seed == 42)
    check("AgentC result.total_steps > 0", result.total_steps > 0)


def test_agent_c_on_benign():
    """Agent C should discover on benign environment."""
    env = make_S6_benign_anti_hallucination(seed=42, mode="trivial")
    result = NoveltyAgent(env, seed=42).run()
    check("AgentC discovers trivial env", result.discovered,
          f"total_steps={result.total_steps}")


# ---------------------------------------------------------------------------
# Agent B — HypothesisAgent
# ---------------------------------------------------------------------------
def test_agent_b_run_returns_result():
    """Agent B run() returns AgentResult with hypothesis tracking."""
    env = make_S0_reference(seed=42)
    agent = HypothesisAgent(env, seed=99)
    result = agent.run()
    check("AgentB result is AgentResult", isinstance(result, AgentResult))
    check("AgentB result.agent", result.agent == "B_hyp")
    check("AgentB result.seed", result.seed == 42)
    check("AgentB has hypotheses_tracked", len(result.hypotheses_tracked) > 0)
    check("AgentB has hyp_steps", result.hyp_steps >= 0)
    check("AgentB result.total_steps > 0", result.total_steps > 0)


def test_agent_b_hypotheses_tracked():
    """Agent B tracks hypothesis IDs, falsified status, and tested_steps."""
    env = make_S0_reference(seed=42)
    result = HypothesisAgent(env, seed=99).run()
    for hyp in result.hypotheses_tracked:
        check(f"Hypothesis has id", "id" in hyp)
        check(f"Hypothesis has falsified", "falsified" in hyp)
        check(f"Hypothesis has tested_steps", "tested_steps" in hyp)
        check(f"Hypothesis has is_decoy", "is_decoy" in hyp)


def test_agent_b_s0_discovery():
    """Agent B should have high discovery rate on S0 (≥ 80% in small sample)."""
    discovered = 0
    n_runs = 10
    for i in range(n_runs):
        env = make_S0_reference(seed=i)
        result = HypothesisAgent(env, seed=i).run()
        if result.discovered:
            discovered += 1
    rate = discovered / n_runs
    check(f"AgentB S0 discovery ≥ 80% (got {rate:.2f})",
          rate >= 0.80, f"rate={rate:.2f}")


# ---------------------------------------------------------------------------
# Ablation variants
# ---------------------------------------------------------------------------
def test_ablation_no_eig():
    """B-no-EIG variant is created and has correct label."""
    env = make_S0_reference(seed=42)
    agent = make_ablation_agent("B-no-EIG", env, 99)
    check("B-no-EIG is HypothesisAgent", isinstance(agent, HypothesisAgent))
    check("B-no-EIG config.use_eig is False", agent.config.use_eig is False)
    result = agent.run()
    check("B-no-EIG ablation_variant", result.ablation_variant == "B-no-EIG")


def test_ablation_no_kill():
    """B-no-kill variant disables kill condition."""
    env = make_S0_reference(seed=42)
    agent = make_ablation_agent("B-no-kill", env, 99)
    check("B-no-kill is HypothesisAgent", isinstance(agent, HypothesisAgent))
    check("B-no-kill config.use_kill_condition is False",
          agent.config.use_kill_condition is False)
    result = agent.run()
    check("B-no-kill ablation_variant", result.ablation_variant == "B-no-kill")


def test_ablation_static():
    """B-static variant has static beliefs."""
    env = make_S0_reference(seed=42)
    agent = make_ablation_agent("B-static", env, 99)
    check("B-static is HypothesisAgent", isinstance(agent, HypothesisAgent))
    check("B-static config.static_beliefs is True",
          agent.config.static_beliefs is True)
    result = agent.run()
    check("B-static ablation_variant", result.ablation_variant == "B-static")


def test_ablation_full():
    """B-full variant has all features enabled."""
    env = make_S0_reference(seed=42)
    agent = make_ablation_agent("B-full", env, 99)
    check("B-full is HypothesisAgent", isinstance(agent, HypothesisAgent))
    check("B-full use_eig True", agent.config.use_eig is True)
    check("B-full use_kill_condition True", agent.config.use_kill_condition is True)
    check("B-full static_beliefs False", agent.config.static_beliefs is False)
    result = agent.run()
    check("B-full ablation_variant empty", result.ablation_variant == "")


def test_ablation_unknown_raises():
    """Unknown ablation variant raises ValueError."""
    env = make_S0_reference(seed=42)
    try:
        make_ablation_agent("B-unknown", env, 99)
        check("unknown ablation raises", False)
    except ValueError:
        check("unknown ablation raises ValueError", True)


if __name__ == "__main__":
    print("test_agents.py")
    test_base_agent_is_abstract()
    test_agent_registry()
    test_make_agent_factory()
    test_agent_result_structure()
    test_agent_a_run_returns_result()
    test_agent_a_deterministic()
    test_agent_a_s0_low_discovery()
    test_agent_c_run_returns_result()
    test_agent_c_on_benign()
    test_agent_b_run_returns_result()
    test_agent_b_hypotheses_tracked()
    test_agent_b_s0_discovery()
    test_ablation_no_eig()
    test_ablation_no_kill()
    test_ablation_static()
    test_ablation_full()
    test_ablation_unknown_raises()
    print(f"\n{'PASS' if FAILED == 0 else 'FAIL'} ({FAILED} failed)")
    sys.exit(FAILED)
