import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "src" / "octopus_cognition"


def _forbidden_imports(path: Path, banned: set[str]) -> list[str]:
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


def test_policy_does_not_import_world_model_predictor():
    path = ROOT / "world_model" / "policy.py"
    banned = {"persistence", "planner", "contracts", "WorldModel"}
    assert _forbidden_imports(path, banned) == []


def test_skill_tracker_does_not_import_planner():
    path = ROOT / "metacontrol" / "skill.py"
    assert _forbidden_imports(path, {"planner", "persistence"}) == []


def test_gate_does_not_import_planner():
    path = ROOT / "metacontrol" / "gate.py"
    assert _forbidden_imports(path, {"planner", "world_model"}) == []


def test_daemon_scripts_do_not_import_planner():
    scripts = Path("/opt/octopus/scripts")
    banned = {"planner"}
    for name in (
        "world_model_shadow.py",
        "skill_tracker_loop.py",
        "metacontrol_shadow.py",
        "stability_monitor.py",
    ):
        assert _forbidden_imports(scripts / name, banned) == [], name


def test_policy_never_executes_even_if_advisory_says_so(tmp_path, monkeypatch):
    from octopus_cognition.world_model import policy

    advisory = tmp_path / "latest.json"
    advisory.write_text('{"executable": true, "recommendation": "PLAN_ALLOWED"}', encoding="utf-8")
    monkeypatch.setattr(policy, "ADVISORY", advisory)
    assert policy.choose_action({}) == "NO_ACTION_OBSERVE_ONLY"
