"""Append-only evidence files. Existing records are never rewritten."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

DEFAULT_DIR = Path("/var/lib/octopus/state/evidence")


def persist_observation(sensor_id: str, obs: dict[str, Any], directory: Path = DEFAULT_DIR) -> Path:
    directory.mkdir(parents=True, exist_ok=True)
    from octopus_sensorium.evidence.canonical_json import canonical_json
    from octopus_sensorium.evidence.content_hash import content_hash

    blob = json.dumps(obs, indent=2, ensure_ascii=False)
    last = directory / "last_l1_observation.json"
    last.write_text(blob, encoding="utf-8")
    safe_id = sensor_id.replace(".", "_")
    path = directory / f"last_{safe_id}.json"
    path.write_text(blob, encoding="utf-8")
    (directory / f"last_{safe_id}.hash").write_text(content_hash(canonical_json(obs)) + "\n", encoding="utf-8")
    if obs.get("observation_type") == "event":
        (directory / f"last_{safe_id}_event.json").write_text(blob, encoding="utf-8")
    return path


def persist_derived(sensor_id: str, event: dict[str, Any], directory: Path = DEFAULT_DIR) -> Path:
    directory.mkdir(parents=True, exist_ok=True)
    safe = sensor_id.replace(".", "_")
    path = directory / f"last_{safe}.json"
    path.write_text(json.dumps(event, indent=2, ensure_ascii=False), encoding="utf-8")
    return path
