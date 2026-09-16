import textwrap
from core.registry import Registry


def test_loads_projects(tmp_path):
    cfg = tmp_path / "config"
    cfg.mkdir()
    (cfg / "projects.yaml").write_text(textwrap.dedent("""
        owner_chat_id: 42
        projects:
          - id: a
            name: آ
            workdir: "x"
            start: ["python", "x.py"]
            enabled: true
    """), encoding="utf-8")
    reg = Registry(cfg / "projects.yaml")
    assert reg.owner_chat_id == 42
    assert reg.get("a").name == "آ"
    assert reg.get("a").enabled is True
    assert len(reg.all()) == 1
