"""Nightly backup CLI. Verifies every copy, then prunes old ones."""

from __future__ import annotations

import os
import time

from . import config
from .adapters.backup import backup, prune, verify_backup

KEEP = 14


def main() -> int:
    cfg = config.load()
    stamp = time.strftime("%Y%m%d-%H%M%S", time.gmtime())
    dest = os.path.join(cfg.backup_root, stamp)
    result = backup(cfg.db_paths, dest, stamp=stamp)
    print(f"backup -> {dest}")
    for entry in result.entries:
        state = "verified" if entry.verified else "UNVERIFIED"
        print(f"  {entry.name}: {entry.bytes} bytes [{state}]")
    if not result.ok:
        print(f"FAILED: {result.detail}")
        return 1
    ok, why = verify_backup(dest)
    print(f"re-verify: {why}")
    if not ok:
        return 1
    removed = prune(cfg.backup_root, keep=KEEP)
    if removed:
        print(f"pruned {len(removed)} old backup(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
