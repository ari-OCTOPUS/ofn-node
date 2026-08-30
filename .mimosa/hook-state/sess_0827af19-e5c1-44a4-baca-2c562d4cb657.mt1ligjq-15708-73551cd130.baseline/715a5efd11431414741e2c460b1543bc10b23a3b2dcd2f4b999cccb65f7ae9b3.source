"""Backup -- the 3-2-1 local snapshot (copy #2) + optional git commit (versioned
copy #1) + a ledger log so the Guardian sees a fresh backup age.

  * git commit   : versions the live folder in place (copy #1, if git is usable)
  * snapshot     : a timestamped .tar.gz in ../_backups (copy #2, a second place)
  * off-site (#3): NOT automatic -- your data never leaves the machine without
                   you. The script prints the restic/rclone command to run.

Streams straight into a .tar.gz with an exclusion filter (no temp staging copy),
excluding rebuildable/heavy things (*.db, __pycache__, .git). Keeps the last 7
snapshots. Pure stdlib, cross-platform.

Usage:  python scripts/backup.py [target_dir]     # default: the genome-system root
"""
from __future__ import annotations

import subprocess
import sys
import tarfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "ledger"))
from ledger import Ledger           # noqa: E402

_EXCLUDE_DIR = {"__pycache__", "_backups", ".git"}
_EXCLUDE_SUFFIX = {".pyc", ".db", ".lock"}


def git_commit(target: Path) -> str:
    """Best-effort in-place versioning. Never fails the backup."""
    def run(*a):
        return subprocess.run(["git", "-C", str(target), *a],
                              capture_output=True, text=True)
    try:
        if not (target / ".git").exists():
            run("init", "-q")
        run("add", "-A")
        r = run("commit", "-q", "-m", f"backup {time.strftime('%Y-%m-%d %H:%M:%S')}")
        if r.returncode == 0:
            return "committed"
        return "nothing-to-commit" if "nothing to commit" in (r.stdout + r.stderr).lower() \
            else "git-skipped"
    except Exception:
        return "git-unavailable"


def snapshot(target: Path, out_dir: Path) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    archive = out_dir / f"{target.name}-{time.strftime('%Y%m%d-%H%M%S')}.tar.gz"

    def keep(ti: tarfile.TarInfo):
        parts = Path(ti.name).parts
        if any(p in _EXCLUDE_DIR for p in parts):
            return None
        if Path(ti.name).suffix in _EXCLUDE_SUFFIX:
            return None
        return ti

    with tarfile.open(archive, "w:gz") as tar:
        tar.add(target, arcname=target.name, filter=keep)
    return archive


def prune(out_dir: Path, keep: int = 7) -> int:
    arcs = sorted(out_dir.glob(f"{ROOT.name}-*.tar.gz"))
    removed = 0
    for a in arcs[:-keep]:
        try:
            a.unlink()
            removed += 1
        except OSError:
            pass
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

    kb = archive.stat().st_size / 1024
    print(f"backup OK  git={git_state}  archive={archive.name} ({kb:.0f} KB)  pruned={pruned}")
    print("off-site copy #3 (configure once, then it is one command):")
    print(f'  restic -r <repo> backup "{out_dir}"        # or')
    print(f'  rclone copy "{out_dir}" <encrypted-remote>')
    return 0


if __name__ == "__main__":
    sys.exit(main())
