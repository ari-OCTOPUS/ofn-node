from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from octopus_sensorium.evidence.store import DEFAULT_DIR, JSONL_NAME, _load_index

DEFAULT_DIR = DEFAULT_DIR


def latest(sensor_id: str, directory: Path = DEFAULT_DIR) -> dict[str, Any] | None:
    path = directory / f"last_{sensor_id.replace('.', '_')}.json"
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def by_event_id(event_id: str, directory: Path = DEFAULT_DIR) -> dict[str, Any] | None:
    meta = (_load_index(directory, "event_id") or {}).get(event_id)
    if not meta:
        return None
    return _read_offset(directory, int(meta.get("offset") or 0))


def by_sensor(sensor_id: str, directory: Path = DEFAULT_DIR) -> list[str]:
    return list((_load_index(directory, "sensor_id") or {}).get(sensor_id) or [])


def replay_query(directory: Path = DEFAULT_DIR) -> list[dict[str, Any]]:
    path = directory / JSONL_NAME
    if not path.exists():
        return []
    out: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            rec = json.loads(line)
            out.append(rec.get("observation") or rec)
    return out


def _read_offset(directory: Path, offset: int) -> dict[str, Any] | None:
    path = directory / JSONL_NAME
    if not path.exists():
        return None
    with path.open(encoding="utf-8") as handle:
        handle.seek(offset)
        line = handle.readline()
    try:
        rec = json.loads(line)
    except ValueError:
        return None
    return rec.get("observation") or rec
