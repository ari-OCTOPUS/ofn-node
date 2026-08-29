"""Persist plugin sequence numbers across process restart. Not a world-state source."""

from __future__ import annotations

import json
import os
from pathlib import Path

DEFAULT_PATH = Path("/var/lib/octopus/state/sequences.json")


def _read(path: Path) -> dict[str, int]:
    if not path.exists() or path.stat().st_size == 0:
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    if not isinstance(data, dict):
        return {}
    out: dict[str, int] = {}
    for key, value in data.items():
        try:
            out[str(key)] = int(value)
        except (TypeError, ValueError):
            continue
    return out


def restore_sequence(sensor_id: str, path: Path | None = None) -> int:
    return int(_read(path or DEFAULT_PATH).get(sensor_id, 0))


def save_sequence(sensor_id: str, sequence: int, path: Path | None = None) -> None:
    path = path or DEFAULT_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    data = _read(path)
    data[sensor_id] = int(sequence)
    blob = json.dumps(data, indent=2, sort_keys=True) + "\n"
    tmp = path.with_suffix(".json.tmp")
    fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o640)
    try:
        os.write(fd, blob.encode("utf-8"))
        os.fsync(fd)
    finally:
        os.close(fd)
    os.replace(tmp, path)
