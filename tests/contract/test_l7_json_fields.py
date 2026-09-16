"""L7: assert keys exist on JSON under 09-LANES only. Does not import src."""
import json
from pathlib import Path

VAULT = Path(__file__).resolve().parents[2]
LANE7 = VAULT / "09-LANES" / "L7"


def test_hooks_routing_boundary_keys():
    data = json.loads((LANE7 / "hooks-routing-boundary.json").read_text(encoding="utf-8-sig"))
    assert "version" in data
    assert "hooks" in data
    hooks = data["hooks"]
    for name in (
        "beforeShellExecution",
        "beforeReadFile",
        "beforeMCPExecution",
        "stop",
    ):
        assert name in hooks


def test_context_bundle_field_list():
    data = json.loads((LANE7 / "context-bundle-fields.json").read_text(encoding="utf-8-sig"))
    for k in ("source_path", "source_sha256_8", "top_level_keys"):
        assert k in data
    keys = data["top_level_keys"]
    for k in ("schema", "organs", "blockers", "gate_0_verdict"):
        assert k in keys
