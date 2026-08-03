"""System runtime adapters: real clock, uuid ids, file-based kill switch."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from pathlib import Path


class SystemClock:
    def now_iso(self) -> str:
        return datetime.now(timezone.utc).isoformat()


class FixedClock:
    """Test double: a clock pinned to an injected instant, advanced explicitly."""

    def __init__(self, start: str = "2026-01-01T00:00:00+00:00") -> None:
        self._now = start

    def now_iso(self) -> str:
        return self._now

    def set(self, ts: str) -> None:
        self._now = ts


class UuidGen:
    def new_id(self, prefix: str) -> str:
        return f"{prefix}-{uuid.uuid4().hex[:12]}"


class SequentialIdGen:
    """Test double: deterministic ids."""

    def __init__(self) -> None:
        self._n = 0

    def new_id(self, prefix: str) -> str:
        self._n += 1
        return f"{prefix}-{self._n:04d}"


class FileKillSwitch:
    """Kill = a file existing. Any human (or cron) can halt the organism with `touch`,
    and the in-band control (record_kill) engages the same file so the API actually stops."""

    def __init__(self, path: str | Path) -> None:
        self._path = Path(path)

    def engaged(self) -> bool:
        return self._path.exists()

    def engage(self) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._path.write_text("engaged\n", encoding="utf-8")

    def release(self) -> None:
        self._path.unlink(missing_ok=True)


class ManualKillSwitch:
    def __init__(self, engaged: bool = False) -> None:
        self._engaged = engaged

    def engaged(self) -> bool:
        return self._engaged

    def engage(self) -> None:
        self._engaged = True

    def release(self) -> None:
        self._engaged = False
