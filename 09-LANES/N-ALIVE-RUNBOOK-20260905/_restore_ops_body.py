#!/usr/bin/env python3
"""Restore missing tracked _ops code from HEAD. No state/.mimosa. No overwrite."""
from __future__ import annotations

import subprocess
from pathlib import Path

ROOT = Path(r"F:/backup")
SKIP_PREFIX = (
    "_ops/.mimosa/",
    "_ops/state/",
    "_ops/_agent_reports/",
)
# Never replace the live flag file or secrets overlay.
NEVER = {
    "_ops/OCTOPUS-flags.cmd",
    "_ops/OCTOPUS.env",
}


def git(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(ROOT), *args],
        text=True,
        capture_output=True,
        check=False,
    )


def main() -> int:
    tracked = git("ls-files", "_ops").stdout.splitlines()
    missing = []
    for rel in tracked:
        if rel in NEVER:
            continue
        if any(rel.startswith(p) for p in SKIP_PREFIX):
            continue
        if not (ROOT / rel).exists():
            missing.append(rel)
    print("missing_code", len(missing))
    if not missing:
        return 0
    # Clear skip-worktree so checkout can materialize.
    for i in range(0, len(missing), 80):
        chunk = missing[i : i + 80]
        r = git("update-index", "--no-skip-worktree", "--", *chunk)
        if r.returncode != 0:
            print("update-index_fail", r.returncode, r.stderr[-400:])
            return r.returncode or 1
    restored = 0
    failed = []
    for i in range(0, len(missing), 40):
        chunk = missing[i : i + 40]
        r = git("checkout", "HEAD", "--", *chunk)
        if r.returncode != 0:
            failed.extend(chunk)
            print("checkout_fail", r.returncode, r.stderr[-300:])
            continue
        restored += len(chunk)
    still = [rel for rel in missing if not (ROOT / rel).exists()]
    print("restored_attempted", restored)
    print("still_missing", len(still))
    for rel in still[:20]:
        print(" still", rel)
    key = [
        "_ops/budget/opslib.py",
        "_ops/wiring.py",
        "_ops/live_loop.py",
        "_ops/RUN-ORGANISM.bat",
        "_ops/telegram_center/center.py",
        "_ops/telegram_center/RUN-TG-CENTER.bat",
    ]
    print("key_exists")
    for rel in key:
        print(" ", int((ROOT / rel).exists()), rel)
    return 1 if still else 0


if __name__ == "__main__":
    raise SystemExit(main())
