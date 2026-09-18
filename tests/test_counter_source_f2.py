"""A2 / F2: no second ofn-node file reports a different value for the
three governance counters. Class Z: this test never writes those values.

Canonical (ADR-F2, laptop proposal; owner vote required for vault files):
  may_authorize -> ofn/agents/brain_schema.py default False
  EXTERNAL_ACTIONS / NEW_LAN_LISTENERS -> no live assignment in this repo
"""
from __future__ import annotations

import ast
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OFN = ROOT / "ofn"
CANON_MAY = OFN / "agents" / "brain_schema.py"
UPPER = ("EXTERNAL_ACTIONS", "NEW_LAN_LISTENERS", "MAY_AUTHORIZE")
ASSIGN = re.compile(
    r"\b(EXTERNAL_ACTIONS|NEW_LAN_LISTENERS|MAY_AUTHORIZE)\s*=\s*(\S+)")


def test_brain_schema_is_the_may_authorize_canon() -> None:
    from ofn.agents.brain_schema import BrainProposal, SchemaViolation

    assert CANON_MAY.is_file()
    p = BrainProposal(business_id="ziman", action="propose",
                      summary="t", confidence=0.1)
    assert p.may_authorize is False
    try:
        BrainProposal(business_id="ziman", action="propose",
                      summary="t", confidence=0.1, may_authorize=True)
    except SchemaViolation:
        return
    raise AssertionError("canonical file must still reject may_authorize=True")


def test_no_second_ofn_source_assigns_the_three_counters() -> None:
    hits: list[str] = []
    for path in OFN.rglob("*"):
        if path.suffix not in {".py", ".json", ".cmd", ".env"}:
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        for m in ASSIGN.finditer(text):
            hits.append(f"{path.relative_to(ROOT)}:{m.group(1)}={m.group(2)}")
    assert hits == [], "F2: second source in ofn-node: " + "; ".join(hits)


def test_no_ofn_py_assigns_may_authorize_true() -> None:
    bad: list[str] = []
    for path in OFN.rglob("*.py"):
        try:
            tree = ast.parse(
                path.read_text(encoding="utf-8-sig"), filename=str(path))
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            if not isinstance(node, ast.keyword):
                continue
            if node.arg != "may_authorize":
                continue
            if isinstance(node.value, ast.Constant) and node.value.value is True:
                bad.append(str(path.relative_to(ROOT)))
    assert bad == [], "F2: may_authorize=True in " + ", ".join(bad)
