#!/usr/bin/env python3
from __future__ import annotations

import subprocess
from pathlib import Path

ROOT = Path(r"F:/backup")
SKIP_PREFIX = ("_ops/.mimosa/", "_ops/state/", "_ops/_agent_reports/")
NEVER = {"_ops/OCTOPUS-flags.cmd", "_ops/OCTOPUS.env"}


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
        if rel in NEVER or any(rel.startswith(p) for p in SKIP_PREFIX):
            continue
        if not (ROOT / rel).exists():
            missing.append(rel)
    print("retry_missing", len(missing))
    ok = 0
    for rel in missing:
        git("update-index", "--no-skip-worktree", "--", rel)
        r = git("checkout", "HEAD", "--", rel)
        if r.returncode == 0 and (ROOT / rel).exists():
            ok += 1
        else:
            print("fail", rel, r.returncode, (r.stderr or "")[-120:])
    still = [rel for rel in missing if not (ROOT / rel).exists()]
    print("retry_ok", ok, "still", len(still))
    return 0 if not still else 1


if __name__ == "__main__":
    raise SystemExit(main())
