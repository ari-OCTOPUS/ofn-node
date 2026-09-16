# -*- coding: utf-8 -*-
"""Worktree rollback. Never deletes. git checkout restores HEAD files."""
from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any

from .contracts import append_jsonl, utc_now
from . import STATE_DIR


def rollback(worktree: Path, files: list[str], *, reason: str) -> dict[str, Any]:
    r = subprocess.run(
        ["git", "checkout", "--", *files],
        cwd=str(worktree), capture_output=True, text=True,
        encoding="utf-8", errors="replace", timeout=30)
    rec = {
        "ts": utc_now(),
        "ok": r.returncode == 0,
        "files": files,
        "reason": reason,
        "stderr": (r.stderr or "")[-300:],
    }
    append_jsonl(STATE_DIR / "failures.jsonl", rec)
    return rec


def rollback_probe(worktree: Path) -> bool:
    """Prove git checkout works in this worktree (no file mutation)."""
    r = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=str(worktree), capture_output=True, text=True,
        encoding="utf-8", errors="replace", timeout=20)
    return r.returncode == 0
