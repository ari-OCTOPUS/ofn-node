# -*- coding: utf-8 -*-
"""Structural parsers for capability registries. No regex over Python source."""
from __future__ import annotations

import ast
import json
from pathlib import Path
from typing import Any

try:
    import yaml  # type: ignore
except ImportError:  # noqa: BLE001
    yaml = None


def _literal(node: ast.AST) -> Any:
    if isinstance(node, ast.Constant):
        return node.value
    if isinstance(node, ast.Name) and node.id in ("None", "True", "False"):
        return {"None": None, "True": True, "False": False}[node.id]
    if isinstance(node, ast.Tuple):
        return tuple(_literal(x) for x in node.elts)
    if isinstance(node, ast.List):
        return [_literal(x) for x in node.elts]
    if isinstance(node, ast.JoinedStr):  # f-string — treat as UNPARSED
        return None
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
        left, right = _literal(node.left), _literal(node.right)
        if isinstance(left, str) and isinstance(right, str):
            return left + right
    raise ValueError(f"non-literal: {type(node).__name__}")


def _dict_from_ast(node: ast.Dict) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for k, v in zip(node.keys, node.values):
        if k is None:
            continue
        key = _literal(k)
        if not isinstance(key, str):
            continue
        if isinstance(v, ast.Dict):
            out[key] = _dict_from_ast(v)
        else:
            try:
                out[key] = _literal(v)
            except ValueError:
                out[key] = {"_unparsed": type(v).__name__}
    return out


def parse_effectors_py(path: Path) -> dict[str, Any]:
    tree = ast.parse(path.read_text(encoding="utf-8", errors="replace"))
    for node in tree.body:
        if not isinstance(node, ast.Assign):
            continue
        if not any(isinstance(t, ast.Name) and t.id == "EFFECTORS" for t in node.targets):
            continue
        if not isinstance(node.value, ast.Dict):
            raise ValueError("EFFECTORS is not a dict literal")
        return _dict_from_ast(node.value)
    raise ValueError("EFFECTORS assignment not found")


def parse_json_capabilities(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, dict) and "capabilities" in data:
        caps = data["capabilities"]
        if isinstance(caps, dict):
            return caps
        if isinstance(caps, list):
            return {str(c.get("id") or c.get("name")): c for c in caps if isinstance(c, dict)}
    if isinstance(data, dict):
        return data
    raise ValueError("unrecognized JSON capability schema")


def parse_yaml_capabilities(path: Path) -> dict[str, Any]:
    if yaml is None:
        raise RuntimeError("PyYAML UNLOCATED — cannot parse YAML capabilities")
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("YAML root is not a mapping")
    caps = data.get("capabilities", data)
    if isinstance(caps, dict):
        return caps
    raise ValueError("unrecognized YAML capability schema")


def parse_capability_file(path: Path) -> dict[str, Any]:
    p = Path(path)
    suf = p.suffix.lower()
    if suf == ".py":
        return parse_effectors_py(p)
    if suf == ".json":
        return parse_json_capabilities(p)
    if suf in (".yml", ".yaml"):
        return parse_yaml_capabilities(p)
    if suf == ".toml":
        import tomllib
        data = tomllib.loads(p.read_text(encoding="utf-8"))
        caps = data.get("capabilities", data)
        if isinstance(caps, dict):
            return caps
        raise ValueError("unrecognized TOML capability schema")
    raise ValueError(f"unsupported suffix {suf}")
