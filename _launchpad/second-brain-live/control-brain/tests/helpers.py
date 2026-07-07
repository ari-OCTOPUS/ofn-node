from core.registry import Registry
from core.store import Store
from core.safety import SafetyGate
from core.manager import ProjectManager
from tests.fakes import FakeRunner


def build(tmp_path, enabled=True, secrets_map=None, provider=None):
    cfg = tmp_path / "config"
    cfg.mkdir()
    lines = [
        "owner_chat_id: 0",
        "projects:",
        "  - id: demo",
        "    name: نمونه",
        '    workdir: "."',
        '    start: ["python", "-c", "pass"]',
        '    test: ["python", "-c", "pass"]',
        f"    enabled: {str(enabled).lower()}",
    ]
    if secrets_map:
        lines.append("    secrets:")
        for k, v in secrets_map.items():
            lines.append(f'      {k}: "{v}"')
    (cfg / "projects.yaml").write_text("\n".join(lines) + "\n", encoding="utf-8")
    reg = Registry(cfg / "projects.yaml")
    store = Store(tmp_path / "state.db")
    safety = SafetyGate(store, tmp_path / "STOP")
    runner = FakeRunner()
    return ProjectManager(reg, store, safety, runner, secrets=provider), safety, runner
