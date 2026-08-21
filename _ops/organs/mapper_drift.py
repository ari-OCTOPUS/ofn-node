# -*- coding: utf-8 -*-
"""T69 — turn cartographer drift *count* into actionable lists. Read-only."""
from __future__ import annotations

import ast
import hashlib
import json
import os
import re
import sys
import time
from datetime import datetime
from pathlib import Path

from .flags import enabled
from .paths import ORGANS_STATE, SKIP_DIR_NAMES, VAULT, assert_not_telegram

MAP_GLOB = "MASTER-ARCHITECTURE-*.md"


def _map_cutoff(vault: Path) -> tuple[str | None, float | None]:
    maps_dir = vault / "06 - Architecture Maps"
    try:
        maps = sorted(maps_dir.glob(MAP_GLOB))
    except OSError:
        return None, None
    if not maps:
        return None, None
    latest = maps[-1]
    try:
        text = latest.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None, None
    m = re.search(r"^updated:\s*(\S+)", text, re.M)
    updated = m.group(1).strip() if m else None
    if not updated:
        return None, None
    try:
        return updated, datetime.fromisoformat(updated).timestamp()
    except ValueError:
        return updated, None


def _iter_py(root: Path) -> list[Path]:
    out: list[Path] = []
    stack = [root]
    while stack:
        cur = stack.pop()
        try:
            with os.scandir(cur) as it:
                for ent in it:
                    if ent.name in SKIP_DIR_NAMES or ent.name.startswith("."):
                        continue
                    if ent.name in {"state", "_bak", "node_modules"}:
                        continue
                    p = Path(ent.path)
                    if ent.is_dir(follow_symlinks=False):
                        stack.append(p)
                    elif ent.is_file(follow_symlinks=False) and ent.name.endswith(".py"):
                        out.append(p)
        except OSError:
            continue
    return out


def _file_hash(path: Path) -> str:
    h = hashlib.sha256()
    try:
        with path.open("rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                h.update(chunk)
        return h.hexdigest()[:16]
    except OSError:
        return ""


def _dead_imports(files: list[Path], vault: Path) -> list[dict]:
    names = {p.stem for p in files}
    dead = []
    for p in files:
        try:
            src = p.read_text(encoding="utf-8", errors="replace")
            tree = ast.parse(src)
        except (OSError, SyntaxError, ValueError):
            continue
        imported: list[str] = []
        for n in ast.walk(tree):
            if isinstance(n, ast.Import):
                imported.extend(a.name.split(".")[0] for a in n.names)
            elif isinstance(n, ast.ImportFrom) and n.module:
                imported.append(n.module.split(".")[0])
        stdlib = set(getattr(sys, "stdlib_module_names", ()))
        stdlib.update({
            "os", "sys", "json", "re", "time", "pathlib", "typing",
            "dataclasses", "collections", "hashlib", "ast", "uuid",
            "argparse", "tempfile", "datetime", "functools",
        })
        for name in imported:
            if name.startswith("_"):
                continue
            if name in names:
                continue
            if name in stdlib:
                continue
            candidate = vault / "_ops" / f"{name}.py"
            pkg = vault / "_ops" / name / "__init__.py"
            if (not candidate.exists()) and (not pkg.exists()) and name.replace("_", "").isalnum():
                if any(name == x for x in ("opslib", "wiring", "organism")):
                    continue
                dead.append({"importer": str(p.relative_to(vault)).replace("\\", "/"),
                             "missing": name})
                if len(dead) >= 40:
                    return dead
    return dead


def scan(*, vault: Path | None = None, emit: bool = True,
         state_root: Path | None = None, include_orphan_scan: bool = False) -> dict:
    if not enabled("mapper_drift_lists", True):
        return {"ok": False, "reason": "flag-off"}
    vault = Path(vault) if vault is not None else VAULT
    ops = vault / "_ops"
    updated, cutoff = _map_cutoff(vault)
    files = _iter_py(ops)
    modified = []
    for p in files:
        try:
            st = p.stat()
        except OSError:
            continue
        if cutoff is not None and st.st_mtime > cutoff:
            try:
                rel = str(p.relative_to(vault)).replace("\\", "/")
            except ValueError:
                rel = str(p)
            modified.append({
                "path": rel,
                "mtime": st.st_mtime,
                "hash16": _file_hash(p),
                "bytes": st.st_size,
            })
    modified.sort(key=lambda r: r["mtime"], reverse=True)

    # duplicate capability heuristic: same stem in different folders
    by_stem: dict[str, list[str]] = {}
    for p in files:
        by_stem.setdefault(p.stem, []).append(str(p.relative_to(vault)).replace("\\", "/"))
    dupes = {k: v for k, v in by_stem.items() if len(v) >= 2 and not k.startswith("test_")}
    # keep a short actionable subset
    dup_cap = [{"name": k, "paths": v} for k, v in sorted(dupes.items()) if len(v) >= 2][:30]

    untested = []
    test_dir = ops / "tests"
    tested_stems = set()
    if test_dir.is_dir():
        for tp in test_dir.glob("test_*.py"):
            tested_stems.add(tp.stem.replace("test_", "", 1))
    for p in files:
        if p.parent.name == "tests" or p.name.startswith("test_"):
            continue
        stem = p.stem
        if stem not in tested_stems and f"test_{stem}" not in {x.stem for x in (test_dir.glob("test_*.py") if test_dir.is_dir() else [])}:
            untested.append(str(p.relative_to(vault)).replace("\\", "/"))
    untested = untested[:80]

    orphans = []
    orphan_meta = {}
    if include_orphan_scan:
        try:
            import sys
            if str(ops) not in sys.path:
                sys.path.insert(0, str(ops))
            import orphan_scan  # noqa: WPS433
            os_scan = orphan_scan.scan()
            orphan_meta = {"checked": os_scan.get("checked"), "total": os_scan.get("total")}
            for row in os_scan.get("orphans") or []:
                if isinstance(row, dict):
                    orphans.append(row)
                else:
                    orphans.append({"module": str(row)})
        except Exception as e:  # noqa: BLE001
            orphan_meta = {"error": type(e).__name__}

    dead = _dead_imports(files[:200], vault)  # bounded

    payload = {
        "ok": True,
        "schema": "mapper-drift/1",
        "map_updated": updated,
        "cutoff_unix": cutoff,
        "new_files": [],  # no prior inventory snapshot — cannot claim births
        "deleted_files": [],  # same
        "modified_files": modified[:400],
        "modified_count": len(modified),
        "orphan_modules": orphans[:200],
        "orphan_meta": orphan_meta,
        "dead_imports": dead,
        "duplicate_capabilities": dup_cap,
        "untested_modules": untested,
        "inventory_note": (
            "new/deleted require a previous hash inventory; this session has none, "
            "so those lists stay empty rather than fabricated. modified_files = "
            "_ops/*.py with mtime > MASTER-ARCHITECTURE updated: — same rule as "
            "wiring._cartographer_map_signal, but with paths."
        ),
        "ts": time.time(),
        "executable": False,
    }
    if emit:
        dest = (Path(state_root) if state_root is not None else ORGANS_STATE) / "mapper-drift.json"
        assert_not_telegram(dest)
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        payload["ledger"] = str(dest)
    return payload
