"""Empty local-CRDT store init (F3 spine). Additive — no writer cutover."""

from __future__ import annotations

import os
from pathlib import Path

from .runtime_truth_v1 import ContractViolation

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_STORE = REPO_ROOT / "data" / "spine" / "events.jsonl"


def open_or_create_empty(path: Path | None = None) -> Path:
    """Open append-only jsonl; create empty file if absent. Never migrate."""
    target = Path(path) if path is not None else DEFAULT_STORE
    if target.is_symlink():
        raise ContractViolation(f"store path must not be a symlink: {target}")
    if target.exists():
        if not target.is_file():
            raise ContractViolation(f"store path is not a file: {target}")
        return target
    parent = target.parent
    created_parent = not parent.exists()
    parent.mkdir(parents=True, exist_ok=True)
    if created_parent:
        os.chmod(parent, 0o700)
    flags = os.O_CREAT | os.O_EXCL | os.O_WRONLY
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    try:
        fd = os.open(target, flags, 0o600)
    except FileExistsError:
        return target
    os.close(fd)
    return target
