"""Backup -- the 3-2-1 local snapshot (copy #2) + optional git commit (versioned
copy #1) + a ledger log so the Guardian sees a fresh backup age.

  * git commit   : versions the live folder in place (copy #1, if git is available)
  * snapshot     : a timestamped .tar.gz in ../_backups (copy #2, a second location)
  * off-site (#3): NOT done automatically -- your data never leaves the machine
                   without you. The script prints the restic/rclone command to run.

Excludes rebuildable / heavy stuff (index.db, __pycache__). Keeps the last 7
snapshots. Cross-platform (pure stdlib).

Usage:  python scripts/backup.py [target_dir]        # default: the genome-system root
"""
from __future__ import annotations

import shutil
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "ledger"))
from ledger import Ledger           # noqa: E402


def git_commit(target: Path) -> str:
    try:
        subprocess.run(["git", "-C", str(target), "init", "-q"], check=True)
        subprocess.run(["git", "-C", str(target), "add", "-A"], check=True)
        r = subprocess.run(
            ["git", "-C", str(target), "commit", "-q", "-m",
             f"backup {time.strftime('%Y-%m-%d %H:%M:%S')}"],
            capture_output=True, text=True)
        return "committed" if r.returncode == 0 else "nothing-to-commit"
    except Exception as exc:                       # git not installed / not a repo
        return f"git-skipped ({exc})"


def snapshot(target: Path, out_dir: Path) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    ts = time.strftime("%Y%m%d-%H%M%S")
    staging = out_dir / f".staging-{ts}"
    shutil.copytree(target, staging, ignore=shutil.ignore_patterns(
        "__pycache__", "*.pyc", "*.db", "_backups", ".git"))
    archive = shutil.make_archive(str(out_dir / f"{target.name}-{ts}"),
                                  "gztar", root_dir=staging)
    shutil.rmtree(staging, ignore_errors=True)
    return Path(archive)


def prune(out_dir: Path, keep: int = 7) -> int:
    arcs = sorted(out_dir.glob(f"{ROOT.name}-*.tar.gz"))
    removed = 0
    for a in arcs[:-keep]:
        a.unlink()
        removed += 1
    return removed


def main() -> int:
    target = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT
    out_dir = target.parent / "_backups"

    git_state = git_commit(target)
    archive = snapshot(target, out_dir)
    pruned = prune(out_dir)

    Ledger(ROOT / "ledger" / "ledger.jsonl").append(
        "METRIC",
        {"backup_last_success_age_h": 0, "archive": archive.name,
         "git": git_state, "pruned": pruned},
        actor="backup")

    size_kb = archive.stat().st_size / 1024
    print(f"backup OK  git={git_state}  archive={archive.name} ({size_kb:.0f} KB)  pruned={pruned}")
    print("off-site copy #3 (configure once, then it is one command):")
    print(f"  restic -r <repo> backup \"{out_dir}\"        # or")
    print(f"  rclone copy \"{out_dir}\" <encrypted-remote>")
    return 0


if __name__ == "__main__":
    sys.exit(main())
