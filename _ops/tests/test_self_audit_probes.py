#!/usr/bin/env python3
"""self_audit probes must not lie with `or True`."""
import ast
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import harness  # noqa: E402

ENV = harness.setup("self-audit-probes")
_OPS = harness.SELF_OPS
for _p in (str(_OPS), str(_OPS / "budget"), str(_OPS / "cortex")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import self_audit as sa  # noqa: E402


def t_named_owner_and_trace_have_no_or_true():
    src = Path(sa.__file__).read_text("utf-8")
    tree = ast.parse(src)
    wanted = {"_probe_named_owner", "_probe_trace_independent"}
    found = set()
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name in wanted:
            found.add(node.name)
            chunk = ast.get_source_segment(src, node) or ""
            assert "or True" not in chunk, f"{node.name} still lies with or True"
    assert found == wanted, found


def t_trace_independent_status_follows_alerts_file():
    item = sa._probe_trace_independent()
    ok = Path(sa.opslib.ALERTS_MD).exists()
    if ok:
        assert item["status"] == "Done", item
    else:
        assert item["status"] == "Partial", item
    assert item["status"] != "Done" or ok


def t_named_owner_is_not_always_done():
    item = sa._probe_named_owner()
    assert item["status"] in ("Partial", "Missing"), item
    assert item["status"] != "Done"


if __name__ == "__main__":
    failed = harness.run([
        ("no or True in owner/trace probes", t_named_owner_and_trace_have_no_or_true),
        ("trace status follows alerts file", t_trace_independent_status_follows_alerts_file),
        ("named owner is not always Done", t_named_owner_is_not_always_done),
    ])
    sys.exit(1 if failed else 0)
