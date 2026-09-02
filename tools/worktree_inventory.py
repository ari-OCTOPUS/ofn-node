#!/usr/bin/env python3
"""Read-only git worktree inventory.

Classifies each registered worktree as VERIFIED / SUSPECTED / UNKNOWN.
Never prunes, never removes, never writes into a worktree.

UNKNOWN is not FALSE: a timeout or unreadable lock is UNKNOWN, not proof
of concurrent writing, and not proof of absence.

Usage:
    python3 tools/worktree_inventory.py            # this repo, stdout
    python3 tools/worktree_inventory.py --json     # machine-readable
    python3 tools/worktree_inventory.py --porcelain-file PATH
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from typing import Any

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

VERIFIED = "VERIFIED"
SUSPECTED = "SUSPECTED"
UNKNOWN = "UNKNOWN"
STATUSES = (VERIFIED, SUSPECTED, UNKNOWN)


def parse_porcelain(text: str) -> list[dict[str, str]]:
    """Parse ``git worktree list --porcelain`` into one dict per worktree.

    Fields we keep: worktree, head, branch, bare, detached, locked, prunable.
    ``prunable`` is recorded as a fact the inventory saw — this tool still
    does not prune.
    """
    entries: list[dict[str, str]] = []
    current: dict[str, str] = {}
    for raw in text.splitlines():
        line = raw.rstrip("\n")
        if not line:
            if current:
                entries.append(current)
                current = {}
            continue
        if line.startswith("worktree "):
            if current:
                entries.append(current)
            current = {"worktree": line.split(" ", 1)[1]}
        elif line.startswith("HEAD "):
            current["head"] = line.split(" ", 1)[1]
        elif line.startswith("branch "):
            current["branch"] = line.split(" ", 1)[1]
        elif line == "bare":
            current["bare"] = "1"
        elif line == "detached":
            current["detached"] = "1"
        elif line.startswith("locked"):
            current["locked"] = line[len("locked"):].strip() or "1"
        elif line.startswith("prunable"):
            current["prunable"] = line[len("prunable"):].strip() or "1"
        # unknown porcelain keys are ignored, not guessed
    if current:
        entries.append(current)
    return entries


def _pointer_is_absolute(path: str) -> bool:
    """A gitdir line is absolute if git wrote it that way.

    Do not ask ntpath to rewrite a POSIX ``/repo/...`` pointer: that
    prepends a drive letter and is a different path. Leading ``/`` or
    ``\\``, or a Windows drive letter, all count as already-absolute.
    """
    if not path:
        return False
    if path.startswith("/") or path.startswith("\\"):
        return True
    if len(path) >= 2 and path[1] == ":" and path[0].isalpha():
        return True
    return os.path.isabs(path)


def read_gitdir_pointer(git_file: str) -> str | None:
    """Parse a linked-worktree ``.git`` *file* for ``gitdir: PATH``.

    Unreadable or malformed → None. The caller must treat None as
    UNKNOWN (not “no lock”, not FALSE).
    """
    try:
        with open(git_file, encoding="utf-8") as fh:
            text = fh.read()
    except OSError:
        return None
    for line in text.splitlines():
        if line.startswith("gitdir:"):
            path = line.split(":", 1)[1].strip()
            if not path:
                return None
            # Absolute pointers stay exactly as git wrote them. On
            # Windows, os.path.normpath("/repo/...") becomes
            # C:\repo\... — that is a second body, not a parse.
            # A leading slash or backslash, or a drive letter, is
            # already absolute even when ntpath.isabs disagrees.
            if _pointer_is_absolute(path):
                return path
            # Relative pointers are relative to the .git *file*, not CWD.
            # Resolving against CWD would be a second body.
            base = os.path.dirname(os.path.abspath(git_file))
            return os.path.normpath(os.path.join(base, path))
    return None


def index_lock_present(path: str) -> tuple[bool, bool]:
    """Return ``(lock_present, lock_unknown)``.

    A regular repo looks at ``.git/index.lock``. A linked worktree
    follows the ``gitdir:`` pointer. An unreadable pointer is
    ``lock_unknown=True`` — UNKNOWN, not proof of absence.
    """
    git = os.path.join(path, ".git")
    if os.path.isdir(git):
        return os.path.isfile(os.path.join(git, "index.lock")), False
    if os.path.isfile(git):
        pointed = read_gitdir_pointer(git)
        if pointed is None:
            return False, True
        # A gitdir that is itself a symlink is not a path we verified.
        # UNKNOWN, not "no lock".
        if os.path.islink(pointed):
            return False, True
        lock = os.path.isfile(os.path.join(pointed, "index.lock"))
        lock = lock or os.path.isfile(os.path.join(path, ".git.lock"))
        return lock, False
    return False, False


def classify(
    entry: dict[str, str],
    *,
    status_ok: bool | None,
    lock_present: bool,
    timeout: bool,
) -> str:
    """Lock-zone verdict for one worktree.

    timeout or status_ok is None → UNKNOWN (not SUSPECTED, not VERIFIED).
    lock present or dirty status → SUSPECTED.
    otherwise → VERIFIED.
    """
    if timeout or status_ok is None:
        return UNKNOWN
    if lock_present or "locked" in entry or not status_ok:
        return SUSPECTED
    return VERIFIED


def _git(args: list[str], cwd: str, timeout_s: float) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", *args],
        cwd=cwd,
        capture_output=True,
        text=True,
        timeout=timeout_s,
        check=False,
    )


def inventory(repo: str, *, timeout_s: float = 8.0) -> dict[str, Any]:
    """Read-only census. Failures become UNKNOWN rows, not invented absences."""
    try:
        listed = _git(["worktree", "list", "--porcelain"], repo, timeout_s)
    except subprocess.TimeoutExpired:
        return {
            "ok": False,
            "classification": UNKNOWN,
            "reason": "worktree-list-timeout",
            "worktrees": [],
        }
    if listed.returncode != 0:
        return {
            "ok": False,
            "classification": UNKNOWN,
            "reason": "worktree-list-failed",
            "worktrees": [],
        }

    rows = []
    for entry in parse_porcelain(listed.stdout):
        path = entry.get("worktree", "")
        timeout = False
        status_ok: bool | None = None
        lock_present = False
        if path:
            lock_present, lock_unknown = index_lock_present(path)
            try:
                st = _git(["status", "--porcelain"], path, timeout_s)
                status_ok = st.returncode == 0 and st.stdout.strip() == ""
            except subprocess.TimeoutExpired:
                timeout = True
                status_ok = None
            if lock_unknown:
                # Unreadable gitdir pointer: not proof of no lock.
                status_ok = None
        verdict = classify(
            entry,
            status_ok=status_ok,
            lock_present=lock_present,
            timeout=timeout,
        )
        row = dict(entry)
        row["status"] = verdict
        row["lock_present"] = "1" if lock_present else "0"
        rows.append(row)

    counts = {s: sum(1 for r in rows if r["status"] == s) for s in STATUSES}
    return {
        "ok": True,
        "classification": "census",
        "counts": counts,
        "worktrees": rows,
        "pruned": False,
        "wrote": False,
    }


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--json", action="store_true")
    p.add_argument("--repo", default=ROOT)
    p.add_argument("--porcelain-file", default="",
                   help="parse this file instead of calling git (tests)")
    args = p.parse_args(argv)

    if args.porcelain_file:
        with open(args.porcelain_file, encoding="utf-8") as fh:
            parsed = parse_porcelain(fh.read())
        report = {
            "ok": True,
            "classification": "parsed-only",
            "worktrees": parsed,
            "pruned": False,
            "wrote": False,
        }
    else:
        report = inventory(args.repo)

    if args.json:
        json.dump(report, sys.stdout, indent=2, sort_keys=True)
        sys.stdout.write("\n")
    else:
        print(f"ok={report.get('ok')} pruned={report.get('pruned')} "
              f"wrote={report.get('wrote')}")
        for row in report.get("worktrees", []):
            print(f"  {row.get('status', '-'):9} {row.get('worktree', '')} "
                  f"{row.get('branch', row.get('detached', ''))}")
    return 0 if report.get("ok") else 2


if __name__ == "__main__":
    sys.exit(main())
