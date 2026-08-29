"""Shadow candidate invariants. Must not touch live Policy."""

from __future__ import annotations

import ast
from pathlib import Path

from octopus_cognition.world_model.interaction_candidate import (
    VERSION,
    apply_delta,
    delta,
    interaction_guard,
    persistence_delta,
)
from octopus_cognition.world_model.policy import choose_action


def _imports(path: Path, banned: set[str]) -> list[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    found: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if any(token in alias.name for token in banned):
                    found.append(alias.name)
        elif isinstance(node, ast.ImportFrom) and node.module:
            if any(token in node.module for token in banned):
                found.append(node.module)
    return found


def test_interaction_guard_candidate_differs_persistence_blind():
    result = interaction_guard("NO_ACTION_OBSERVE_ONLY")
    assert result["pass"] is True
    assert result["persistence_is_interaction_blind"] is True
    assert result["candidate_delta_a"] != result["candidate_delta_b"]
    assert result["persistence_delta_a"] == result["persistence_delta_b"]


def test_same_action_two_states_different_delta():
    action = "ADVISORY_THROTTLE"
    a = {"compute_pressure": 0.05, "memory_pressure": 0.1, "storage_integrity": 0.04, "sensor_coverage": 0.5}
    b = {"compute_pressure": 0.5, "memory_pressure": 0.4, "storage_integrity": 0.1, "sensor_coverage": 0.6667}
    assert delta(a, action) != delta(b, action)
    assert persistence_delta(a, action) == persistence_delta(b, action)


def test_live_policy_does_not_import_candidate():
    path = Path("/opt/octopus/cognition/src/octopus_cognition/world_model/policy.py")
    assert _imports(path, {"interaction_candidate", "planner", "PersistenceModel"}) == []
    assert choose_action({"compute_pressure": 0.9}) == "NO_ACTION_OBSERVE_ONLY"


def test_live_world_model_script_does_not_import_candidate():
    path = Path("/opt/octopus/scripts/world_model_shadow.py")
    assert _imports(path, {"interaction_candidate", "planner"}) == []


def test_evaluator_does_not_import_planner():
    path = Path("/opt/octopus/scripts/evaluate_shadow_candidate.py")
    assert path.is_file()
    assert _imports(path, {"planner"}) == []


def test_candidate_version_stable():
    assert VERSION == "interaction-meanrev-v1"
    state = {"compute_pressure": 0.2, "memory_pressure": 0.2, "storage_integrity": 0.05, "sensor_coverage": 0.6667}
    pred = apply_delta(state, "NO_ACTION_OBSERVE_ONLY")
    assert set(pred) == set(state)
    assert pred["sensor_coverage"] == state["sensor_coverage"]
