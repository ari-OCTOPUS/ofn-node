# -*- coding: utf-8 -*-
"""Experiment record + worktree factory. Worktrees live outside the live tree."""
from __future__ import annotations

import json
import os
import subprocess
import time
from pathlib import Path
from typing import Any

from . import LAB_DIR, ROOT
from .contracts import Experiment, append_jsonl, utc_now, write_json
from . import STATE_DIR

WT_ROOT = Path(r"F:\backup\.claude\worktrees")
BRANCH_PREFIX = "sul"
READY_NAME = ".sul-ready"
SPARSE_CONE = ["_ops"]


def _kill_tree(pid: int) -> None:
    if os.name == "nt":
        subprocess.run(
            ["taskkill", "/F", "/T", "/PID", str(pid)],
            capture_output=True, text=True, timeout=20)
        return
    try:
        os.killpg(pid, 9)
    except OSError:
        os.kill(pid, 9)


def _run(args: list[str], cwd: Path | None = None, timeout: int = 60) -> subprocess.CompletedProcess:
    popen_kw: dict[str, Any] = {
        "args": args,
        "cwd": str(cwd or ROOT),
        "stdout": subprocess.PIPE,
        "stderr": subprocess.PIPE,
        "text": True,
        "encoding": "utf-8",
        "errors": "replace",
    }
    if os.name == "nt":
        popen_kw["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP
    else:
        popen_kw["start_new_session"] = True
    p = subprocess.Popen(**popen_kw)
    try:
        stdout, stderr = p.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        _kill_tree(p.pid)
        try:
            p.wait(timeout=15)
        except subprocess.TimeoutExpired:
            pass
        raise
    return subprocess.CompletedProcess(args, p.returncode, stdout, stderr)


def existing_worktree(layer: str) -> Path | None:
    pointer = LAB_DIR / "worktrees" / layer / "WORKTREE.json"
    if not pointer.is_file():
        return None
    try:
        rec = json.loads(pointer.read_text(encoding="utf-8"))
    except ValueError:
        return None
    p = Path(rec.get("path") or "")
    return p if p.is_dir() and (p / READY_NAME).is_file() else None


def _abandon_incomplete(dest: Path) -> None:
    """Rename a partial checkout out of the way (O(1)); prune git metadata. Never wait on full rmtree."""
    if dest.exists():
        junk = dest.with_name(f"{dest.name}.partial-{int(time.time())}")
        try:
            dest.rename(junk)
        except OSError:
            _run(["git", "worktree", "remove", "--force", str(dest)], timeout=45)
    _run(["git", "worktree", "prune"], timeout=30)


def ensure_worktree(layer: str, cycle_id: str, base: str = "HEAD") -> dict[str, Any]:
    """Create (or reuse) an isolated git worktree. Never patches the live tree.

    Full-tree ``git worktree add`` on this vault exceeds 120s and leaves a
    half-checked-out dest whose ``.git`` made the next call reuse garbage.
    Lab tests only need tracked ``_ops``, so we add --no-checkout and cone-sparse.
    """
    dest = WT_ROOT / f"sul-{layer}"
    branch = f"{BRANCH_PREFIX}/{layer}-c1"
    pointer_dir = LAB_DIR / "worktrees" / layer
    pointer_dir.mkdir(parents=True, exist_ok=True)
    git_marker = dest / ".git"
    ops_dir = dest / "_ops"
    ready = dest / READY_NAME
    reuse = dest.is_dir() and ready.is_file() and ops_dir.is_dir()
    if reuse:
        rec = {"path": str(dest), "branch": branch, "reused": True, "cycle_id": cycle_id, "ts": utc_now()}
        write_json(pointer_dir / "WORKTREE.json", rec)
        return rec
    WT_ROOT.mkdir(parents=True, exist_ok=True)
    if dest.exists() or git_marker.exists():
        _abandon_incomplete(dest)
    r = _run(["git", "worktree", "add", "--no-checkout", "-B", branch, str(dest), base], timeout=45)
    if r.returncode != 0:
        raise RuntimeError(f"worktree add --no-checkout failed: {(r.stderr or r.stdout)[-500:]}")
    r2 = _run(["git", "-C", str(dest), "sparse-checkout", "init", "--cone"], timeout=30)
    if r2.returncode != 0:
        raise RuntimeError(f"sparse-checkout init failed: {(r2.stderr or r2.stdout)[-400:]}")
    r3 = _run(["git", "-C", str(dest), "sparse-checkout", "set", *SPARSE_CONE], timeout=90)
    if r3.returncode != 0:
        raise RuntimeError(f"sparse-checkout set failed: {(r3.stderr or r3.stdout)[-400:]}")
    # --no-checkout leaves an empty index; pathspec "_ops" is unknown until HEAD is materialized.
    r4 = _run(["git", "-C", str(dest), "checkout", "--force", "HEAD"], timeout=120)
    if r4.returncode != 0 or not ops_dir.is_dir():
        raise RuntimeError(f"sparse checkout HEAD failed: {(r4.stderr or r4.stdout)[-400:]}")
    ready.write_text(cycle_id + "\n", encoding="utf-8")
    rec = {"path": str(dest), "branch": branch, "reused": False,
           "sparse": True, "no_checkout": True,
           "stdout": (r.stdout or "")[-200:], "cycle_id": cycle_id, "base": base, "ts": utc_now()}
    write_json(pointer_dir / "WORKTREE.json", rec)
    return rec


def record_experiment(exp: Experiment) -> None:
    append_jsonl(STATE_DIR / "experiments.jsonl", {**exp.to_dict(), "ts": utc_now()})
