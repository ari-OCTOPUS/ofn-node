#!/usr/bin/env python3
"""Regression: manifest must not count its own/test processes as limbs."""
from __future__ import annotations

import importlib.util
import json
import tempfile
from pathlib import Path

OPS = Path(__file__).resolve().parents[1]
MODULE_PATH = OPS / "audit" / "organism_manifest.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("organism_manifest_tested", MODULE_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("unable to load organism_manifest")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> int:
    manifest = _load_module()

    assert manifest._role_of(
        "python organism.py", str(OPS / "organism.py")
    ) == "organism"
    assert manifest._role_of(
        "python organism_manifest.py", str(OPS / "audit" / "organism_manifest.py")
    ) == "audit(aux)"
    assert manifest._role_of(
        "python extract_graph.py", "extract_graph.py"
    ) == "tool(aux)"
    assert manifest._role_of(
        "python -m pytest test_x.py", str(OPS / "tests" / "test_x.py")
    ) == "test(aux)"
    assert manifest._role_of(
        "python board_cp/server.py", str(OPS / "board_cp" / "server.py")
    ) == "board_cp(aux)"
    assert manifest._role_of(
        "python -m brain.daemon", None
    ) == "4d_daemon(aux)"

    fake = [
        {"pid": 1, "started": "t1",
         "cmdline": f'python "{OPS / "organism.py"}"'},
        {"pid": 2, "started": "t2",
         "cmdline": f'python "{OPS / "board_cp" / "server.py"}"'},
        {"pid": 3, "started": "t3",
         "cmdline": f'python -m pytest "{OPS / "tests" / "test_x.py"}"'},
        {"pid": 4, "started": "t4",
         "cmdline": f'python "{OPS / "audit" / "organism_manifest.py"}"'},
    ]

    with tempfile.TemporaryDirectory() as td:
        out = Path(td) / "manifest.json"
        original_out = manifest.OUT
        original_processes = manifest._processes
        original_ports = manifest._ports
        original_flags = manifest._effective_flags_last_wins
        original_run = manifest._run
        manifest.OUT = out
        manifest._processes = lambda: fake
        manifest._ports = lambda: {1: [8771], 2: [8801]}
        manifest._effective_flags_last_wins = lambda: {}
        manifest._run = lambda *_args, **_kwargs: ""
        try:
            assert manifest.main() == 0
            data = json.loads(out.read_text(encoding="utf-8"))
        finally:
            manifest.OUT = original_out
            manifest._processes = original_processes
            manifest._ports = original_ports
            manifest._effective_flags_last_wins = original_flags
            manifest._run = original_run

    roles = [row["role"] for row in data["members_observed"]]
    transient_roles = [row["role"] for row in data["transient_processes_observed"]]
    assert roles == ["organism", "board_cp(aux)"], roles
    assert transient_roles == ["test(aux)", "audit(aux)"], transient_roles
    assert data["observed_processes_total"] == 4, data
    assert data["drift"]["unknown_cmdline_members"] == 0, data

    print("PASS organism manifest separates transient probes from members")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
