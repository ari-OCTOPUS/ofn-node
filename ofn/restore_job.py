"""Restore from the newest verified backup. Refuses anything unverified."""

from __future__ import annotations

import os
import sys

from . import config
from .adapters.backup import restore, verify_backup


def main() -> int:
    cfg = config.load()
    root = cfg.backup_root
    if not os.path.isdir(root):
        print("no backups found", file=sys.stderr)
        return 1
    for name in sorted(os.listdir(root), reverse=True):
        candidate = os.path.join(root, name)
        if not os.path.isdir(candidate):
            continue
        ok, why = verify_backup(candidate)
        if not ok:
            print(f"skipping {name}: {why}")
            continue
        done, detail = restore(candidate, cfg.db_paths,
                               keep_corrupt_as="before-restore")
        print(f"{name}: {detail}")
        return 0 if done else 1
    print("no verified backup available", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
