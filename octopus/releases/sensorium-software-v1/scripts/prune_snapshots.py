#!/usr/bin/env python3
"""Prune state/snapshots/snapshot-*.json older than the retention window.

Keeps latest.json untouched. Operational telemetry only — evidence ledgers are
not in scope (see LEDGER_RETENTION.yaml).
"""

from __future__ import annotations

import argparse
import time
from pathlib import Path

DIR = Path("/var/lib/octopus/state/snapshots")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--hours", type=float, default=24.0)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    cutoff = time.time() - args.hours * 3600
    removed = 0
    kept = 0
    freed = 0
    if DIR.is_dir():
        for path in sorted(DIR.glob("snapshot-*.json")):
            st = path.stat()
            if st.st_mtime < cutoff:
                freed += st.st_size
                if not args.dry_run:
                    path.unlink()
                removed += 1
            else:
                kept += 1
    print(
        f"prune hours={args.hours} removed={removed} kept={kept} "
        f"freed_bytes={freed} dry_run={args.dry_run}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
