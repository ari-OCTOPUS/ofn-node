# -*- coding: utf-8 -*-
"""Impact-based test runner with a tiny result cache. Never hangs the whole lab
on one timeout — isolate, budget, move on."""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

from . import STATE_DIR
from .contracts import sha16, utc_now, write_json

CACHE = STATE_DIR / "test-cache.json"


def _cache() -> dict:
    try:
        return json.loads(CACHE.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def _save_cache(c: dict) -> None:
    write_json(CACHE, c)


def _key(worktree: Path, rel: str) -> str:
    p = worktree / rel
    st = p.stat() if p.is_file() else None
    head = ""
    dirty = ""
    try:
        head = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=str(worktree),
            text=True, encoding="utf-8", errors="replace").strip()
        dirty = subprocess.check_output(
            ["git", "status", "--porcelain"], cwd=str(worktree),
            text=True, encoding="utf-8", errors="replace")
    except (OSError, subprocess.CalledProcessError):
        pass
    raw = f"{rel}|{st.st_mtime_ns if st else 0}|{st.st_size if st else 0}|{head}|{sha16(dirty.encode())}"
    return sha16(raw.encode())


def run_one(worktree: Path, rel: str, *, timeout_s: int = 90,
            extra_env: dict | None = None) -> dict[str, Any]:
    """Run a single test file in the worktree. Cache green+unchanged."""
    cache = _cache()
    ck = _key(worktree, rel)
    hit = cache.get(ck)
    if hit and hit.get("status") == "PASS" and hit.get("rel") == rel:
        return {**hit, "cache_hit": True, "ts": utc_now()}
    env = dict(**{**__import__("os").environ, **(extra_env or {})})
    env.setdefault("PYTHONUTF8", "1")
    env["PYTHONPATH"] = str(worktree / "_ops") + __import__("os").pathsep + env.get("PYTHONPATH", "")
    cmd = [sys.executable, "-X", "utf8", str(worktree / rel)]
    t0 = time.time()
    try:
        r = subprocess.run(
            cmd, cwd=str(worktree), capture_output=True, text=True,
            encoding="utf-8", errors="replace", timeout=timeout_s, env=env)
        status = "PASS" if r.returncode == 0 else "FAIL"
        rec = {
            "rel": rel, "status": status, "exit": r.returncode,
            "duration_s": round(time.time() - t0, 3),
            "stdout_tail": (r.stdout or "")[-800:],
            "stderr_tail": (r.stderr or "")[-400:],
            "cache_hit": False, "ts": utc_now(),
        }
    except subprocess.TimeoutExpired:
        rec = {"rel": rel, "status": "TIMEOUT", "exit": -1,
               "duration_s": timeout_s, "cache_hit": False, "ts": utc_now()}
    if rec["status"] == "PASS":
        cache[ck] = {k: rec[k] for k in ("rel", "status", "exit", "duration_s")}
        _save_cache(cache)
    return rec


def run_many(worktree: Path, rels: list[str], **kw) -> dict[str, Any]:
    rows = [run_one(worktree, rel, **kw) for rel in rels]
    passed = sum(1 for r in rows if r["status"] == "PASS")
    return {
        "n": len(rows), "passed": passed, "failed": sum(1 for r in rows if r["status"] == "FAIL"),
        "timeouts": sum(1 for r in rows if r["status"] == "TIMEOUT"),
        "all_pass": passed == len(rows) and len(rows) > 0,
        "rows": rows,
    }
