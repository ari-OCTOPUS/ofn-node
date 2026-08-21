#!/usr/bin/env python3
"""Generate an auditable node map from the literal run_all.py registry.

The generator imports no test module and executes no test.  It parses Python
AST only, reports every registered file, every discovered top-level test node,
duplicate registry entries, missing files, syntax errors, and zero-node files.
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import json
import subprocess
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
RUN_ALL = HERE / "run_all.py"


def _registry() -> list[str]:
    tree = ast.parse(RUN_ALL.read_text(encoding="utf-8", errors="replace"))
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(
            isinstance(target, ast.Name) and target.id == "TESTS"
            for target in node.targets
        ):
            value = ast.literal_eval(node.value)
            if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
                raise ValueError("TESTS must be a literal list[str]")
            return value
    raise ValueError("literal TESTS registry not found")


def _head() -> str:
    try:
        return subprocess.check_output(
            ["git", "-C", str(ROOT), "rev-parse", "HEAD"],
            text=True, stderr=subprocess.DEVNULL, timeout=5,
        ).strip()
    except (OSError, subprocess.SubprocessError):
        return "unknown"


def _file_nodes(path: Path, relative: str) -> tuple[list[dict], str | None]:
    try:
        source = path.read_text(encoding="utf-8", errors="replace")
        tree = ast.parse(source, filename=str(path))
    except (OSError, SyntaxError) as exc:
        return [], f"{type(exc).__name__}:{exc}"
    nodes = []
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and (
            node.name.startswith("test_") or node.name.startswith("t_")
        ):
            nodes.append(
                {
                    "node_id": f"{relative}::{node.name}",
                    "function": node.name,
                    "line": int(node.lineno),
                }
            )
        elif isinstance(node, ast.ClassDef) and node.name.startswith("Test"):
            for child in node.body:
                if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)) and child.name.startswith("test_"):
                    nodes.append(
                        {
                            "node_id": f"{relative}::{node.name}::{child.name}",
                            "function": child.name,
                            "class": node.name,
                            "line": int(child.lineno),
                        }
                    )
    return nodes, None


def build() -> dict:
    registry = _registry()
    seen: dict[str, int] = {}
    for name in registry:
        seen[name] = seen.get(name, 0) + 1
    files = []
    all_nodes = []
    missing = []
    parse_errors = []
    zero_nodes = []
    for name in registry:
        path = HERE / name
        relative = f"_ops/tests/{name}"
        if not path.is_file():
            missing.append(relative)
            files.append({"path": relative, "exists": False, "nodes": []})
            continue
        nodes, error = _file_nodes(path, relative)
        row = {
            "path": relative,
            "exists": True,
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            "size": path.stat().st_size,
            "nodes": nodes,
        }
        if error:
            row["parse_error"] = error
            parse_errors.append({"path": relative, "error": error})
        elif not nodes:
            zero_nodes.append(relative)
        files.append(row)
        all_nodes.extend(nodes)
    node_ids = [row["node_id"] for row in all_nodes]
    duplicate_nodes = sorted({item for item in node_ids if node_ids.count(item) > 1})
    return {
        "schema": "octopus-test-node-map/1",
        "generated_at_unix": time.time(),
        "head": _head(),
        "registry": "_ops/tests/run_all.py:TESTS",
        "registered_files": len(registry),
        "unique_registered_files": len(seen),
        "duplicate_registry_entries": sorted(name for name, count in seen.items() if count > 1),
        "missing_registered_files": missing,
        "parse_errors": parse_errors,
        "zero_discovered_node_files": zero_nodes,
        "discovered_nodes": len(all_nodes),
        "duplicate_node_ids": duplicate_nodes,
        "files": files,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=HERE / "TEST-NODE-MAP.json")
    args = parser.parse_args()
    result = build()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: result[key] for key in (
        "registered_files", "unique_registered_files", "discovered_nodes",
        "duplicate_registry_entries", "missing_registered_files",
        "parse_errors", "duplicate_node_ids",
    )}, ensure_ascii=False, indent=2))
    return 1 if (
        result["duplicate_registry_entries"]
        or result["missing_registered_files"]
        or result["parse_errors"]
        or result["duplicate_node_ids"]
    ) else 0


if __name__ == "__main__":
    raise SystemExit(main())
