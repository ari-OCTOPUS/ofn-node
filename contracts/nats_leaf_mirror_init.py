"""Empty NATS leaf/mirror init (F3 spine). Additive — no writer cutover.

Owner vote: NATS_LEAF_MIRROR (supersedes LOCAL_CRDT).
Creates an empty durable init file only. Does NOT connect to NATS,
does NOT start leaf/mirror daemons, does NOT cut over publishers.
stdlib-only.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Mapping

from .runtime_truth_v1 import ContractViolation

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INIT = REPO_ROOT / "data" / "spine" / "nats_leaf_mirror.init.json"

INIT_SCHEMA = "nats_leaf_mirror.init.v1"

EMPTY_INIT: dict[str, Any] = {
    "schema": INIT_SCHEMA,
    "mode": "leaf_mirror",
    "enabled": False,
    "hub_url": "",
    "leaf_name": "",
    "mirror_prefix": "",
    "note": "empty init — no network, no writer cutover",
}


def open_or_create_empty(path: Path | None = None) -> Path:
    """Open leaf/mirror init JSON; create empty disabled stub if absent. Never migrate."""
    target = Path(path) if path is not None else DEFAULT_INIT
    if target.is_symlink():
        raise ContractViolation(f"init path must not be a symlink: {target}")
    if target.exists():
        if not target.is_file():
            raise ContractViolation(f"init path is not a file: {target}")
        return target
    parent = target.parent
    created_parent = not parent.exists()
    parent.mkdir(parents=True, exist_ok=True)
    if created_parent:
        os.chmod(parent, 0o700)
    payload = json.dumps(EMPTY_INIT, indent=2, sort_keys=True) + "\n"
    flags = os.O_CREAT | os.O_EXCL | os.O_WRONLY
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    try:
        fd = os.open(target, flags, 0o600)
    except FileExistsError:
        return target
    try:
        os.write(fd, payload.encode("utf-8"))
    finally:
        os.close(fd)
    return target


def read_init(path: Path | None = None) -> Mapping[str, Any]:
    target = open_or_create_empty(path)
    data = json.loads(target.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ContractViolation("nats leaf/mirror init must be a JSON object")
    if data.get("schema") != INIT_SCHEMA:
        raise ContractViolation(f"unexpected init schema: {data.get('schema')!r}")
    if data.get("enabled") is True:
        raise ContractViolation("enabled=true forbidden in empty-init slice (no cutover)")
    return data
