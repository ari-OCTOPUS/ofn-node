"""Append-only quarantine for malformed events. Never mutates original evidence."""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

DEFAULT_PATH = Path("/var/lib/octopus/state/quarantine/malformed.jsonl")


def persist_quarantine(
    *,
    sensor_id: str,
    stage: str,
    reason: str,
    payload: dict[str, Any] | None = None,
    path: Path = DEFAULT_PATH,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    record = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "sensor_id": sensor_id,
        "stage": stage,
        "reason": reason,
        "payload_keys": sorted((payload or {}).keys()),
    }
    line = json.dumps(record, separators=(",", ":"), ensure_ascii=False) + "\n"
    fd = os.open(path, os.O_WRONLY | os.O_APPEND | os.O_CREAT, 0o640)
    try:
        os.write(fd, line.encode("utf-8"))
        os.fsync(fd)
    finally:
        os.close(fd)
