# -*- coding: utf-8 -*-
"""Apply a bounded patch inside a worktree. Production tree is never the target."""
from __future__ import annotations

import hashlib
import subprocess
from pathlib import Path
from typing import Any

from . import LAB_DIR, ROOT
from .contracts import MAX_DIFF_LINES, MAX_PROD_FILES, sha16

_PROD_PREFIXES = ("_ops/",)


def _run(args: list[str], cwd: Path, timeout: int = 60) -> subprocess.CompletedProcess:
    return subprocess.run(
        args, cwd=str(cwd), capture_output=True, text=True,
        encoding="utf-8", errors="replace", timeout=timeout)


def _rel(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix()


def apply_unified_diff(worktree: Path, diff_path: Path, allowlist: list[str]) -> dict[str, Any]:
    raw = diff_path.read_bytes()
    text = raw.decode("utf-8", errors="replace")
    files = []
    for line in text.splitlines():
        if line.startswith("+++ b/"):
            files.append(line[6:].strip())
    prod_files = [f for f in files if not f.startswith("_ops/tests/")]
    if len(prod_files) > MAX_PROD_FILES:
        return {"ok": False, "reason": "too-many-prod-files", "files": prod_files}
    if text.count("\n") > MAX_DIFF_LINES * 3:  # unified diffs are ~3x line-change
        # still allow if actual +/- under cap; counted below after apply
        pass
    for f in files:
        if f != "/dev/null" and f not in allowlist:
            return {"ok": False, "reason": "allowlist-violation", "file": f, "allowlist": allowlist}
    r = _run(["git", "apply", "--whitespace=nowarn", str(diff_path)], cwd=worktree, timeout=30)
    if r.returncode != 0:
        r = _run(["git", "apply", "--3way", "--whitespace=nowarn", str(diff_path)],
                 cwd=worktree, timeout=30)
    if r.returncode != 0:
        return {"ok": False, "reason": "git-apply-failed",
                "stderr": (r.stderr or "")[-600:], "patch_hash": sha16(raw)}
    stat = _run(["git", "diff", "--numstat"], cwd=worktree, timeout=20)
    added = deleted = 0
    for line in (stat.stdout or "").splitlines():
        parts = line.split("\t")
        if len(parts) >= 2 and parts[0].isdigit() and parts[1].isdigit():
            added += int(parts[0]); deleted += int(parts[1])
    if added + deleted > MAX_DIFF_LINES:
        _run(["git", "checkout", "--", "."], cwd=worktree, timeout=20)
        return {"ok": False, "reason": "diff-too-large", "added": added, "deleted": deleted}
    return {"ok": True, "patch_hash": hashlib.sha256(raw).hexdigest()[:16],
            "files": files, "added": added, "deleted": deleted,
            "prod_files": prod_files}


def write_files(worktree: Path, files: dict[str, str], allowlist: list[str]) -> dict[str, Any]:
    """Write full-file replacements (for new tests)."""
    if len([f for f in files if not f.startswith("_ops/tests/")]) > MAX_PROD_FILES:
        return {"ok": False, "reason": "too-many-prod-files"}
    for rel, content in files.items():
        rel_n = rel.replace("\\", "/")
        if rel_n not in allowlist:
            return {"ok": False, "reason": "allowlist-violation", "file": rel_n}
        dest = worktree / rel_n
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(content, encoding="utf-8", newline="\n")
    blob = "\n".join(f"{k}\n{v}" for k, v in sorted(files.items())).encode("utf-8")
    return {"ok": True, "patch_hash": sha16(blob), "files": list(files),
            "added": sum(v.count("\n") + 1 for v in files.values()), "deleted": 0}


def apply_splices(worktree: Path, rel: str, replacements: list[tuple[str, str]],
                  allowlist: list[str]) -> dict[str, Any]:
    rel_n = rel.replace("\\", "/")
    if rel_n not in allowlist:
        return {"ok": False, "reason": "allowlist-violation", "file": rel_n}
    p = worktree / rel_n
    if not p.is_file():
        return {"ok": False, "reason": "missing", "file": rel_n}
    text = p.read_text(encoding="utf-8")
    for old, new in replacements:
        if old not in text:
            return {"ok": False, "reason": "anchor-not-found", "file": rel_n,
                    "anchor": old[:80]}
        text = text.replace(old, new, 1)
    if text.count("\n") > 20_000:
        return {"ok": False, "reason": "file-implausibly-large"}
    p.write_text(text, encoding="utf-8", newline="\n")
    return {"ok": True, "file": rel_n, "n_splices": len(replacements),
            "patch_hash": sha16(text.encode("utf-8"))}


def patch_hash_running(worktree: Path, rels: list[str]) -> str:
    h = hashlib.sha256()
    for rel in rels:
        p = worktree / rel
        if p.is_file():
            h.update(rel.encode()); h.update(p.read_bytes())
    return h.hexdigest()[:16]
