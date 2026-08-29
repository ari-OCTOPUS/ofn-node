"""Allowed-path filesystem watcher. Untrusted filenames are data, not commands."""

from __future__ import annotations

import os
import stat
from collections.abc import AsyncIterator
from pathlib import Path

from octopus_sensorium.sensors.base import BaseSensor, DiscoveryResult, RawObservation, SelfTestResult

DEFAULT_PATHS = (
    "/etc/octopus/config",
    "/var/lib/octopus",
)


def _stat_path(path: Path) -> dict | None:
    try:
        st = path.stat()
    except OSError:
        return None
    return {
        "path": str(path),
        "mtime_ns": st.st_mtime_ns,
        "size": st.st_size,
        "mode": stat.filemode(st.st_mode),
        "uid": st.st_uid,
        "gid": st.st_gid,
        "is_dir": path.is_dir(),
    }


class FilesystemSensor(BaseSensor):
    sensor_type = "filesystem"
    capabilities = {"config_mtime", "state_mtime"}

    def __init__(self, manifest: dict) -> None:
        super().__init__(manifest)
        allowed = tuple(manifest.get("source", {}).get("allowed_paths") or DEFAULT_PATHS)
        self.allowed_paths = [Path(p) for p in allowed]
        self._last: dict[str, dict] = {}

    async def discover(self) -> DiscoveryResult:
        existing = [str(p) for p in self.allowed_paths if p.exists()]
        return DiscoveryResult(present=bool(existing), details={"paths": existing})

    async def self_test(self) -> SelfTestResult:
        readable = []
        for path in self.allowed_paths:
            info = _stat_path(path)
            if info:
                readable.append(info)
        ok = bool(readable)
        return SelfTestResult(passed=ok, message=f"{len(readable)} paths", measurements={"paths": readable})

    async def observe(self) -> AsyncIterator[RawObservation]:
        changes = []
        snapshot = []
        for path in self.allowed_paths:
            info = _stat_path(path)
            if not info:
                continue
            snapshot.append(info)
            prev = self._last.get(str(path))
            if prev and prev.get("mtime_ns") != info["mtime_ns"]:
                changes.append({"path": str(path), "previous_mtime_ns": prev["mtime_ns"], "mtime_ns": info["mtime_ns"]})
            self._last[str(path)] = info
        payload = {
            "sequence": self.next_sequence(),
            "snapshot": snapshot,
            "changes": changes,
            "pid": os.getpid(),
        }
        yield RawObservation(payload=payload, source_id="posix-stat", bytes_len=len(str(payload)))
