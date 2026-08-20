# -*- coding: utf-8 -*-
"""Discover test_*.py vs AST-registered names in run_all.py.

Registry is file-level (one `test_*.py` = one slot). Function count inside a
file is a separate metric and must not be added to `discovered`.
"""
from __future__ import annotations

import ast
from pathlib import Path
from typing import Any

_OPS = Path(__file__).resolve().parent.parent
DEFAULT_TESTS_DIR = _OPS / "tests"
DEFAULT_RUN_ALL = DEFAULT_TESTS_DIR / "run_all.py"


def _string_constants(node: ast.AST) -> list[str]:
    out: list[str] = []
    for child in ast.walk(node):
        if isinstance(child, ast.Constant) and isinstance(child.value, str):
            out.append(child.value)
    return out


def registered_from_run_all(run_all: Path | None = None) -> set[str]:
    path = Path(run_all or DEFAULT_RUN_ALL)
    tree = ast.parse(path.read_text(encoding="utf-8", errors="replace"))
    names: set[str] = set()
    for node in tree.body:
        if not isinstance(node, ast.Assign):
            continue
        targets = [t.id for t in node.targets if isinstance(t, ast.Name)]
        if not any(t in ("TESTS", "EXTRA_TESTS", "PYTEST_TESTS") for t in targets):
            continue
        for s in _string_constants(node.value):
            base = Path(s.replace("\\", "/")).name
            if base.startswith("test_") and base.endswith(".py"):
                names.add(base)
            elif base.endswith(".py") and "test" in base:
                names.add(base)
    return names


def discover_test_files(tests_dir: Path | None = None,
                        extra_roots: list[Path] | None = None) -> set[str]:
    roots = [Path(tests_dir or DEFAULT_TESTS_DIR)]
    roots.extend(extra_roots or [])
    found: set[str] = set()
    for root in roots:
        if not root.is_dir():
            continue
        for p in root.glob("test_*.py"):
            found.add(p.name)
        for p in root.glob("**/test_*.py"):
            if "_tmp" in p.parts or "node_modules" in p.parts:
                continue
            found.add(p.name)
    return found


def report(*, tests_dir: Path | None = None, run_all: Path | None = None) -> dict[str, Any]:
    discovered = discover_test_files(tests_dir)
    registered = registered_from_run_all(run_all)
    missing = sorted(discovered - registered)
    extra = sorted(registered - discovered)
    gap = len(missing)
    return {
        "schema": "test-discovery/1",
        "discovered": len(discovered),
        "registered": len(registered),
        "gap": gap,
        "ci_failure": gap_is_ci_failure(gap),
        "not_registered_sample": missing[:20],
        "registered_missing_file_sample": extra[:20],
        "writes_performed": False,
    }


def gap_is_ci_failure(gap: int) -> bool:
    """CI predicate: any discoverable test absent from run_all is a failure."""
    return int(gap) > 0
