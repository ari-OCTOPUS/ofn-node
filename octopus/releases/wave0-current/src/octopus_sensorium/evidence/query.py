from __future__ import annotations

import json
from pathlib import Path
from typing import Any

DEFAULT_DIR = Path("/var/lib/octopus/state/evidence")


def latest(sensor_id: str, directory: Path = DEFAULT_DIR) -> dict[str, Any] | None:
    path = directory / f"last_{sensor_id.replace('.', '_')}.json"
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
