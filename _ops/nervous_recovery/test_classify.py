# -*- coding: utf-8 -*-
"""Classify unregistered test_*.py files. Does not edit run_all by itself."""
from __future__ import annotations

import ast
from pathlib import Path
from typing import Any

from . import test_discovery

_OPS = Path(__file__).resolve().parent.parent
TESTS = _OPS / "tests"

ARCHIVE_MARKERS = (
    "retired", "archive", "_tmp", "generated", "close_experiments",
    "close_c025",
)
HELPER_MARKERS = ("conftest", "fixture", "helpers")


def _classify_one(path: Path) -> str:
    name = path.name.lower()
    if any(m in name for m in ARCHIVE_MARKERS):
        return "archived"
    if any(m in name for m in HELPER_MARKERS):
        return "fixture/helper"
    try:
        src = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return "broken/unrunnable"
    try:
        tree = ast.parse(src)
    except SyntaxError:
        return "broken/unrunnable"
    has_test = False
    has_main = False
    has_pytest = "pytest" in src
    module_assert = False
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and (
                node.name.startswith("test_") or node.name.startswith("t_")):
            has_test = True
        if isinstance(node, ast.Assert) and isinstance(getattr(node, "col_offset", None), int):
            module_assert = True
        if isinstance(node, ast.Compare):
            pass
        if isinstance(node, ast.If):
            try:
                dump = ast.dump(node)
            except Exception:  # noqa: BLE001
                dump = ""
            if "__main__" in dump:
                has_main = True
    # Top-level asserts (script-style suites).
    for node in tree.body:
        if isinstance(node, ast.Assert):
            module_assert = True
    if has_test or has_main or module_assert:
        return "valid test"
    if has_pytest:
        return "valid test"
    if "FAIL = []" in src or "def check(" in src or "def ok(" in src:
        return "valid test"
    return "unknown"


def classify_unregistered(*, tests_dir: Path | None = None,
                          run_all: Path | None = None) -> dict[str, Any]:
    tests_dir = Path(tests_dir or TESTS)
    rep = test_discovery.report(tests_dir=tests_dir, run_all=run_all)
    missing = sorted(set(test_discovery.discover_test_files(tests_dir))
                     - test_discovery.registered_from_run_all(run_all))
    buckets: dict[str, list[str]] = {}
    for name in missing:
        p = tests_dir / name
        kind = _classify_one(p) if p.exists() else "broken/unrunnable"
        buckets.setdefault(kind, []).append(name)
    return {
        "schema": "test-classify/1",
        "discovered": rep["discovered"],
        "registered": rep["registered"],
        "unregistered": len(missing),
        "counts": {k: len(v) for k, v in sorted(buckets.items())},
        "buckets": buckets,
        "valid_to_register": buckets.get("valid test", []),
        "note": "Do not register archived/helper/generated just to zero the gap.",
    }
