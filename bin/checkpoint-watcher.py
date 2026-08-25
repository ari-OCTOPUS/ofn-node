#!/usr/bin/env python3
"""Keep-alive checkpoint watcher. One bad receipt must not stop the process."""
from __future__ import annotations

import json
import time
from datetime import datetime, timezone
from pathlib import Path

from ofn.organism.runtime.checkpoint import safe_load_checkpoint

LAB = Path("/opt/octopus/lab")
RECEIPTS = LAB / "artifacts/completion-phase3/receipts"
QUARANTINE = RECEIPTS / "quarantine"
HEARTBEAT = RECEIPTS / "watcher.heartbeat.json"
WATCH_PATH = RECEIPTS / "05_deployment_checkpoint.json"


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def write_heartbeat(payload: dict) -> None:
    HEARTBEAT.parent.mkdir(parents=True, exist_ok=True)
    tmp = HEARTBEAT.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    tmp.replace(HEARTBEAT)


def main() -> int:
    invalid = 0
    valid = 0
    while True:
        parsed, error = safe_load_checkpoint(WATCH_PATH, QUARANTINE)
        if parsed is not None:
            valid += 1
            status = "ok"
            last_error = None
        else:
            invalid += 1
            status = "quarantined_last"
            last_error = None if error is None else error.as_dict()
        write_heartbeat(
            {
                "running": True,
                "updated_utc": utc_now(),
                "status": status,
                "valid_loads": valid,
                "invalid_loads": invalid,
                "last_error_kind": None if last_error is None else last_error["kind"],
                "watch_path": str(WATCH_PATH),
            }
        )
        time.sleep(15)


if __name__ == "__main__":
    raise SystemExit(main())
