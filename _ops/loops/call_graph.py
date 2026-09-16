# -*- coding: utf-8 -*-
"""AST call graph for eight vital paths. Read-only. No execution of targets."""
from __future__ import annotations

import ast
import json
from pathlib import Path
from typing import Any

_OPS = Path(__file__).resolve().parent.parent
_ROOT = _OPS.parent

VITAL_PATHS = (
    ("telegram_center", "_ops/telegram_center/center.py"),
    ("miniapp_gateway", "_ops/telegram_center/miniapp_gateway.py"),
    ("durable_loop", "_ops/telegram_center/durable_loop.py"),
    ("telegram_organ", "_ops/loops/telegram_organ.py"),
    ("improve", "_ops/cortex/improve.py"),
    ("calibration_probe", "_ops/cortex/calibration_probe.py"),
    ("self_insight", "_ops/self_insight.py"),
    ("self_knowledge", "_ops/doctor/self_knowledge.py"),
    ("cockpit_brain", "_ops/cockpit_brain.py"),
    ("doctor_daemon", "OCTOPUS-DOCTOR/doctor/daemon.py"),
    ("telegram_adapter", "_ops/intel_spine/telegram_adapter.py"),
    ("memory_gate", "_ops/memory/gate.py"),
    ("organism", "_ops/organism.py"),
    ("orphan_watchdog", "_ops/orphan_watchdog.py"),
)


def _name(node: ast.AST) -> str:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return f"{_name(node.value)}.{node.attr}"
    if isinstance(node, ast.Call):
        return _name(node.func)
    return type(node).__name__


def analyze_file(rel: str) -> dict[str, Any]:
    path = _ROOT / rel
    out: dict[str, Any] = {
        "path": rel,
        "exists": path.is_file(),
        "bytes": path.stat().st_size if path.is_file() else 0,
        "imports": [],
        "functions": [],
        "calls": [],
        "parse_error": None,
    }
    if not path.is_file():
        return out
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=rel)
    except (SyntaxError, UnicodeDecodeError) as e:
        out["parse_error"] = f"{type(e).__name__}: {e}"
        return out
    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            if isinstance(node, ast.Import):
                for a in node.names:
                    out["imports"].append(a.name)
            else:
                mod = node.module or ""
                out["imports"].append(mod)
        elif isinstance(node, ast.FunctionDef):
            out["functions"].append(node.name)
        elif isinstance(node, ast.Call):
            out["calls"].append(_name(node.func))
    # unique, stable order, capped (center.py is huge)
    out["imports"] = sorted(set(out["imports"]))
    out["functions"] = sorted(set(out["functions"]))
    seen, uniq = set(), []
    for c in out["calls"]:
        if c not in seen:
            seen.add(c)
            uniq.append(c)
    out["n_calls"] = len(uniq)
    out["calls"] = uniq[:80]
    return out


def graph() -> dict[str, Any]:
    nodes = []
    edges = []
    for key, rel in VITAL_PATHS:
        info = analyze_file(rel)
        info["id"] = key
        nodes.append(info)
        for imp in info.get("imports") or []:
            for other, orel in VITAL_PATHS:
                stem = Path(orel).stem
                if imp == stem or imp.endswith("." + stem):
                    edges.append({"from": key, "to": other, "via": imp})
    return {
        "schema": "loop-call-graph/1",
        "n_paths": len(VITAL_PATHS),
        "parsed": sum(1 for n in nodes if n.get("exists") and not n.get("parse_error")),
        "nodes": nodes,
        "edges": edges,
    }


def write(dest: Path) -> dict[str, Any]:
    g = graph()
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(g, ensure_ascii=False, indent=2), encoding="utf-8")
    return g
