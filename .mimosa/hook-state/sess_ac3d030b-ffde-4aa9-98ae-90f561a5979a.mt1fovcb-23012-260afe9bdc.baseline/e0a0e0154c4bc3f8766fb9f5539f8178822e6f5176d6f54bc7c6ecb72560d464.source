#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Fast class-level unwired sweep (read-only). JSON to stdout."""
from __future__ import annotations

import ast
import json
import os
import re
import sys
import time
from pathlib import Path

ROOT = Path(r"F:\backup")
SKIP_DIR = {
    "tests", "__pycache__", "_bak", ".git", "eval", "smoke",
    "worktrees", ".claude", "node_modules", "_Archive", "_Duplicates",
    "venv", ".venv", "_code", "nbb-cp-kre",
}
# nbb_cp src is a separate product stack; still scanned under 4d_system/src
COMMON_CLASS = {
    "Exception", "Error", "Handler", "Thread", "Lock", "Path", "Enum",
}


def is_test(p: Path) -> bool:
    parts = {x.lower() for x in p.parts}
    if "tests" in parts:
        return True
    n = p.name
    return n.startswith("test_") or n.endswith("_test.py")


def skip_dir(p: Path) -> bool:
    return bool(set(p.parts) & SKIP_DIR)


def iter_py(base: Path, tests: bool) -> list[Path]:
    out = []
    for f in base.rglob("*.py"):
        if "__pycache__" in f.parts:
            continue
        if skip_dir(f) and not (tests and "tests" in f.parts):
            if is_test(f) and tests:
                out.append(f)
            continue
        if is_test(f):
            if tests:
                out.append(f)
            continue
        if not tests:
            out.append(f)
    return out


def class_defs(src: str) -> list[dict]:
    try:
        tree = ast.parse(src)
    except SyntaxError:
        return []
    items = []
    for n in tree.body:
        if isinstance(n, ast.ClassDef) and not n.name.startswith("_"):
            items.append({
                "name": n.name,
                "lineno": n.lineno,
                "end": getattr(n, "end_lineno", n.lineno) or n.lineno,
            })
    return items


def main() -> None:
    t0 = time.time()
    scopes = [ROOT / "_ops", ROOT / "4d_system"]
    prod, tests = [], []
    for base in scopes:
        prod.extend(iter_py(base, False))
        tests.extend(iter_py(base, True))
    prod = sorted(set(prod))
    tests = sorted(set(tests))

    defs = []
    for f in prod:
        try:
            src = f.read_text("utf-8", errors="replace")
        except OSError:
            continue
        rel = str(f.relative_to(ROOT)).replace("\\", "/")
        mtime = int(f.stat().st_mtime)
        for d in class_defs(src):
            defs.append({
                "rel": rel,
                "name": d["name"],
                "lineno": d["lineno"],
                "span": d["end"] - d["lineno"] + 1,
                "mtime": mtime,
            })

    # Load production + test texts once
    prod_text = {}
    for f in prod:
        try:
            prod_text[str(f.relative_to(ROOT)).replace("\\", "/")] = f.read_text(
                "utf-8", errors="replace")
        except OSError:
            continue
    test_text = {}
    for f in tests:
        try:
            test_text[str(f.relative_to(ROOT)).replace("\\", "/")] = f.read_text(
                "utf-8", errors="replace")
        except OSError:
            continue

    # Precompile name regexes for unique-enough class names
    name_count: dict[str, int] = {}
    for d in defs:
        name_count[d["name"]] = name_count.get(d["name"], 0) + 1

    candidates = []
    for d in defs:
        name = d["name"]
        if name in COMMON_CLASS:
            continue
        if name_count[name] > 4:
            continue  # too ambiguous (Handler, etc.)
        pat = re.compile(r"\b" + re.escape(name) + r"\b")
        prod_hits = []
        for rel, txt in prod_text.items():
            if rel == d["rel"]:
                continue
            n = len(pat.findall(txt))
            if n:
                prod_hits.append((rel, n))
        test_hits = []
        for rel, txt in test_text.items():
            n = len(pat.findall(txt))
            if n:
                test_hits.append((rel, n))
        n_prod = sum(x[1] for x in prod_hits)
        n_test = sum(x[1] for x in test_hits)
        if n_prod > 0:
            continue
        candidates.append({
            **d,
            "name_collisions": name_count[name],
            "prod_hits": n_prod,
            "test_hits": n_test,
            "test_files": [x[0] for x in test_hits[:6]],
            "has_tests": n_test > 0,
        })

    candidates.sort(key=lambda r: (-int(r["has_tests"]), -r["span"], r["rel"]))
    out = {
        "schema": "unwired-class-scan.v1",
        "prod_files": len(prod),
        "test_files": len(tests),
        "public_classes": len(defs),
        "candidates": len(candidates),
        "with_tests": sum(1 for c in candidates if c["has_tests"]),
        "elapsed_s": round(time.time() - t0, 2),
        "rows": candidates,
    }
    json.dump(out, sys.stdout, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    main()
