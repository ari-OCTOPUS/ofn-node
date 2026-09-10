"""Atomic write (temp -> fsync -> replace), hashing, sealed-artifact guard."""

from __future__ import annotations

import hashlib
import json
import os
import tempfile
from pathlib import Path
from typing import Any, Optional, Union


class SealedArtifactError(OSError):
    pass


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: str | Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def atomic_write_bytes(path: str | Path, data: bytes, *, refuse_overwrite_if_different: bool = True) -> str:
    """Write bytes atomically. Refuse overwrite when existing content differs (sealed)."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and refuse_overwrite_if_different:
        existing = path.read_bytes()
        if existing == data:
            return sha256_bytes(data)
        raise SealedArtifactError(
            f"refuse_overwrite_sealed_artifact:{path}"
        )
    fd, tmp_name = tempfile.mkstemp(prefix=path.name + ".", suffix=".tmp", dir=str(path.parent))
    try:
        with os.fdopen(fd, "wb") as tmp:
            tmp.write(data)
            tmp.flush()
            os.fsync(tmp.fileno())
        os.replace(tmp_name, path)
    except Exception:
        try:
            if os.path.exists(tmp_name):
                os.unlink(tmp_name)
        except OSError:
            pass
        raise
    # Best-effort directory fsync (may fail on some Windows volumes)
    try:
        dir_fd = os.open(str(path.parent), os.O_RDONLY)
        try:
            os.fsync(dir_fd)
        finally:
            os.close(dir_fd)
    except OSError:
        pass
    return sha256_bytes(data)


def atomic_write_json(
    path: str | Path,
    obj: Any,
    *,
    refuse_overwrite_if_different: bool = True,
    sort_keys: bool = False,
) -> str:
    data = (json.dumps(obj, ensure_ascii=False, indent=2, sort_keys=sort_keys) + "\n").encode("utf-8")
    return atomic_write_bytes(path, data, refuse_overwrite_if_different=refuse_overwrite_if_different)


def read_json(path: str | Path) -> Any:
    raw = Path(path).read_bytes()
    # tolerate BOM
    if raw.startswith(b"\xef\xbb\xbf"):
        text = raw.decode("utf-8-sig")
    else:
        text = raw.decode("utf-8")
    return json.loads(text)


def recover_interrupted_write(path: str | Path, data: bytes) -> str:
    """Re-run atomic write after a simulated interruption; same path ends consistent."""
    return atomic_write_bytes(path, data, refuse_overwrite_if_different=False)
