"""Idempotency keys and duplicate-run suppression."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Optional

from .atomic_io import atomic_write_json, read_json, sha256_bytes


def inputs_hash(parts: dict[str, Any]) -> str:
    payload = json.dumps(parts, sort_keys=True, ensure_ascii=False, default=str).encode("utf-8")
    return sha256_bytes(payload)


def make_idempotency_key(task_id: str, previous_sha: str, inputs: dict[str, Any]) -> str:
    ih = inputs_hash(inputs)
    raw = f"{task_id}|{previous_sha}|{ih}".encode("utf-8")
    return sha256_bytes(raw)


class IdempotencyStore:
    def __init__(self, path: str | Path):
        self.path = Path(path)

    def load(self) -> dict:
        if not self.path.exists():
            return {}
        try:
            data = read_json(self.path)
            return data if isinstance(data, dict) else {}
        except Exception:
            return {}

    def lookup(self, key: str) -> Optional[dict]:
        return self.load().get(key)

    def remember(self, key: str, artifact_meta: dict) -> None:
        data = self.load()
        if key in data:
            # second run: do not duplicate side effects; keep first record
            return
        data[key] = artifact_meta
        atomic_write_json(self.path, data, refuse_overwrite_if_different=False)
